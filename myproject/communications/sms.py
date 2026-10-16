from abc import ABC, abstractmethod
import json
from urllib import parse, request
from urllib.error import HTTPError, URLError

from django.conf import settings


class BaseSMSProvider(ABC):
    """قرارداد همه Providerهای پیامک."""

    @abstractmethod
    def send(self, phone: str, message: str):
        raise NotImplementedError


class ConsoleSMSProvider(BaseSMSProvider):
    provider_name = "console"

    def send(self, phone: str, message: str):
        print("=" * 50)
        print("SMS PROVIDER: CONSOLE")
        print(f"TO: {phone}")
        print(f"MESSAGE: {message}")
        print("=" * 50)

        return {
            "success": True,
            "provider": self.provider_name,
            "message_id": None,
            "status": "console",
            "error": None,
        }


class KavenegarProvider(BaseSMSProvider):
    provider_name = "kavenegar"
    timeout = 15

    def __init__(self):
        self.api_key = getattr(settings, "KAVENEGAR_API_KEY", "")
        self.sender = getattr(settings, "KAVENEGAR_SENDER", "")

    def send(self, phone: str, message: str):
        if not self.api_key:
            return {
                "success": False,
                "provider": self.provider_name,
                "message_id": None,
                "status": "configuration_error",
                "error": "KAVENEGAR_API_KEY تنظیم نشده است.",
            }

        endpoint = (
            f"https://api.kavenegar.com/v1/"
            f"{self.api_key}/sms/send.json"
        )
        payload = {
            "receptor": phone,
            "message": message,
        }
        if self.sender:
            payload["sender"] = self.sender

        encoded = parse.urlencode(payload).encode("utf-8")
        http_request = request.Request(
            endpoint,
            data=encoded,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)
        except HTTPError as exc:
            return {
                "success": False,
                "provider": self.provider_name,
                "message_id": None,
                "status": f"http_{exc.code}",
                "error": str(exc),
            }
        except (URLError, TimeoutError, ValueError) as exc:
            return {
                "success": False,
                "provider": self.provider_name,
                "message_id": None,
                "status": "connection_error",
                "error": str(exc),
            }

        status = (data.get("return") or {}).get("status")
        message_text = (data.get("return") or {}).get("message", "")
        entries = data.get("entries") or []
        entry = entries[0] if entries else {}

        success = str(status) == "200"
        return {
            "success": success,
            "provider": self.provider_name,
            "message_id": str(entry.get("messageid", "")) or None,
            "status": str(status or "unknown"),
            "error": "" if success else message_text or "ارسال پیامک ناموفق بود.",
        }


class SMSFactory:
    providers = {
        "console": ConsoleSMSProvider,
        "kavenegar": KavenegarProvider,
    }

    @classmethod
    def get_provider(cls):
        provider_name = getattr(
            settings,
            "SMS_PROVIDER",
            "console",
        )

        provider_class = cls.providers.get(
            provider_name,
            ConsoleSMSProvider,
        )

        return provider_class()
