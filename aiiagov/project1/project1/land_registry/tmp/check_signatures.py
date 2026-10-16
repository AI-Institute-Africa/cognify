import os
import django
import sys

# Set up Django environment
sys.path.append(r'c:\Users\USER 2\Downloads\project1\project1\land_registry')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry.models import BRD
import fitz

def check_brds():
    log_file = r'c:\Users\USER 2\Downloads\project1\project1\land_registry\tmp\debug_log.txt'
    with open(log_file, 'w', encoding='utf-8') as f:
        brds = BRD.objects.exclude(signed_document='').order_by('-id')[:5]
        for brd in brds:
            f.write(f"BRD {brd.id}: {brd.title}\n")
            f.write(f"  Signed Document: {brd.signed_document.name}\n")
            if os.path.exists(brd.signed_document.path):
                f.write(f"  File exists: Yes ({os.path.getsize(brd.signed_document.path)} bytes)\n")
                try:
                    doc = fitz.open(brd.signed_document.path)
                    f.write(f"  Pages: {len(doc)}\n")
                    for i in range(len(doc)):
                        page = doc[i]
                        img_list = page.get_images()
                        if img_list:
                            f.write(f"    Page {i}: {len(img_list)} images found\n")
                    doc.close()
                except Exception as e:
                    f.write(f"  Error opening PDF: {e}\n")
            else:
                f.write(f"  File exists: No\n")
            f.write("-" * 20 + "\n")

if __name__ == "__main__":
    check_brds()
