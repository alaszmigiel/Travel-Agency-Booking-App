from __future__ import annotations
from decimal import Decimal
from typing import List, Tuple
from django.db import transaction
from offers.models import Offer
from orders.models import Cart, CartItem

class CartService:

    SESSION_KEY = "cart"

    def session_get_offer_ids(self, request) -> list[int]:
        ids = request.session.get(self.SESSION_KEY, [])
        if not isinstance(ids, list):
            return []
        out: list[int] = []
        for x in ids:
            try:
                out.append(int(x))
            except Exception:
                continue
        return out

    def session_get_offers(self, request) -> list[Offer]:
        ids = self.session_get_offer_ids(request)
        if not ids:
            return []
        offers = Offer.objects.filter(id__in=ids, is_active=True)
        by_id = {o.id: o for o in offers}
        return [by_id[i] for i in ids if i in by_id]

    def session_add_offer_id(self, request, offer_id: int) -> bool:
        ids = self.session_get_offer_ids(request)
        if offer_id in ids:
            return False
        ids.append(offer_id)
        request.session[self.SESSION_KEY] = ids
        request.session.modified = True
        return True

    def session_remove_offer_id(self, request, offer_id: int) -> None:
        ids = self.session_get_offer_ids(request)
        request.session[self.SESSION_KEY] = [i for i in ids if i != offer_id]
        request.session.modified = True

    @transaction.atomic
    def remove_offer_ids(self, *, user, offer_ids: list[int]) -> None:
        cart = self.get_or_create_cart(user=user)
        cart.items.filter(offer_id__in=offer_ids).delete()

    def session_clear(self, request) -> None:
        request.session[self.SESSION_KEY] = []
        request.session.modified = True

    @staticmethod
    def get_or_create_cart(*, user) -> Cart:
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    def get_items(self, *, user) -> List[CartItem]:
        cart = self.get_or_create_cart(user=user)
        return list(cart.items.select_related("offer").order_by("added_at", "id"))

    def has_items(self, *, user) -> bool:
        cart = self.get_or_create_cart(user=user)
        return cart.items.exists()

    @transaction.atomic
    def add_offer(self, *, user, offer: Offer) -> Tuple[bool, CartItem]:

        cart = self.get_or_create_cart(user=user)

        existing = (CartItem.objects.select_for_update()
                    .filter(cart=cart, offer=offer).first()
        )
        if existing:
            return False, existing

        participants = int(offer.available_seats or 0)
        price = offer.base_price
        line_total = price * participants

        item = CartItem.objects.create(
            cart=cart,
            offer=offer,
            participants=participants,
            price_per_person=price,
            line_total=line_total,
        )
        return True, item

    @transaction.atomic
    def remove_offer(self, *, user, offer_id: int) -> None:
        cart = self.get_or_create_cart(user=user)
        CartItem.objects.filter(cart=cart, offer_id=offer_id).delete()

    @transaction.atomic
    def clear(self, *, user) -> None:
        cart = self.get_or_create_cart(user=user)
        cart.items.all().delete()

    def calculate_total(self, *, user) -> Decimal:
        total = Decimal("0.00")
        for item in self.get_items(user=user):
            total += item.line_total
        return total

    def build_items(self, *, user) -> List[dict]:

        out: list[dict] = []
        for item in self.get_items(user=user):
            out.append({
                "offer": item.offer,
                "people": item.participants,
                "price_per_person": item.price_per_person,
                "line_total": item.line_total,
            })
        return out

    @staticmethod
    def clear_offer_checkout_data(request, offer_id: int) -> None:

        key = str(offer_id)

        participants = request.session.get("participants", {})
        if isinstance(participants, dict):
            participants.pop(key, None)
            request.session["participants"] = participants

        reservations = request.session.get("reservations", {})
        if isinstance(reservations, dict):
            reservations.pop(key, None)
            request.session["reservations"] = reservations

        choices = request.session.get("personalization_choices", {})
        if isinstance(choices, dict):
            choices.pop(key, None)
            request.session["personalization_choices"] = choices

        request.session.modified = True


    @transaction.atomic
    def merge_session_into_db(self, request, *, user) -> dict:

        offers = self.session_get_offers(request)
        added = 0
        skipped = 0

        for offer in offers:
            ok, _ = self.add_offer(user=user, offer=offer)
            if ok:
                added += 1
            else:
                skipped += 1

        self.session_clear(request)
        return {"added": added, "skipped": skipped}