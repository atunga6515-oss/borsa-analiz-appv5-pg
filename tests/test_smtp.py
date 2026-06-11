import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg['Subject'] = "AlfaBIST Terminal - Yeni İletişim Talebi (test)"
msg['From'] = "user@example.com"
msg['To'] = "admin@example.com"
body = "Yeni bir iletişim / demo talebi aldınız:\n\nAd Soyad: dfghjklş\nE-posta: test@test.com\n\nMesaj:\nhghuk\n\xa0"
msg.set_content(body)

print("Headers:", msg.items())
print("Body:", msg.get_payload())
try:
    s = msg.as_string()
    print("as_string works")
except Exception as e:
    print("as_string error:", e)

