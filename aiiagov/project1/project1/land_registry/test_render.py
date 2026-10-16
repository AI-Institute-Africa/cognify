import fitz
import os
import sys

def test_render(path):
    print(f"Testing {path}...")
    try:
        doc = fitz.open(path)
        print(f"Successfully opened! Pages: {len(doc)}")
        for i in range(min(1, len(doc))):
            page = doc[i]
            pix = page.get_pixmap()
            print(f"Page {i} rendered to pixmap: {pix.width}x{pix.height}")
        doc.close()
    except Exception as e:
        print(f"Failed to open/render: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    file_path = r"C:\Users\USER 2\Downloads\project1\project1\land_registry\media\brds\originals\Digital_Banking_Branch_-_Proposal_002.docx"
    if os.path.exists(file_path):
        test_render(file_path)
    else:
        print(f"File not found: {file_path}")
