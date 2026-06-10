"""
Sends the HTML report email via Outlook SMTP.
Credentials are loaded from environment variables (set via .env).

Works for:
  - Persoonlijk Outlook.com / Hotmail / Live account  → smtp-mail.outlook.com:587
  - Microsoft 365 zakelijk account                    → smtp.office365.com:587

Zorg dat SMTP AUTH is ingeschakeld voor je account:
  - Outlook.com persoonlijk: werkt direct met je gewone wachtwoord
    (of een app-wachtwoord als je 2FA aan hebt staan)
  - Microsoft 365 zakelijk: SMTP AUTH moet aan staan in het M365 admin center
    (Instellingen → Gebruikers → Actieve gebruikers → gebruiker → Mail → SMTP AUTH)
"""

import logging
import os
import smtplib
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# Persoonlijk Outlook.com/Hotmail/Live
OUTLOOK_SMTP_HOST = "smtp-mail.outlook.com"
# Microsoft 365 zakelijk → gebruik "smtp.office365.com" (zelfde poort)
OUTLOOK_SMTP_PORT = 587


def _build_subject() -> str:
    today = date.today()
    week_ago = today - timedelta(days=7)
    months_nl = {
        1: "jan", 2: "feb", 3: "mrt", 4: "apr", 5: "mei", 6: "jun",
        7: "jul", 8: "aug", 9: "sep", 10: "okt", 11: "nov", 12: "dec",
    }
    date_range = (
        f"{week_ago.day} {months_nl[week_ago.month]} – "
        f"{today.day} {months_nl[today.month]} {today.year}"
    )
    return f"Nieuw vastgoedaanbod boven €2,5M | {date_range}"


def send_report(html_body: str, plain_body: str) -> None:
    """
    Verstuur het wekelijkse rapport via Outlook SMTP.
    Leest OUTLOOK_USER, OUTLOOK_PASSWORD en RECIPIENT_EMAIL uit de omgeving.
    Gooit geen exception bij falen — fouten worden gelogd.
    """
    outlook_user = os.environ.get("OUTLOOK_USER")
    outlook_password = os.environ.get("OUTLOOK_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    if not all([outlook_user, outlook_password, recipient]):
        missing = [
            k for k, v in {
                "OUTLOOK_USER": outlook_user,
                "OUTLOOK_PASSWORD": outlook_password,
                "RECIPIENT_EMAIL": recipient,
            }.items() if not v
        ]
        logger.error(f"Ontbrekende omgevingsvariabelen: {', '.join(missing)}")
        return

    subject = _build_subject()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Lammers Beton Vastgoedmonitor <{outlook_user}>"
    msg["To"] = recipient

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Bepaal de juiste SMTP-server op basis van het domein
    domain = outlook_user.split("@")[-1].lower() if "@" in outlook_user else ""
    if domain in ("outlook.com", "hotmail.com", "live.com", "live.nl", "hotmail.nl"):
        smtp_host = "smtp-mail.outlook.com"
    else:
        # Microsoft 365 zakelijk (bijv. @lammers.nl)
        smtp_host = "smtp.office365.com"

    try:
        with smtplib.SMTP(smtp_host, OUTLOOK_SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(outlook_user, outlook_password)
            server.sendmail(outlook_user, recipient, msg.as_string())
        logger.info(f"E-mail verstuurd naar {recipient} via {smtp_host} | {subject}")
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Outlook authenticatie mislukt. Controleer OUTLOOK_USER en OUTLOOK_PASSWORD. "
            "Bij een zakelijk M365-account: controleer of SMTP AUTH is ingeschakeld "
            "in het Microsoft 365 admin center."
        )
    except smtplib.SMTPException as exc:
        logger.error(f"SMTP-fout bij versturen: {exc}")
    except OSError as exc:
        logger.error(f"Netwerkfout bij versturen: {exc}")
