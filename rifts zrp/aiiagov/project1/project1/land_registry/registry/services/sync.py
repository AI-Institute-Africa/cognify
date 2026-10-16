import logging
from django.utils import timezone
from django.db import transaction
from registry.models import OfflineSyncQueue, File, ScannedDocument, ScannerDevice

logger = logging.getLogger(__name__)

class SyncService:
    @staticmethod
    def process_queue():
        """
        Main engine that processes pending offline capture records.
        """
        pending_records = OfflineSyncQueue.objects.filter(status='Pending').order_by('created_at')
        results = {'synced': 0, 'conflicts': 0, 'failed': 0}

        for record in pending_records:
            try:
                with transaction.atomic():
                    # 1. Conflict Detection
                    conflict = SyncService.check_conflict(record)
                    if conflict:
                        record.status = 'Conflict'
                        record.conflict_notes = conflict
                        record.save()
                        results['conflicts'] += 1
                        continue

                    # 2. Ingestion
                    SyncService.ingest_record(record)
                    
                    record.status = 'Synced'
                    record.processed_at = timezone.now()
                    record.save()
                    results['synced'] += 1
                    
            except Exception as e:
                logger.error(f"Sync failed for record {record.local_id}: {str(e)}")
                record.status = 'Failed'
                record.conflict_notes = str(e)
                record.save()
                results['failed'] += 1

        return results

    @staticmethod
    def check_conflict(record):
        """
        Checks if the incoming record conflicts with current system state.
        """
        # Scenario A: The File reference number no longer exists
        file_exists = File.objects.filter(ref_num=record.ref_num).exists()
        if not file_exists:
            return f"Reference Number {record.ref_num} not found in registry."

        # Scenario B: Simultaneous upload (rare but check for exact match in filename/size)
        # For now, we allow multiple scans per file as history.
        
        return None

    @staticmethod
    def ingest_record(record):
        """
        Converts a sync record into a formal ScannedDocument.
        """
        file_obj = File.objects.get(ref_num=record.ref_num)
        
        # Determine Scanner identity (default to a system 'Mobile' scanner)
        mobile_scanner, _ = ScannerDevice.objects.get_or_create(
            name="Mobile Device Capture",
            defaults={'is_active': True}
        )

        # Create the formal scan record
        ScannedDocument.objects.create(
            scanner=mobile_scanner,
            raw_file=record.attachment,
            extracted_text=record.data.get('notes', ""),
            status='Awaiting Link' if not file_obj else 'Pending',
            linked_file=file_obj,
            metadata={
                'local_id': str(record.local_id),
                'sync_data': record.data,
                'captured_by': record.user.username
            }
        )
        
        # Trigger Digital Twin Update if needed
        from registry.services.twin import DigitalTwinService
        DigitalTwinService.instantiate_twin(file_obj, user=record.user)
