import os, smtplib, socket, ssl
from email.message import EmailMessage

to_email   = os.environ.get("TO_EMAIL", "")
from_email = os.environ.get("FROM_EMAIL", "ci@jenkins.local")
smtp_host  = os.environ.get("SMTP_SERVER", "smtp.mailtrap.io")
smtp_port  = int(os.environ.get("SMTP_PORT", "2525"))
smtp_user  = os.environ.get("SMTP_USERNAME", "")
smtp_pass  = os.environ.get("SMTP_PASSWORD", "")
tests      = os.environ.get("TESTS_STATUS", "UNKNOWN")
package    = os.environ.get("PACKAGE_STATUS", "UNKNOWN")
sha        = os.environ.get("GIT_SHA", "")
branch     = os.environ.get("GIT_BRANCH", "")
run_id     = os.environ.get("GITHUB_RUN_ID", "")
run_num    = os.environ.get("GITHUB_RUN_NUMBER", "")

body = f"""Pipeline Jenkins finalizado.

Branch: {branch}
Commit: {sha}

Testes:   {tests}
Empacote: {package}

Run ID: {run_id}
Run #:  {run_num}
Host:   {socket.gethostname()}
"""

msg = EmailMessage()
msg["Subject"] = f"[CI] {branch} @ {sha} — tests:{tests} pkg:{package}"
msg["From"] = from_email
msg["To"] = to_email
msg.set_content(body)

ctx = ssl.create_default_context()
with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
    s.ehlo()
    try:
        s.starttls(context=ctx)
        s.ehlo()
    except Exception as e:
        print("WARN: STARTTLS não disponível ou falhou:", e)
    if smtp_user or smtp_pass:
        s.login(smtp_user, smtp_pass)
    s.send_message(msg)
print("Email enviado para", to_email)
