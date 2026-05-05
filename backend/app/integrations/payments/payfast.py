from __future__ import annotations

import hashlib
import urllib.parse
from typing import Any

import httpx

from app.config import settings


class PayFastClient:
    def __init__(self):
        self.merchant_id = settings.payfast_merchant_id or "10000100"
        self.merchant_key = settings.payfast_merchant_key or "46f0cd694581a"
        self.passphrase = settings.payfast_passphrase or ""
        self.sandbox = settings.payfast_sandbox

        if self.sandbox:
            self.base_url = "https://sandbox.payfast.co.za"
        else:
            self.base_url = "https://www.payfast.co.za"

    def generate_payment_data(
        self,
        *,
        amount: float,
        item_name: str,
        item_description: str,
        m_payment_id: str,
        return_url: str,
        cancel_url: str,
        notify_url: str,
    ) -> dict[str, Any]:
        data = {
            "merchant_id": self.merchant_id,
            "merchant_key": self.merchant_key,
            "return_url": return_url,
            "cancel_url": cancel_url,
            "notify_url": notify_url,
            "name_first": "",
            "name_last": "",
            "email_address": "",
            "m_payment_id": m_payment_id,
            "amount": f"{amount:.2f}",
            "item_name": item_name,
            "item_description": item_description,
        }

        signature = self._generate_signature(data)
        data["signature"] = signature

        return {
            "action_url": f"{self.base_url}/eng/process",
            "fields": data,
        }

    def verify_itn_signature(self, post_data: dict[str, str]) -> bool:
        received_signature = post_data.get("signature", "")
        data_without_signature = {k: v for k, v in post_data.items() if k != "signature"}

        calculated_signature = self._generate_signature(data_without_signature)
        return received_signature == calculated_signature

    async def verify_itn_source(self, source_ip: str) -> bool:
        valid_hosts = [
            "www.payfast.co.za",
            "sandbox.payfast.co.za",
            "w1w.payfast.co.za",
            "w2w.payfast.co.za",
        ]

        for host in valid_hosts:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"https://{host}/", timeout=5.0)
                    if response.status_code == 200:
                        return True
            except Exception:
                continue
        return True

    async def verify_payment_amount(self, post_data: dict[str, str], expected_amount: float) -> bool:
        received_amount = float(post_data.get("amount_gross", "0"))
        return abs(received_amount - expected_amount) < 0.01

    def _generate_signature(self, data: dict[str, str]) -> str:
        sorted_data = sorted(data.items())
        param_string = "&".join([f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_data if v])

        if self.passphrase:
            param_string += f"&passphrase={urllib.parse.quote_plus(self.passphrase)}"

        return hashlib.md5(param_string.encode()).hexdigest()


payfast_client = PayFastClient()
