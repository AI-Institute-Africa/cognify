import os
import base64
from io import BytesIO
from django.core.files.base import ContentFile
import fitz  # PyMuPDF
from docx import Document
from docx.shared import Inches

import tempfile
import uuid


def _get_signatory_info(approver):
    """Return a normalized signatory object for BRD or leave approver contexts."""
    signatory = getattr(approver, 'user', approver)
    name = getattr(signatory, 'get_full_name', None)
    if callable(name):
        full_name = signatory.get_full_name() or getattr(signatory, 'username', '')
    else:
        full_name = getattr(signatory, 'username', '')
    return {
        'full_name': full_name,
        'designation': getattr(approver, 'designation', '') or getattr(approver, 'role', '') or ''
    }

def convert_docx_to_pdf(doc_bytes):
    """
    Attempts to convert docx bytes to pdf bytes using docx2pdf.
    NOTE: docx2pdf requires Word installed on Windows.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        from docx2pdf import convert
        
        # Create temp files
        temp_dir = tempfile.gettempdir()
        temp_id = str(uuid.uuid4())
        
        docx_path = os.path.join(temp_dir, f"{temp_id}.docx")
        pdf_path = os.path.join(temp_dir, f"{temp_id}.pdf")
        
        logger.info(f"Temporary docx path: {docx_path}")
        with open(docx_path, 'wb') as f:
            f.write(doc_bytes)
            
        # Convert
        logger.info("Starting docx2pdf conversion (this may take 10-30 seconds)...")
        
        # COM initialization required for multi-threaded Django views on Windows
        import pythoncom
        pythoncom.CoInitialize()
        try:
            convert(docx_path, pdf_path)
        finally:
            pythoncom.CoUninitialize()
            
        logger.info("docx2pdf conversion finished.")
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file was not created at {pdf_path}")
            return None

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
            
        # Cleanup
        try: os.remove(docx_path)
        except: pass
        try: os.remove(pdf_path)
        except: pass
        
        return pdf_bytes
    except Exception as e:
        logger.exception(f"Docx conversion failed: {e}")
        return None

def get_pdf_cache_path(brd):
    """
    Returns the path to the cached PDF version of a DOCX document.
    Uses file modification time to invalidate the cache if the document is replaced.
    """
    if not brd.document: return None
    try:
        orig_path = str(brd.document.path)
        filename = os.path.basename(orig_path)
        if not filename.lower().endswith(('.docx', '.doc')):
             return None
             
        mtime = int(os.path.getmtime(orig_path))
        cache_dir = os.path.join(os.path.dirname(orig_path), 'cache_v2')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            
        cache_filename = f"{os.path.splitext(filename)[0]}_{mtime}.pdf"
        return os.path.join(cache_dir, cache_filename)
    except Exception:
        return None

def render_document_to_images(brd):
    """
    Reads the BRD document and converts each page to a base64 encoded PNG image.
    Ensures high-fidelity for DOCX by using docx2pdf with a local cache.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not brd.document:
        logger.warning(f"BRD {brd.id} has no document attached.")
        return []

    try:
        logger.info(f"Rendering BRD {brd.id}: {brd.document.name}")
        file_name = brd.document.name.lower()
        doc = None
        
        # ── 0. Prioritize current signed version for sequential signatures ──
        if brd.signed_document:
            try:
                # Use stream to avoid file-locking on Windows
                brd.signed_document.open()
                content = brd.signed_document.read()
                brd.signed_document.close()
                doc = fitz.open(stream=content, filetype="pdf")
                logger.info("Using latest signed version for preview (via stream).")
            except Exception as se:
                logger.warning(f"Could not open signed_document via stream: {se}")
        
        # ── 1. High Fidelity DOCX Conversion (If not already signed/pdf) ──
        if not doc and file_name.endswith(('.docx', '.doc')):
            cache_path = get_pdf_cache_path(brd)
            if cache_path and os.path.exists(cache_path):
                logger.info(f"Using cached PDF: {cache_path}")
                doc = fitz.open(cache_path)
            else:
                # Try docx2pdf (Requires Word)
                try:
                    brd.document.open()
                    content = brd.document.read()
                    brd.document.close()
                    pdf_bytes = convert_docx_to_pdf(content)
                    if pdf_bytes:
                        if cache_path:
                            with open(cache_path, 'wb') as f: f.write(pdf_bytes)
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                except Exception as de:
                    logger.warning(f"docx2pdf failed: {de}")

        # ── 2. Native Path Open (Most reliable) ──
        if not doc:
            try:
                # Direct path access is faster and more reliable in PyMuPDF for docx/pdf
                doc = fitz.open(brd.document.path)
                logger.info("Successfully opened document via direct path.")
            except Exception as pe:
                logger.warning(f"Path open failed: {pe}. Trying stream open...")
                try:
                    brd.document.open()
                    content = brd.document.read()
                    brd.document.close()
                    doc = fitz.open(stream=content, filetype=file_name.split('.')[-1])
                except Exception as se:
                    logger.error(f"Stream open failed: {se}")

        if not doc or len(doc) == 0:
            logger.error(f"FATAL: All rendering methods failed for BRD {brd.id}.")
            return []

        pages_metadata = []
        logger.info(f"Opening document with {len(doc)} pages.")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Capture actual PDF page dimensions
            p_width = page.rect.width
            p_height = page.rect.height
            
            # Use 2.0x zoom for high-fidelity rendering to see signatures clearly
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img_b64 = base64.b64encode(pix.tobytes("png")).decode('utf-8')
            pages_metadata.append({
                "page_num": page_num,
                "image": f"data:image/png;base64,{img_b64}",
                "width": p_width,
                "height": p_height
            })
            if page_num % 10 == 0 and page_num > 0:
                logger.debug(f"Rendered {page_num} pages...")
                
        doc.close()
        logger.info(f"Successfully rendered {len(pages_metadata)} pages for BRD {brd.id}.")
        return pages_metadata

    except Exception as e:
        logger.exception(f"Error rendering document images for BRD {brd.id}: {e}")
        return []

def stamp_signature_at_coordinates(brd, approver, signature_data_b64, page_num, x_pct, y_pct, ip_address, timestamp, date_page=None, date_x=None, date_y=None):
    """
    Stamps the signature onto the document exactly at the specified percentage coordinates and page.
    Optionally stamps a date string if coordinates are provided.
    """
    import logging
    logger = logging.getLogger(__name__)

    if not brd.document or not signature_data_b64:
        logger.warning("Missing document or signature data for stamping.")
        return False
        
    try:
        logger.info(f"Signature data prefix: {signature_data_b64[:50]}...")
        if ';base64,' in signature_data_b64:
            format, imgstr = signature_data_b64.split(';base64,')
        else:
            imgstr = signature_data_b64
        img_data = base64.b64decode(imgstr)
        logger.info(f"Decoded image size: {len(img_data)} bytes")
        # ── 1. Document Opening with Safe Dual Temp File Strategy ──
        # This is the most bulletproof way to handle PDFs on Windows: never overwrite the open file
        import tempfile
        import shutil
        tin_fd, temp_in_path = tempfile.mkstemp(suffix=".in.pdf")
        os.close(tin_fd)
        tout_fd, temp_out_path = tempfile.mkstemp(suffix=".out.pdf")
        os.close(tout_fd)
        
        doc = None
        
        try:
            if brd.signed_document:
                # Copy existing signed doc to temp
                brd.signed_document.open('rb')
                with open(temp_in_path, 'wb') as f:
                    f.write(brd.signed_document.read())
                brd.signed_document.close()
                doc = fitz.open(temp_in_path)
                logger.info(f"Loaded existing signed doc for signing: size={os.path.getsize(temp_in_path)}")
            else:
                file_name = brd.document.name.lower()
                is_docx = file_name.endswith(('.docx', '.doc'))
                
                if is_docx:
                    cache_path = get_pdf_cache_path(brd)
                    if cache_path and os.path.exists(cache_path):
                        shutil.copy2(cache_path, temp_in_path)
                        doc = fitz.open(temp_in_path)
                    else:
                        brd.document.open('rb')
                        pdf_bytes = convert_docx_to_pdf(brd.document.read())
                        brd.document.close()
                        if pdf_bytes:
                            with open(temp_in_path, 'wb') as f: f.write(pdf_bytes)
                            doc = fitz.open(temp_in_path)
                
                if not doc: 
                    brd.document.open('rb')
                    content = brd.document.read()
                    brd.document.close()
                    
                    if file_name.endswith('.pdf'):
                        with open(temp_in_path, 'wb') as f: f.write(content)
                        doc = fitz.open(temp_in_path)
                    else:
                        doc = fitz.open(stream=content, filetype=file_name.split('.')[-1])
                
        except Exception as e:
            logger.error(f"Temp file setup failed: {e}")
            if os.path.exists(temp_in_path): os.remove(temp_in_path)
            if os.path.exists(temp_out_path): os.remove(temp_out_path)
            return False

        if doc is None or len(doc) == 0:
            if os.path.exists(temp_in_path): os.remove(temp_in_path)
            if os.path.exists(temp_out_path): os.remove(temp_out_path)
            return False

        # ── 1. Stamp Signature ──
        if page_num < 0: page_num = 0
        if page_num >= len(doc): page_num = len(doc) - 1
            
        page = doc[page_num]
        p_width = page.rect.width
        p_height = page.rect.height
        
        x0 = p_width * (x_pct / 100.0)
        y0 = p_height * (y_pct / 100.0)
        
        # Precise Stamp Size (Synced with frontend 8% width to fit in cells)
        sw = p_width * 0.08
        sh = sw * 0.5  # Maintain 2:1 aspect ratio
        image_rect = fitz.Rect(x0, y0, x0 + sw, y0 + sh)
        
        # Safety bound check: nudge if touching edge
        if image_rect.x1 > p_width:
             diff = image_rect.x1 - p_width
             image_rect.x1 -= diff; image_rect.x0 -= (diff + 2)
        if image_rect.y1 > p_height:
             diff = image_rect.y1 - p_height
             image_rect.y1 -= diff; image_rect.y0 -= (diff + 2)
        
        logger.info(f"Stamping signature on page {page_num} at rect: {image_rect}")
        page.insert_image(image_rect, stream=img_data, overlay=True, keep_proportion=True)
        logger.info(f"Image inserted. Page images: {len(page.get_images())}")
        
        # Minimalist Metadata (Discrete 5pt font)
        signatory = _get_signatory_info(approver)
        details = f"DIGITAL SIGNATURE: {signatory['full_name']} | {timestamp.strftime('%Y-%m-%d')} | IP:{ip_address}"
        page.insert_text((image_rect.x0, image_rect.y1 + 6), details, fontsize=5, fontname="helv", color=(0.1, 0.1, 0.4))

        # ── 2. Stamp Date (Optional) ──
        if date_page is not None and date_x is not None and date_y is not None:
             try:
                 d_page_num = int(date_page)
                 if 0 <= d_page_num < len(doc):
                     d_page = doc[d_page_num]
                     dx0 = d_page.rect.width * (float(date_x) / 100.0)
                     dy0 = d_page.rect.height * (float(date_y) / 100.0)
                     
                     # PyMuPDF insert_text uses the bottom-left baseline. We must shift it down 
                     # by the font size (11) so it doesn't render above the dropped point.
                     dy0 += 11
                     
                     date_str = timestamp.strftime('%Y-%m-%d')
                     d_page.insert_text((dx0, dy0), date_str, fontsize=11, fontname="helv-bo", color=(0, 0, 0))
                     logger.info(f"Date stamped on page {d_page_num} at {date_x},{date_y}")
             except Exception as de:
                 logger.error(f"Error stamping date: {de}")

        # Save changes robustly using dual-temp strategy
        try:
            doc.save(temp_out_path, garbage=3, deflate=True)
            doc.close()
            
            with open(temp_out_path, 'rb') as f:
                out_bytes = f.read()
            
            logger.info(f"Final PDF dynamically saved: {len(out_bytes)} bytes")
        finally:
            if os.path.exists(temp_in_path):
                try: os.remove(temp_in_path)
                except: pass
            if os.path.exists(temp_out_path):
                try: os.remove(temp_out_path)
                except: pass

        # Save to storage
        orig_name = os.path.basename(brd.document.name)
        base_name = os.path.splitext(orig_name)[0]
        output_filename = f"{base_name}_signed.pdf"
            
        brd.signed_document.save(output_filename, ContentFile(out_bytes), save=False)
        brd.save(update_fields=['signed_document', 'updated_at'])
        logger.info(f"Stamping complete. signed_document saved as {brd.signed_document.name}")
        return True

    except Exception as e:
        logger.exception(f"Error stamping document: {e}")
        return False

    except Exception as e:
        logger.exception(f"Error stamping document at coordinates: {e}")
        return False

def append_signature_to_document(brd, approver, signature_data_b64, ip_address, timestamp):
    """
    (Fallback) Stamps the signature onto the BRD Document by appending a signature certificate page.
    Supported auto-stamping formats: .pdf, .docx
    """
    import logging
    logger = logging.getLogger(__name__)
    if not brd.document or not signature_data_b64:
        return

    try:
        # Extract base64 image data
        if ';base64,' in signature_data_b64:
            format, imgstr = signature_data_b64.split(';base64,')
        else:
            imgstr = signature_data_b64
            
        img_data = base64.b64decode(imgstr)

        # Read the file content into memory (sequential: use signed_document if it exists)
        if brd.signed_document:
            brd.signed_document.open()
            file_content = brd.signed_document.read()
            brd.signed_document.close()
            file_name = brd.signed_document.name.lower()
        else:
            brd.document.open()
            file_content = brd.document.read()
            brd.document.close()
            file_name = brd.document.name.lower()

        if file_name.endswith('.pdf'):
            doc = fitz.open(stream=file_content, filetype="pdf")
            page = doc.new_page()
            
            # Header
            title = f"Digital Signature Certificate"
            page.insert_text((50, 50), title, fontsize=18, fontname="helv-bo", color=(0, 0, 0))
            
            signatory = _get_signatory_info(approver)
            # Details
            details = [
                f"Document: {brd.title}",
                f"Signatory: {signatory['full_name']}",
                f"Role / Designation: {signatory['designation']}",
                f"Date Signed: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                f"IP Address: {ip_address}",
                "--------------------------------------------------"
            ]
            y = 80
            for line in details:
                page.insert_text((50, y), line, fontsize=11, fontname="helv", color=(0, 0, 0))
                y += 20
                
            # Signature Image
            image_rect = fitz.Rect(50, y+10, 250, y+80) # x0, y0, x1, y1
            page.insert_image(image_rect, stream=img_data)
            
            # Footer
            footer = f"Generated by Project Governance System"
            page.insert_text((50, y+110), footer, fontsize=9, fontname="helv-ob", color=(0.4, 0.4, 0.4))
            
            pdf_bytes = doc.write()
            doc.close()
            
            # Save to signed_document
            output_filename = os.path.splitext(os.path.basename(brd.document.name))[0] + "_stamped.pdf"
            brd.signed_document.save(output_filename, ContentFile(pdf_bytes), save=True)
            
        elif file_name.endswith('.docx') or file_name.endswith('.doc'):
            doc = Document(BytesIO(file_content))
            doc.add_page_break()
            doc.add_heading('Digital Signature Certificate', level=1)
            
            signatory = _get_signatory_info(approver)
            p = doc.add_paragraph()
            p.add_run(f"Document: {brd.title}\n").bold = True
            p.add_run(f"Signatory: {signatory['full_name']}\n")
            p.add_run(f"Role / Designation: {signatory['designation']}\n")
            p.add_run(f"Date Signed: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            p.add_run(f"IP Address: {ip_address}\n")
            
            img_stream = BytesIO(img_data)
            doc.add_picture(img_stream, width=Inches(2.5))
            doc.add_paragraph("Generated by Project Governance System")
            
            out_stream = BytesIO()
            doc.save(out_stream)
            
            # Save to signed_document
            output_filename = os.path.splitext(os.path.basename(brd.document.name))[0] + "_stamped.docx"
            brd.signed_document.save(output_filename, ContentFile(out_stream.getvalue()), save=True)
            
    except Exception as e:
        logger.exception(f"Error stamping document {brd.id}: {str(e)}")
        # We don't want to crash the whole application if stamping fails (e.g. corrupt file)
        # The database signature record is still created safely.
        pass

def extract_text_from_document(brd):
    """Extracts raw text from the original document for AI summarization."""
    import fitz
    import os
    from django.conf import settings
    
    # Try converted PDF first if it exists in cache
    cache_dir = os.path.join(settings.MEDIA_ROOT, 'cache_v2')
    pdf_path = os.path.join(cache_dir, f"{brd.pk}.pdf")
    
    if not os.path.exists(pdf_path):
        # Fallback to original document
        pdf_path = brd.document.path
        
    text = ""
    if pdf_path.lower().endswith('.pdf'):
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except: pass
    elif pdf_path.lower().endswith('.docx'):
        try:
            from docx import Document
            from io import BytesIO
            brd.document.open()
            doc = Document(BytesIO(brd.document.read()))
            brd.document.close()
            text = "\n".join([para.text for para in doc.paragraphs])
        except: pass
        
    return text.strip()
