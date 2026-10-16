import qrcode
from io import BytesIO
from django.core.files import File as DjangoFile
from registry.models import File

def generate_file_qr(file_id):
    """
    Generates a QR code for a specific file and saves it to the model.
    The QR data contains the file's reference number and a verification URL.
    """
    try:
        file_obj = File.objects.get(id=file_id)
        
        # QR Data: We use the ref_num as the primary identifier
        qr_data = f"RIFTS-X|{file_obj.ref_num}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO to upload to ImageField
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f'qr_{file_obj.ref_num}.png'
        
        file_obj.qr_code.save(filename, DjangoFile(buffer), save=True)
        return True
    except Exception as e:
        print(f"Error generating QR for file {file_id}: {e}")
        return False
