# scripts/notify.py
import os
import smtplib
from email.message import EmailMessage
import sys
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--status", default="unknown")
    p.add_argument("--run-id", default="")
    p.add_argument("--repo", default="")
    p.add_argument("--branch", default="")
    args = p.parse_args()

    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "2525"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    EMAIL_TO = os.getenv("EMAIL_TO")

    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_TO):
        print("Faltam variáveis SMTP/EMAIL_TO", file=sys.stderr)
        sys.exit(2)

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = f"Pipeline: {args.status} (run {args.run_id})"
    body = f"Repo: {args.repo}\nBranch: {args.branch}\nStatus: {args.status}\nRun: {args.run_id}"
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        print("Email enviado com sucesso.")
    except Exception as e:
        print("Erro ao enviar email:", e, file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
