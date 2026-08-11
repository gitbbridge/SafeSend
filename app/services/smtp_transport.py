from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Callable


@dataclass(slots=True)
class SMTPResult:
    success: bool
    status: str
    smtp_code: int | None = None
    response: str = ""
    transient: bool = False


class SMTPTransport:
    def send(self, profile: dict, message: EmailMessage) -> SMTPResult:
        mode = profile.get("security_mode") or "STARTTLS"
        host = profile["host"]
        port = int(profile["port"])
        client = None
        try:
            if mode in {"SSL/TLS", "SSL"}:
                client = smtplib.SMTP_SSL(host, port, timeout=30, context=ssl.create_default_context())
            else:
                client = smtplib.SMTP(host, port, timeout=30)
                client.ehlo()
                if mode in {"STARTTLS", "TLS"}:
                    client.starttls(context=ssl.create_default_context())
                    client.ehlo()
            username = profile.get("username") or ""
            password = profile.get("password") or ""
            if username or password:
                client.login(username, password)
            client.send_message(message)
            return SMTPResult(True, "SENT", response="Message accepted")
        except smtplib.SMTPAuthenticationError as exc:
            return SMTPResult(False, "AUTH_ERROR", exc.smtp_code, str(exc.smtp_error or exc), transient=False)
        except smtplib.SMTPResponseException as exc:
            transient = 400 <= int(exc.smtp_code or 0) < 500
            return SMTPResult(False, "DEFERRED" if transient else "FAILED", exc.smtp_code, str(exc.smtp_error or exc), transient)
        except (OSError, smtplib.SMTPException) as exc:
            return SMTPResult(False, "DEFERRED", response=str(exc), transient=True)
        finally:
            if client:
                try:
                    client.quit()
                except Exception:
                    pass


class ScriptedSMTPTransport:
    def __init__(self, script: Callable[[dict, EmailMessage], SMTPResult] | None = None) -> None:
        self.script = script or self._default_script
        self.sent_messages: list[EmailMessage] = []

    def send(self, profile: dict, message: EmailMessage) -> SMTPResult:
        result = self.script(profile, message)
        if result.success:
            self.sent_messages.append(message)
        return result

    def _default_script(self, _profile: dict, _message: EmailMessage) -> SMTPResult:
        return SMTPResult(True, "SENT", response="scripted-success")
