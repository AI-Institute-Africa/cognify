import smtplib
import ssl

host = "smtp.gmail.com"
port = 587
user = "takuechakanyuka@gmail.com"
password = "hsgz yony gxag gmnv"
recipient = "confluencesystemspvtltd@gmail.com"

print(f"Connecting to {host}:{port}...")

try:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with smtplib.SMTP(host, port) as server:
        server.set_debuglevel(1)
        server.starttls(context=context)
        server.login(user, password)
        server.sendmail(user, recipient, "Subject: SMTP Raw Test\n\nTesting raw smtplib connection.")
    print("\nSUCCESS: Raw SMTP test completed.")
except Exception as e:
    print(f"\nFAILURE: Raw SMTP test failed. Error: {e}")
    import traceback
    traceback.print_exc()
