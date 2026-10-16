import logging
from django.db import transaction
from registry.models import File, CloudFolder, ScannedDocument
from registry.services.cloud import CloudService
from registry.services.risk import RiskEngine
from registry.services.sla import SLAManager

logger = logging.getLogger(__name__)

class DigitalTwinService:
    @staticmethod
    def instantiate_twin(file_obj, user=None):
        """
        Orchestrates the birth of a Digital Twin for a physical file.
        Ensures a cloud folder exists, links orphaned scans, and triggers intelligence baseline.
        """
        try:
            with transaction.atomic():
                # 1. Create/Verify Cloud Governance Folder
                from registry.models import Department
                dept = file_obj.current_department or Department.objects.first()
                if not dept:
                    # If absolutely no department exists, we might need a generic one
                    dept, _ = Department.objects.get_or_create(name="Registry General")

                folder = CloudService.get_or_create_folder(
                    name=file_obj.ref_num,
                    department=dept,
                    project_context=f"Twin for {file_obj.title}",
                    user=user
                )
                
                # 2. Link "Floating" Scanned Documents
                # Search for scans that mention this ref_num in their metadata or text
                orphaned_scans = ScannedDocument.objects.filter(
                    linked_file__isnull=True,
                    # Simplistic check: if ref_num matches a key in metadata or is in extracted_text
                    # In a real system, we'd use a more robust indexing/search
                )
                
                # We'll specifically look for metadata['ref_num'] if it exists
                # or if the extracted text contains the ref_num
                for scan in orphaned_scans:
                    if str(file_obj.ref_num) in (scan.extracted_text or "") or \
                       scan.metadata.get('ref_num') == str(file_obj.ref_num):
                        scan.linked_file = file_obj
                        scan.save()
                        logger.info(f"Auto-linked scan {scan.id} to Digital Twin {file_obj.ref_num}")

                # 3. Initialize Intelligence Baseline
                # Calculate initial risk and sla
                RiskEngine.update_file_risk(file_obj)
                # SLA is calculated on the fly in views, but we ensure its infrastructure works
                # by checking if a log exists. If not, we might create a 'Creation' log if missing
                
                logger.info(f"Digital Twin instantiated for {file_obj.ref_num}")
                return True
        except Exception as e:
            logger.error(f"Failed to instantiate twin for {file_obj.ref_num}: {str(e)}")
            return False

    @staticmethod
    def get_twin_resilience(file_obj):
        """
        Calculates a resilience percentage.
        100% means the digital twin is fully synced.
        If the physical file is lost, the 'survival' of information is shown here.
        """
        scans_count = file_obj.scanned_documents.count()
        versions_count = file_obj.versions.count()
        
        # Base factor: having at least one scan or version means information survives
        if file_obj.is_lost:
            if scans_count > 0 or versions_count > 0:
                return 100 # Information survived physical loss
            return 0 # Information lost with physical file
            
        # Normal operation: balance of digitized records
        score = 50 # Base for being indexed
        if scans_count > 0: score += 25
        if versions_count > 0: score += 25
        
        return min(score, 100)
