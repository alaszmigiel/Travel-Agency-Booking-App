from django.urls import path
from . import views

app_name = "shop"

urlpatterns = [
    path("cart/", views.cart_detail, name="cart_detail"),
    path("add/<int:offer_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove/<int:offer_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("clear/", views.clear_cart, name="clear_cart"),
    path("checkout/", views.checkout_start, name="checkout_start"),
    path("checkout/personalization/<int:step>/", views.checkout_personalization, name="checkout_personalization"),
    path("checkout/reservation/<int:step>/", views.checkout_reservation, name="checkout_reservation"),
    path("checkout/participants/<int:step>/", views.checkout_participants, name="checkout_participants"),
    path("checkout/summary/", views.checkout_summary, name="checkout_summary"),
    path("checkout/pay/", views.checkout_pay, name="checkout_pay"),
    path("checkout/confirmation/<int:order_id>/", views.checkout_confirmation, name="checkout_confirmation"),
    path("order-status/<int:order_id>/", views.order_status, name="order_status"),
    path("payu/notify/", views.payu_notify, name="payu_notify"),
    path("payu/return/<int:order_id>/", views.payu_return, name="payu_return"),
    path("checkout/merge/", views.merge_cart, name="merge_cart"),
]