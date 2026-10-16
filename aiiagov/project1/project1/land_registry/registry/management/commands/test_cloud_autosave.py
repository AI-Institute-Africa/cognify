"""
Management command: test_cloud_autosave
---------------------------------------
Simulates the exact Finance Officer approval auto-save logic
for the most recent SupplyRequisition and prints detailed errors.

Usage:
    python manage.py test_cloud_autosave
    python manage.py test_cloud_autosave --ref NBSZ-00005
"""
import traceback
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = "Test the cloud auto-save logic for a fully approved purchase requisition."

    def add_arguments(self, parser):
        parser.add_argument('--ref', type=str, help='Specific requisition ref number (e.g. NBSZ-00005)')

    def handle(self, *args, **kwargs):
        from registry.models import SupplyRequisition, Department, CloudFolder, CloudFile
        from registry.services.cloud import CloudService

        ref = kwargs.get('ref')
        if ref:
            req = SupplyRequisition.objects.filter(ref_number=ref).first()
        else:
            req = SupplyRequisition.objects.order_by('-id').first()

        if not req:
            self.stdout.write(self.style.ERROR("No requisitions found."))
            return

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Requisition : {req.ref_number}")
        self.stdout.write(f"Status      : {req.status}")
        self.stdout.write(f"Payment     : {req.payment_status}")
        self.stdout.write(f"Department  : {req.department}")
        self.stdout.write(f"Requester   : {req.requester}")
        self.stdout.write(f"Finance Off : {req.finance_officer}")
        self.stdout.write(f"Items       : {req.items.count()}")
        self.stdout.write(f"Quotations  : {req.quotations.count()}")
        self.stdout.write(f"Uploaded Doc: {req.uploaded_document or 'None'}")
        self.stdout.write(f"Proof of Pay: {req.proof_of_payment or 'None'}")
        self.stdout.write(f"{'='*60}\n")

        # --- Step 1: PDF Generation ---
        self.stdout.write("STEP 1: Testing PDF generation...")
        try:
            from registry.views import generate_supply_requisition_pdf
            pdf_file = generate_supply_requisition_pdf(req)
            self.stdout.write(self.style.SUCCESS(f"  OK  PDF generated: {pdf_file.name} ({pdf_file.size} bytes)"))
        except Exception:
            self.stdout.write(self.style.ERROR("  FAIL  PDF generation failed:"))
            self.stdout.write(traceback.format_exc())
            return

        # --- Step 2: Registry File Creation ---
        self.stdout.write("\nSTEP 2: Testing Registry File creation...")
        try:
            from registry.models import Category, SubCategory, File
            cat, _ = Category.objects.get_or_create(name='Procurement', defaults={'description': 'Procurement Files'})
            subcat, _ = SubCategory.objects.get_or_create(category=cat, name='Purchase Requisitions', defaults={'description': 'Purchase Requisition Files'})
            existing = File.objects.filter(ref_num=req.ref_number).first()
            if existing:
                self.stdout.write(self.style.WARNING(f"  SKIP Registry file already exists: {existing.ref_num}"))
            else:
                pdf_file.seek(0)
                f = File.objects.create(
                    sub_category=subcat,
                    ref_num=req.ref_number,
                    title=f"Purchase Requisition {req.ref_number}",
                    description=f"Approved PR. Purpose: {req.purpose}. Grand Total: {req.grand_total}.",
                    file_attachment=pdf_file,
                    current_department=req.department,
                )
                self.stdout.write(self.style.SUCCESS(f"  OK  Registry file created: {f.ref_num}"))
        except Exception:
            self.stdout.write(self.style.ERROR("  FAIL  Registry file creation failed:"))
            self.stdout.write(traceback.format_exc())

        # --- Step 3: Department Resolution ---
        self.stdout.write("\nSTEP 3: Resolving department...")
        try:
            dept = req.department or Department.objects.first()
            if dept:
                self.stdout.write(self.style.SUCCESS(f"  OK  Department resolved: {dept.name}"))
            else:
                self.stdout.write(self.style.ERROR("  FAIL  No department found in DB! Cannot create cloud folder."))
                return
        except Exception:
            self.stdout.write(self.style.ERROR("  FAIL  Department resolution failed:"))
            self.stdout.write(traceback.format_exc())
            return

        # --- Step 4: Cloud Folder Creation ---
        self.stdout.write("\nSTEP 4: Creating/finding Cloud Folder...")
        try:
            uploader = req.finance_officer or req.requester
            cloud_folder = CloudService.get_or_create_folder(
                name=req.ref_number,
                department=dept,
                user=uploader,
                project_context=req.ref_number
            )
            self.stdout.write(self.style.SUCCESS(f"  OK  Cloud folder: '{cloud_folder.name}' (ID={cloud_folder.id}, dept={cloud_folder.department})"))
        except Exception:
            self.stdout.write(self.style.ERROR("  FAIL  Cloud folder creation failed:"))
            self.stdout.write(traceback.format_exc())
            return

        # --- Step 5: Upload PDF ---
        self.stdout.write("\nSTEP 5: Uploading requisition PDF...")
        try:
            pdf_file.seek(0)
            cf = CloudService.upload_file(
                folder=cloud_folder,
                uploaded_file=pdf_file,
                user=uploader,
                commit_message=f"Approved Supply Requisition PDF for {req.ref_number}",
                is_internal_only=False
            )
            self.stdout.write(self.style.SUCCESS(f"  OK  PDF uploaded: {cf.name}"))
        except Exception:
            self.stdout.write(self.style.ERROR("  FAIL  PDF upload to cloud failed:"))
            self.stdout.write(traceback.format_exc())

        # --- Step 6: Upload Supporting Doc ---
        self.stdout.write("\nSTEP 6: Uploading supporting document (if any)...")
        if req.uploaded_document:
            try:
                req.uploaded_document.seek(0)
                name = os.path.basename(req.uploaded_document.name)
                wrapped = ContentFile(req.uploaded_document.read(), name=name)
                cf = CloudService.upload_file(
                    folder=cloud_folder, uploaded_file=wrapped, user=uploader,
                    commit_message=f"Requester doc for {req.ref_number}", is_internal_only=False
                )
                self.stdout.write(self.style.SUCCESS(f"  OK  Supporting doc uploaded: {cf.name}"))
            except Exception:
                self.stdout.write(self.style.ERROR("  FAIL  Supporting doc upload failed:"))
                self.stdout.write(traceback.format_exc())
        else:
            self.stdout.write("  SKIP No supporting document attached.")

        # --- Step 7: Upload Quotations ---
        self.stdout.write("\nSTEP 7: Uploading supplier quotations...")
        for q in req.quotations.all():
            if q.quotation_file:
                try:
                    q.quotation_file.seek(0)
                    name = os.path.basename(q.quotation_file.name)
                    wrapped = ContentFile(q.quotation_file.read(), name=f"supplier_{q.order}_{name}")
                    cf = CloudService.upload_file(
                        folder=cloud_folder, uploaded_file=wrapped, user=uploader,
                        commit_message=f"Quotation from {q.supplier_name}", is_internal_only=False
                    )
                    self.stdout.write(self.style.SUCCESS(f"  OK  Quotation uploaded: {cf.name}"))
                except Exception:
                    self.stdout.write(self.style.ERROR(f"  FAIL  Quotation {q.order} upload failed:"))
                    self.stdout.write(traceback.format_exc())
            else:
                self.stdout.write(f"  SKIP Quotation {q.order} has no file.")

        # --- Step 8: Upload Proof of Payment ---
        self.stdout.write("\nSTEP 8: Uploading proof of payment (if any)...")
        if req.proof_of_payment:
            try:
                req.proof_of_payment.seek(0)
                name = os.path.basename(req.proof_of_payment.name)
                wrapped = ContentFile(req.proof_of_payment.read(), name=name)
                cf = CloudService.upload_file(
                    folder=cloud_folder, uploaded_file=wrapped, user=uploader,
                    commit_message=f"Proof of payment for {req.ref_number}", is_internal_only=False
                )
                self.stdout.write(self.style.SUCCESS(f"  OK  Proof of payment uploaded: {cf.name}"))
            except Exception:
                self.stdout.write(self.style.ERROR("  FAIL  Proof of payment upload failed:"))
                self.stdout.write(traceback.format_exc())
        else:
            self.stdout.write("  SKIP No proof of payment attached.")

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS(f"DONE. Cloud folder '{cloud_folder.name}' is ready in the Institutional Cloud."))
        self.stdout.write(f"{'='*60}\n")
