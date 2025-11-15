echo "📤 Enviando e-mail via Mailtrap..."
pwd

python3 <<EOF
import smtplib
from email.mime.text import MIMEText
import os

EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")
MAILTRAP_USER = os.getenv("USERNAME")
MAILTRAP_PASS = os.getenv("PASSWORD")

msg = MIMEText("✅ O pipeline foi executado com sucesso!")
msg["Subject"] = "Status do Jenkins - Pipeline Concluído"
msg["From"] = "jenkins@flagit.com"
msg["To"] = EMAIL_DESTINO

try:
    with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
        server.starttls()
        server.login(MAILTRAP_USER, MAILTRAP_PASS)
        server.send_message(msg)
    print("✅ E-mail enviado com sucesso para:", EMAIL_DESTINO)
except Exception as e:
    print("❌ Erro ao enviar e-mail:", e)
EOF