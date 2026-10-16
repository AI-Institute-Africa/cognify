from django.utils import timezone
from registry.models import CustodyLog, File, FileLocation, Department, Organization, FederationLink

class CustodyService:
    @staticmethod
    def log_movement(file_doc, handler, action, reason=None, to_dept=None, from_dept=None, to_org=None, from_org=None, location=None, acknowledged=False):
        """
        Records a movement in the immutable CustodyLog.
        Reason for transfer is mandatory for all movements except creation.
        """
        if action != 'CREATED' and not reason:
            raise ValueError("Reason for transfer requirement: All file movements must have a recorded reason.")
            
        log = CustodyLog.objects.create(
            file_doc=file_doc,
            handler=handler,
            action=action,
            reason=reason,
            from_department=from_dept,
            to_department=to_dept,
            from_organization=from_org,
            to_organization=to_org,
            location=location,
            timestamp=timezone.now(),
            acknowledged=acknowledged
        )
        
        # Update file's real-time status
        file_doc.last_moved_at = timezone.now()
        file_doc.last_handler = handler
        if location:
            file_doc.current_location = location
        if to_dept:
            file_doc.current_department = to_dept
        file_doc.save()
            
        return log
        
    @staticmethod
    def record_creation(file_obj, user, location=None):
        """
        Records the initial entry of a file into the registry system.
        """
        return CustodyService.log_movement(
            file_doc=file_obj,
            handler=user,
            action='CREATED',
            reason="Initial record creation and physical placement.",
            location=location,
            acknowledged=True # Created by the user themselves
        )

    @staticmethod
    def acknowledge_receipt(log_id, user):
        """
        Digital acknowledgment on receipt.
        """
        try:
            log = CustodyLog.objects.get(id=log_id)
            log.acknowledged = True
            log.received_by = user
            log.received_at = timezone.now()
            log.save()
            return True
        except CustodyLog.DoesNotExist:
            return False

    @staticmethod
    def handover(file_obj, current_user, target_user, reason, location=None):
        """
        Internal department handover between officers.
        """
        return CustodyService.log_movement(
            file_doc=file_obj,
            handler=target_user,
            action='HANDOVER',
            reason=f"Handover from {current_user.username}: {reason}",
            from_dept=None, # Same dept
            to_dept=None,
            location=location,
            acknowledged=False # Requires acknowledgment
        )

    @staticmethod
    def transfer(file_obj, current_user, target_dept, reason, location=None):
        """
        Inter-departmental transfer.
        Resolves from_dept from (in order of preference):
        1. The file's current_department field (most reliable)
        2. The user's borrower_profile.department (if set)
        3. None (for admin/staff with no profile)
        """
        from_dept = None

        # Priority 1: use the file's tracked current department
        if file_obj.current_department:
            from_dept = file_obj.current_department

        # Priority 2: fall back to the user's borrower profile department
        elif hasattr(current_user, 'borrower_profile') and current_user.borrower_profile.department:
            from_dept = current_user.borrower_profile.department

        return CustodyService.log_movement(
            file_doc=file_obj,
            handler=current_user,
            action='TRANSFER',
            reason=reason,
            from_dept=from_dept,
            to_dept=target_dept,
            location=location,
            acknowledged=False  # Requires acknowledgment by receiver
        )

    @staticmethod
    def federated_transfer(file_obj, current_user, target_org, target_dept_name, reason):
        """
        Handles transfer to an external federated organization.
        """
        from_org = None
        if file_obj.current_department and file_obj.current_department.organization:
            from_org = file_obj.current_department.organization
        
        # Check for active federation link
        from registry.services.federation import FederationService
        if not FederationService.validate_transfer(from_org.code if from_org else 'LOCAL_ORG', target_org.code):
             raise ValueError(f"No active federation link exists between this institution and {target_org.name}.")

        log = CustodyService.log_movement(
            file_doc=file_obj,
            handler=current_user,
            action='FEDERATED_TRANSFER',
            reason=f"Federated Transfer to {target_org.name} ({target_dept_name}): {reason}",
            from_org=from_org,
            to_org=target_org,
            acknowledged=False
        )

        # Mark file as 'in_transit' or 'external'
        file_obj.f_status = 'external'
        file_obj.save()

        return log

    @staticmethod
    def mark_lost(file_obj, user, reason):
        """
        Marks a physical file as lost while maintaining its digital twin.
        """
        file_obj.is_lost = True
        file_obj.save()
        return CustodyService.log_movement(
            file_doc=file_obj,
            handler=user,
            action='LOST',
            reason=f"ALERT: File reported lost. {reason}",
            acknowledged=True
        )

    @staticmethod
    def mark_found(file_obj, user, location, reason):
        """
        Restores a file to active status upon recovery.
        """
        file_obj.is_lost = False
        file_obj.current_location = location
        file_obj.save()
        return CustodyService.log_movement(
            file_doc=file_obj,
            handler=user,
            action='FOUND',
            reason=f"Recovery: File located at {location}. {reason}",
            location=location,
            acknowledged=True
        )

    @staticmethod
    def request_approval(file_obj, user, action_type, comments=None):
        """
        Initializes a formal approval request for sensitive actions.
        """
        from registry.models import FileApproval
        return FileApproval.objects.create(
            file_doc=file_obj,
            requester=user,
            action_type=action_type,
            comments=comments,
            status='Pending'
        )
