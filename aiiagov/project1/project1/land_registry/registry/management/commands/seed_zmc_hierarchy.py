from django.core.management.base import BaseCommand
from registry.models import Category, SubCategory, Department, CloudFolder, Organization

class Command(BaseCommand):
    help = "Seeds the 9 official ZRP Document & Electronic Records Management Root Hierarchy Folders and Subcategories."

    def handle(self, *args, **options):
        self.stdout.write("Seeding ZRP Official Document Hierarchy...")

        # Get or create default ZRP Organization
        org, _ = Organization.objects.get_or_create(
            code='ZRP',
            defaults={'name': 'Zimbabwe Republic Police', 'is_local': True}
        )

        # Get or create default Registry Department
        registry_dept, _ = Department.objects.get_or_create(
            name='Registry & Records',
            defaults={'organization': org, 'description': 'Centralized Records and Document Registry'}
        )

        # Proposed 9 ZRP Root Categories & Subcategories
        ZRP_structure = [
            {
                "name": "01. Corporate/Commission",
                "description": "Commission meetings, policies, strategic plans, annual reports and correspondence.",
                "subcategories": ["Commission Meetings", "Policies & Regulations", "Strategic Plans", "Annual Reports", "Corporate Correspondence"]
            },
            {
                "name": "02. Human Resources",
                "description": "Employee records, leave, attendance, performance management, training and development, recruitment, interviews and staff welfare.",
                "subcategories": ["Employee Personal Records", "Leave & Absence", "Attendance Logs", "Performance Appraisals", "Training & Development", "Recruitment & Interviews", "Staff Welfare"]
            },
            {
                "name": "03. Finance",
                "description": "Budgets, allowances, acquittals.",
                "subcategories": ["Budgets & Allocations", "Staff Allowances", "Financial Acquittals", "Audit Reports"]
            },
            {
                "name": "04. Procurement",
                "description": "Procurement requisitions and approvals, and annual procurement plan.",
                "subcategories": ["Procurement Requisitions", "Bid Evaluations & Analyses", "Annual Procurement Plan", "Supplier Contracts"]
            },
            {
                "name": "05. Departments/Directorates",
                "description": "Department-specific files and correspondence.",
                "subcategories": ["Media Monitoring & Compliance", "Research & Development", "Legal & Licensing", "Public Relations & Communication"]
            },
            {
                "name": "06. Meetings and Minutes",
                "description": "Commission, management, departmental and committee meetings and action registers.",
                "subcategories": ["Commission Board Meetings", "Executive Management Meetings", "Departmental Meetings", "Committee Minutes & Action Registers"]
            },
            {
                "name": "07. Training, Travel & Subsistence",
                "description": "Training requests, travel requests, TSA applications, approvals, reports and acquittals.",
                "subcategories": ["Training Applications", "Local & Foreign Travel Requests", "TSA Applications & Approvals", "Travel Acquittals & Trip Reports"]
            },
            {
                "name": "08. Reports and Analytics",
                "description": "Departmental reports, attendance, training/travel and management reports.",
                "subcategories": ["Departmental Monthly Reports", "Attendance Summaries", "Travel & Training Reports", "Management Analytics"]
            },
            {
                "name": "09. Admin",
                "description": "Stores request, vehicle request, fuel request and internal purchase requisition.",
                "subcategories": ["Stores Requisitions", "Vehicle Requests & Logbooks", "Fuel Requisitions", "Internal Purchase Requisitions"]
            },
        ]

        created_cat_count = 0
        created_sub_count = 0

        for cat_data in ZRP_structure:
            cat, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={
                    "description": cat_data["description"],
                    "status": "1"
                }
            )
            if created:
                created_cat_count += 1

            # Seed CloudFolder equivalent
            cloud_folder, _ = CloudFolder.objects.get_or_create(
                name=cat_data["name"],
                department=registry_dept,
                defaults={"parent": None}
            )

            for sub_name in cat_data["subcategories"]:
                sub, sub_created = SubCategory.objects.get_or_create(
                    category=cat,
                    name=sub_name,
                    defaults={
                        "description": f"{sub_name} under {cat.name}",
                        "status": "1"
                    }
                )
                if sub_created:
                    created_sub_count += 1

                # Subfolder in CloudFolder
                CloudFolder.objects.get_or_create(
                    name=sub_name,
                    parent=cloud_folder,
                    department=registry_dept
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded ZRP Hierarchy! ({created_cat_count} Root Categories, {created_sub_count} Subcategories created)"))
