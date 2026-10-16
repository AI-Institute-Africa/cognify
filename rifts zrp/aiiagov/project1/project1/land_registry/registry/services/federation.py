import hmac
import hashlib
import secrets
import json
from django.utils import timezone
from registry.models import Organization, FederationLink, CustodyLog


class FederationService:

    @staticmethod
    def get_or_create_local_org():
        """
        Ensures a local organization record exists representing this instance.
        """
        org, created = Organization.objects.get_or_create(
            code='LOCAL_ORG',
            defaults={
                'name': 'Local Institution',
                'is_local': True
            }
        )
        return org

    @staticmethod
    def create_link(source_org, target_org_code, target_org_name):
        """
        Initiates a federation link request with a generated shared secret.
        """
        target_org, created = Organization.objects.get_or_create(
            code=target_org_code,
            defaults={'name': target_org_name}
        )

        link, link_created = FederationLink.objects.get_or_create(
            source_org=source_org,
            target_org=target_org,
            defaults={
                'link_status': 'Pending',
                'shared_secret': secrets.token_urlsafe(48)  # 384-bit secret
            }
        )
        return link

    @staticmethod
    def generate_access_token(link, payload: dict) -> str:
        """
        Generates an HMAC-SHA256 token for a federated transfer request.
        The token signs the JSON payload with the link's shared secret.

        Returns a hex-encoded MAC.
        """
        if not link.shared_secret:
            raise ValueError("FederationLink has no shared secret.")

        message = json.dumps(payload, sort_keys=True).encode('utf-8')
        mac = hmac.new(
            link.shared_secret.encode('utf-8'),
            message,
            hashlib.sha256
        )
        return mac.hexdigest()

    @staticmethod
    def verify_access_token(link, payload: dict, token: str) -> bool:
        """
        Verifies an incoming HMAC-SHA256 token against the link's shared secret.
        Uses a constant-time comparison to prevent timing attacks.
        """
        if not link.shared_secret:
            return False
        expected = FederationService.generate_access_token(link, payload)
        return hmac.compare_digest(expected, token)

    @staticmethod
    def validate_transfer(source_org_code, target_org_code):
        """
        Verifies if an active federation link exists between two organizations.
        """
        try:
            FederationLink.objects.get(
                source_org__code=source_org_code,
                target_org__code=target_org_code,
                link_status='Active'
            )
            return True
        except FederationLink.DoesNotExist:
            return False

    @staticmethod
    def authorize_federated_access(token: str, link, payload: dict) -> bool:
        """
        Full cryptographic authorization for an incoming federated access request.
        Validates the HMAC token against the shared secret and checks link status.
        """
        if link.link_status != 'Active':
            return False
        return FederationService.verify_access_token(link, payload, token)

    @staticmethod
    def get_transfer_summary(source_org_code, target_org_code) -> dict:
        """
        Returns a summary of the federation link state for UI rendering.
        """
        try:
            link = FederationLink.objects.get(
                source_org__code=source_org_code,
                target_org__code=target_org_code,
            )
            return {
                'status': link.link_status,
                'target': link.target_org.name,
                'is_active': link.link_status == 'Active',
                'link_id': link.pk,
            }
        except FederationLink.DoesNotExist:
            return {'status': 'Not Linked', 'is_active': False}
