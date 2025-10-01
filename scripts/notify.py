import os
import smtplib
from email.message import EmailMessage

TO = os.environ.get("TO_EMAIL")
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
FROM_EMAIL = os.environ.get("FROM_EMAIL") or SMTP_USERNAME

tests_status = os.environ.get("TESTS_STATUS", "unknown")
package_status = os.environ.get("PACKAGE_STATUS", "unknown")
sha = (os.environ.get("GIT_SHA") or "")[:8]
branch = os.environ.get("GIT_BRANCH", "")
run_id = os.environ.get("GITHUB_RUN_ID", "")
run_number = os.environ.get("GITHUB_RUN_NUMBER", "")

if not TO:
    raise SystemExit("TO_EMAIL não definido.")
if not (SMTP_SERVER and SMTP_USERNAME and SMTP_PASSWORD):
    raise SystemExit("Variáveis SMTP ausentes.")

subject = f"[CI/Jenkins] Pipeline executado #{run_number} ({branch}@{sha})"
body = f"""\
Pipeline executado no Jenkins!

Status:
- Tests:   {tests_status}
- Package: {package_status}

Build: {run_number}
Branch: {branch}
Commit: {sha}

(Artefatos e relatórios disponíveis na página do build do Jenkins)
"""

msg = EmailMessage()
msg["Subject"] = subject
msg["From"] = FROM_EMAIL
msg["To"] = TO
msg.set_content(body)

with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
    try:
        smtp.starttls()
    except Exception:
        pass
    smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
    smtp.send_message(msg)

print("Notificação enviada para:", TO)
