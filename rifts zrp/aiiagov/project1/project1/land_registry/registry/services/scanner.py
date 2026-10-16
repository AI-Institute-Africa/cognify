import re
import os
from django.utils import timezone
from registry.models import ScannerDevice, ScannedDocument, File, Requisition, Contract, LeaveRequest, RetentionRule
from registry.services.ai_assistant import AIAssistantService

class ScannerService:
    @staticmethod
    def ingest(uploaded_file, scanner_token):
        """
        Authenticates a scanner and saves the raw upload.
        """
        try:
            scanner = ScannerDevice.objects.get(api_key=scanner_token, is_active=True)
            doc = ScannedDocument.objects.create(
                scanner=scanner,
                raw_file=uploaded_file,
                status='Pending'
            )
            return doc
        except ScannerDevice.DoesNotExist:
            return None

    @staticmethod
    def process_document(doc_id):
        """
        High-level pipeline: OCR -> Classify -> Link -> Retention
        """
        try:
            doc = ScannedDocument.objects.get(id=doc_id)
            doc.status = 'Processing'
            doc.save()

            # 1. OCR (Placeholder for Tesseract/Cloud OCR)
            if not doc.extracted_text:
                doc.extracted_text = ScannerService._mock_ocr(doc)
            
            # 2. AI Classification
            doc.classification, doc.confidence_score = ScannerService._classify_content(doc.extracted_text)
            
            # 3. Entity Extraction
            ScannerService._extract_entities(doc)
            
            # 4. Automatic Linking
            ScannerService._auto_link(doc)
            
            # 4. Success
            doc.status = 'Completed' if doc.linked_file or doc.linked_requisition or doc.linked_contract or doc.linked_leave_request else 'Awaiting Link'
            doc.processed_at = timezone.now()
            doc.save()
            
            return doc
        except Exception as e:
            if 'doc' in locals():
                doc.status = 'Failed'
                doc.metadata['error'] = str(e)
                doc.save()
            return None

    @staticmethod
    def _mock_ocr(doc):
        """
        Simulates OCR text extraction.
        In a real RIFTS-X enterprise setup, this would hook into a Tesseract or AWS Textract worker.
        """
        filename = doc.raw_file.name.lower()
        
        # Smart mock: use filename to suggest content
        content = f"RIFTS-X AUTO-SCAN: {filename}\n"
        if 'title' in filename or 'deed' in filename or 'land' in filename:
            content += "Official Land Registry Record. Title Deed information included."
        elif 'contract' in filename or 'agreement' in filename:
            content += "Formal Agreement and Contract details."
        else:
            content += "Content summary for general classification."
            
        return content

    @staticmethod
    def _classify_content(text):
        """
        Uses heuristics and AIAssistant patterns to classify the doc.
        """
        if not text:
            return "Unknown", 0.0
            
        text = text.lower()
        if any(word in text for word in ['contract', 'agreement', 'tender', 'mou']):
            return "Contract", 0.9
        elif any(word in text for word in ['leave', 'vacation', 'sick', 'time off']):
            return "LeaveRequest", 0.85
        elif any(word in text for word in ['requisition', 'purchase', 'p.o.', 'request for goods']):
            return "Requisition", 0.8
        elif any(word in text for word in ['land', 'title', 'deed', 'registry', 'parcel', 'folio']):
            return "File", 0.95
        elif 'ref-' in text or 'ref:' in text:
            return "File", 0.6 # Moderate guess if ref is present
            
        return "General Document", 0.5

    @staticmethod
    def _auto_link(doc):
        """
        Attempts to find matching entities in the system.
        """
        text = doc.extracted_text.lower()
        
        # Look for Reference Numbers (e.g., REF-SCAN-001, CONT-456)
        # We look for matches and try to find one that isn't a known system tag like RIFTS-X or AUTO-SCAN
        text_content = doc.extracted_text
        ref_matches = re.findall(r'([A-Z0-9]{3,}(?:-[A-Z0-9]{1,})+)', text_content)
        
        ref_num = None
        # Prioritize ones with digits
        for m in ref_matches:
            val = m.upper()
            if val not in ['RIFTS-X', 'AUTO-SCAN'] and any(c.isdigit() for c in val):
                ref_num = val
                break
        
        # Fallback to first non-system tag if no digits
        if not ref_num:
            for m in ref_matches:
                val = m.upper()
                if val not in ['RIFTS-X', 'AUTO-SCAN']:
                    ref_num = val
                    break
        
        if ref_num:
            if doc.classification == "File":
                doc.linked_file = File.objects.filter(ref_num=ref_num).first()
            elif doc.classification == "Contract":
                doc.linked_contract = Contract.objects.filter(contract_ref=ref_num).first()
            elif doc.classification == "Requisition":
                # Assuming item name or search for logic
                pass

        # If it's linked to a File, assign retention
        if doc.linked_file:
            ScannerService.assign_retention(doc.linked_file)

    @staticmethod
    def assign_retention(file_obj):
        """
        Assigns retention rules based on category.
        """
        if not file_obj.retention_rule:
            # Default logic: Legal docs get 10 years, General 5, Financial 7
            cat_name = file_obj.sub_category.category.name.lower()
            
            rule_name = "General Retention"
            years = 5
            
            if 'legal' in cat_name or 'land' in cat_name:
                rule_name = "Legal/Permanent Retention"
                years = 10
            elif 'finance' in cat_name or 'budget' in cat_name:
                rule_name = "Financial Retention"
                years = 7
                
            rule, _ = RetentionRule.objects.get_or_create(
                name=rule_name,
                defaults={'years_to_keep': years}
            )
            
            file_obj.retention_rule = rule
            file_obj.expiry_date = timezone.now().date() + timezone.timedelta(days=years*365)
            file_obj.save()

    @staticmethod
    def _extract_entities(doc):
        """
        AI-Powered Entity Extraction.
        Parses Names, Dates, Amounts, and Reference Numbers.
        """
        text = doc.extracted_text
        metadata = doc.metadata or {}
        
        # 1. Names (Simulated with simple pattern or AI call)
        # In a real setup, we'd use a Spacy NER model or AIAssistant
        name_match = re.search(r'(?:Name|Signed by|Authorized by):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
        if name_match:
            metadata['extracted_name'] = name_match.group(1)
            
        # 2. Dates
        date_matches = re.findall(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
        if date_matches:
            metadata['extracted_dates'] = date_matches
            
        # 3. Amounts (Currency)
        amount_match = re.search(r'(?:\$|USD|UGX|ZWL)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        if amount_match:
            val = float(amount_match.group(1).replace(',', ''))
            metadata['extracted_amount'] = val
            
        # 4. Reference Numbers (already handled for linking, but store in metadata too)
        ref_match = re.search(r'([A-Z0-9]{3,}(?:-[A-Z0-9]{1,})+)', text)
        if ref_match:
            metadata['ref_num'] = ref_match.group(1).upper()

        doc.metadata = metadata
        doc.save()
