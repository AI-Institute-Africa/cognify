import os
import django
import sys
import io
import zipfile

# Setup django environment
sys.path.append(r"c:\Users\USER 2\Desktop\aiiagov\project1\project1\land_registry")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "land_registry.settings")
django.setup()

from registry.models import SupplyRequisition, Category, SubCategory, File, Department, CloudFolder, CloudFile, CloudFileVersion
from registry.views import generate_supply_requisition_pdf
from registry.services.cloud import CloudService
from django.core.files.base import ContentFile
from django.contrib.auth.models import User

def run_migration():
    print("Starting Purchase Requisitions Migration...")
    
    # 1. Ensure the new SubCategory exists
    proc_cat, _ = Category.objects.get_or_create(name='Procurement', defaults={'description': 'Procurement Files'})
    purchase_subcat, _ = SubCategory.objects.get_or_create(
        category=proc_cat, 
        name='Purchase Requisitions', 
        defaults={'description': 'Purchase Requisition Files'}
    )
    
    # 2. Query all SupplyRequisitions ordered by id
    requisitions = SupplyRequisition.objects.order_by('id')
    
    for idx, req in enumerate(requisitions, 1):
        old_ref = req.ref_number
        new_ref = f"NBSZ-{idx:05d}"
        
        print(f"\n--- Migrating {old_ref} -> {new_ref} (ID: {req.id}) ---")
        
        # A. Update Requisition
        req.ref_number = new_ref
        req.save()
        print(f"Updated SupplyRequisition ref_number to {new_ref}")
        
        # B. Update associated Registry Files
        reg_files = File.objects.filter(ref_num=old_ref)
        for rf in reg_files:
            rf.ref_num = new_ref
            rf.sub_category = purchase_subcat
            rf.title = rf.title.replace(old_ref, new_ref).replace("Supply Requisition", "Purchase Requisition")
            rf.description = rf.description.replace(old_ref, new_ref).replace("Supply Requisition", "Purchase Requisition")
            
            # If the requisition is Approved/Paid, regenerate the PDF with the logo and new reference
            if req.status == 'Approved':
                print("Regenerating PDF...")
                pdf_file = generate_supply_requisition_pdf(req)
                rf.file_attachment = pdf_file
                
            rf.save()
            print(f"Updated Registry File: {rf.title} (ID: {rf.id})")
            
        # C. Update Cloud Folders
        folders = CloudFolder.objects.filter(project_context=old_ref)
        for cf in folders:
            cf.project_context = new_ref
            cf.name = "Purchase Requisitions"
            cf.save()
            print(f"Updated CloudFolder context to {new_ref} and name to Purchase Requisitions")
            
            # Clean out files with old reference inside the cloud folder, then re-upload updated ones
            CloudFile.objects.filter(folder=cf).delete()
            print("Cleared old CloudFiles from the folder.")
            
            # Now upload the new files
            finance_user = req.finance_officer or User.objects.filter(is_superuser=True).first()
            if finance_user:
                # 1. Regenerated PDF
                pdf_file = generate_supply_requisition_pdf(req)
                pdf_file.seek(0)
                CloudService.upload_file(
                    folder=cf,
                    uploaded_file=pdf_file,
                    user=finance_user,
                    commit_message=f"Approved Purchase Requisition PDF for {new_ref}",
                    is_internal_only=False
                )
                print("Uploaded regenerated PDF to Cloud.")
                
                # 2. Requester document (if any)
                if req.uploaded_document:
                    try:
                        req.uploaded_document.seek(0)
                        name = os.path.basename(req.uploaded_document.name)
                        wrapped_file = ContentFile(req.uploaded_document.read(), name=name)
                        CloudService.upload_file(
                            folder=cf,
                            uploaded_file=wrapped_file,
                            user=finance_user,
                            commit_message=f"Requester document for {new_ref}",
                            is_internal_only=False
                        )
                        print(f"Uploaded requester document: {name}")
                    except Exception as e:
                        print(f"Failed to upload requester doc: {e}")
                        
                # 3. Supplier quotations
                for q in req.quotations.all():
                    if q.quotation_file:
                        try:
                            q.quotation_file.seek(0)
                            name = os.path.basename(q.quotation_file.name)
                            wrapped_file = ContentFile(q.quotation_file.read(), name=f"supplier_{q.order}_{name}")
                            CloudService.upload_file(
                                folder=cf,
                                uploaded_file=wrapped_file,
                                user=finance_user,
                                commit_message=f"Quotation from {q.supplier_name} for {new_ref}",
                                is_internal_only=False
                            )
                            print(f"Uploaded supplier quotation: {name}")
                        except Exception as e:
                            print(f"Failed to upload supplier quotation: {e}")
                            
                # 4. Proof of payment
                if req.proof_of_payment:
                    try:
                        req.proof_of_payment.seek(0)
                        name = os.path.basename(req.proof_of_payment.name)
                        wrapped_file = ContentFile(req.proof_of_payment.read(), name=name)
                        CloudService.upload_file(
                            folder=cf,
                            uploaded_file=wrapped_file,
                            user=finance_user,
                            commit_message=f"Proof of payment for {new_ref}",
                            is_internal_only=False
                        )
                        print(f"Uploaded proof of payment: {name}")
                    except Exception as e:
                        print(f"Failed to upload proof of payment: {e}")
                        
                # 5. Compiled ZIP file
                zip_buffer = io.BytesIO()
                has_files = False
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    if req.uploaded_document:
                        try:
                            req.uploaded_document.seek(0)
                            name = os.path.basename(req.uploaded_document.name)
                            zip_file.writestr(f"1_requester_document/{name}", req.uploaded_document.read())
                            has_files = True
                        except Exception:
                            pass
                    for q in req.quotations.all():
                        if q.quotation_file:
                            try:
                                q.quotation_file.seek(0)
                                name = os.path.basename(q.quotation_file.name)
                                zip_file.writestr(f"2_supplier_quotations/supplier_{q.order}_{name}", q.quotation_file.read())
                                has_files = True
                            except Exception:
                                pass
                    if req.proof_of_payment:
                        try:
                            req.proof_of_payment.seek(0)
                            name = os.path.basename(req.proof_of_payment.name)
                            zip_file.writestr(f"3_proof_of_payment/{name}", req.proof_of_payment.read())
                            has_files = True
                        except Exception:
                            pass
                            
                if has_files:
                    zip_buffer.seek(0)
                    zip_file_wrapped = ContentFile(zip_buffer.getvalue(), name=f"{new_ref}_compiled_documents.zip")
                    CloudService.upload_file(
                        folder=cf,
                        uploaded_file=zip_file_wrapped,
                        user=finance_user,
                        commit_message=f"Compiled documentation ZIP for {new_ref}",
                        is_internal_only=False
                    )
                    print(f"Uploaded compiled ZIP: {new_ref}_compiled_documents.zip")

    # D. Delete old SubCategory if empty
    old_subcat = SubCategory.objects.filter(name='Supply Requisitions').first()
    if old_subcat:
        if not File.objects.filter(sub_category=old_subcat).exists():
            old_subcat.delete()
            print("\nDeleted empty old SubCategory 'Supply Requisitions'")
            
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    run_migration()
