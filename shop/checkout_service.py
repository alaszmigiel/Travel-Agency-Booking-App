from orders.models import Order, OrderItem
from shop.cart_service import CartService


class CheckoutService:
    @staticmethod
    def create_order_from_cart(*, user) -> Order:
        cart = CartService()
        items = cart.get_items(user=user)
        total = cart.calculate_total(user=user)

        order = Order.objects.create(
            user=user,
            final_amount=total,
            payment_status="pending",
        )
        order.ext_order_id = f"TA-{order.id}"
        order.save(update_fields=["ext_order_id"])

        for ci in items:
            OrderItem.objects.create(
                order=order,
                offer=ci.offer,
                participants=ci.participants,
                price_per_person=ci.price_per_person,
                line_total=ci.line_total,
            )

        return order

    @staticmethod
    def clear_checkout_session(request) -> None:
        CartService().clear(user=request.user)

        request.session.pop("reservations", None)
        request.session.pop("participants", None)
        request.session.pop("personalization_choices", None)
        request.session.modified = True