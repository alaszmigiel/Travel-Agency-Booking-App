import json
from typing import Tuple

from orders.models import Order
from shop.payu_client import PayUClient
from shop.payu_signature import verify_notification_signature


class PayUService:
    def __init__(self):
        self.client = PayUClient()

    def start_payment(self, *, order: Order, request) -> Tuple[str, str]:
        token = self.client.get_access_token()

        total_grosze = int(order.final_amount * 100)

        products = []
        for item in order.items.all():
            products.append({
                "name": item.offer.title,
                "unitPrice": str(int(item.price_per_person * 100)),
                "quantity": str(item.participants),
            })

        resp = self.client.create_payu_order(
            token=token,
            order=order,
            request=request,
            products=products,
            total_amount_grosze=total_grosze,
        )

        payu_order_id = resp.get("orderId", "") or ""
        redirect_uri = resp.get("redirectUri", "") or ""
        return payu_order_id, redirect_uri

    def refresh_payment_status(self, *, order: Order) -> str:
        if order.payment_status in ("paid", "failed", "canceled"):
            return order.payment_status

        if not order.payu_order_id:
            order.payment_status = "failed"
            order.save(update_fields=["payment_status"])
            return "failed"

        try:
            token = self.client.get_access_token()
            payu_resp = self.client.retrieve_order(token=token, payu_order_id=order.payu_order_id)
        except Exception:
            return "pending"

        if isinstance(payu_resp.get("orders"), list) and payu_resp["orders"]:
            payu_order = payu_resp["orders"][0]
        else:
            payu_order = payu_resp.get("order", {}) or {}

        payu_status = (payu_order.get("status") or "").upper()

        if payu_status == "COMPLETED":
            order.payment_status = "paid"
        elif payu_status == "CANCELED":
            order.payment_status = "canceled"
        elif payu_status in ("PENDING", "WAITING_FOR_CONFIRMATION", "NEW"):
            order.payment_status = "pending"
        else:
            order.payment_status = "failed"

        order.save(update_fields=["payment_status"])
        return order.payment_status

    @staticmethod
    def handle_notification(*, raw_body: bytes, signature_header: str) -> None:

        if not verify_notification_signature(raw_body, signature_header):
            return

        data = json.loads(raw_body.decode("utf-8"))
        order_data = data.get("order", {}) or {}
        payu_order_id = order_data.get("orderId")
        status = (order_data.get("status") or "").upper()

        if not payu_order_id:
            return

        try:
            order = Order.objects.get(payu_order_id=payu_order_id)
        except Order.DoesNotExist:
            return

        if status == "COMPLETED":
            order.payment_status = "paid"
        elif status == "CANCELED":
            order.payment_status = "canceled"
        elif status in ("PENDING", "WAITING_FOR_CONFIRMATION", "NEW"):
            order.payment_status = "pending"
        else:
            order.payment_status = "failed"

        order.save(update_fields=["payment_status"])