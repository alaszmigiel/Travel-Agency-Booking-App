import uuid
import requests

from django.conf import settings
from django.urls import reverse


class PayUClient:
    def __init__(self):
        self.base = settings.PAYU_BASE_URL

    def get_access_token(self) -> str:
        url = f"{self.base}/pl/standard/user/oauth/authorize"
        data = {
            "grant_type": "client_credentials",
            "client_id": settings.PAYU_CLIENT_ID,
            "client_secret": settings.PAYU_CLIENT_SECRET,
        }
        r = requests.post(url, data=data, timeout=15)
        r.raise_for_status()
        return r.json()["access_token"]

    def create_payu_order(
        self,
        *,
        token: str,
        order,
        request,
        products: list[dict],
        total_amount_grosze: int,
    ) -> dict:
        url = f"{self.base}/api/v2_1/orders"
        ext_order_id = order.ext_order_id or str(uuid.uuid4())

        notify_url = request.build_absolute_uri(reverse("shop:payu_notify"))
        continue_url = request.build_absolute_uri(reverse("shop:payu_return", args=[order.id]))

        payload = {
            "notifyUrl": notify_url,
            "continueUrl": continue_url,
            "customerIp": self._customer_ip(request),
            "merchantPosId": settings.PAYU_POS_ID,
            "description": f"TravelAgency order #{order.id}",
            "currencyCode": "PLN",
            "totalAmount": str(total_amount_grosze),
            "extOrderId": ext_order_id,
            "buyer": {
                "email": request.user.email or "test@example.com",
                "language": "pl",
            },
            "products": products,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        r = requests.post(url, json=payload, headers=headers, timeout=15, allow_redirects=False)
        r.raise_for_status()
        return r.json()

    def retrieve_order(self, *, token: str, payu_order_id: str) -> dict:
        url = f"{self.base}/api/v2_1/orders/{payu_order_id}"
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _customer_ip(request) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR") or "127.0.0.1"