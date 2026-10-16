import re
import datetime
from django.utils import timezone

def generate_zrp_naming_convention(department_code, doc_type, subject, ref_number, date_obj=None, version="V1"):
    """
    Generates a standardized ZRP document file name following:
    Department – Document Type – Subject – Reference Number – Date – Version
    Example: HR-LEAVE-ANNUAL_LEAVE-JOHN_DOE-2026-001-V1
    """
    if not date_obj:
        date_obj = timezone.now()

    date_str = date_obj.strftime("%Y-%m-%d") if isinstance(date_obj, (datetime.date, datetime.datetime)) else str(date_obj)

    # Sanitize parts to uppercase with underscores
    clean_dept = re.sub(r'[^A-Z0-9_]', '', department_code.upper().replace(' ', '_'))
    clean_type = re.sub(r'[^A-Z0-9_]', '', doc_type.upper().replace(' ', '_'))
    clean_subj = re.sub(r'[^A-Z0-9_]', '', subject.upper().replace(' ', '_'))
    clean_ref = re.sub(r'[^A-Z0-9_]', '', ref_number.upper().replace(' ', '_'))
    clean_ver = version.upper() if version.upper().startswith('V') else f"V{version}"

    return f"{clean_dept}-{clean_type}-{clean_subj}-{clean_ref}-{date_str}-{clean_ver}"

# Backward-compat alias
generate_zmc_naming_convention = generate_zrp_naming_convention


def validate_zrp_naming_convention(filename):
    """
    Validates if a filename matches the standard ZRP structure.
    Returns (is_valid, parsed_dict)
    """
    pattern = r'^(?P<dept>[A-Z0-9_]+)-(?P<type>[A-Z0-9_]+)-(?P<subject>[A-Z0-9_]+)-(?P<ref>[A-Z0-9_]+)-(?P<date>\d{4}-\d{2}-\d{2})-(?P<version>V\d+)$'
    match = re.match(pattern, filename.strip())

    if match:
        return True, match.groupdict()
    return False, {}
