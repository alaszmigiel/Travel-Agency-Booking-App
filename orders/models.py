from django.db import models
from django.contrib.auth.models import User
from offers.models import Offer, Hotel, Room, Flight
from django.conf import settings

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    offer = models.ForeignKey(Offer, on_delete=models.PROTECT, related_name="cart_items")

    participants = models.PositiveIntegerField(default=1)
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "offer")

class Order(models.Model):
    PAYMENT_STATUS = [
        ("paid", "Opłacone"),
        ("pending", "Oczekuje na płatność"),
        ("failed", "Nieudana"),
        ("canceled", "Anulowana"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="pending")

    payu_order_id = models.CharField(max_length=64, blank=True, default="")
    ext_order_id = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    offer = models.ForeignKey(Offer, on_delete=models.PROTECT)
    participants = models.PositiveIntegerField()
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

class ReservationData(models.Model):
    order_item = models.OneToOneField(
        "OrderItem",
        related_name="reservation_data",
        on_delete=models.CASCADE
    )

    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"ReservationData for item {self.order_item_id}"

class Participant(models.Model):
    DOC_TYPE_CHOICES = [
        ("id", "Dowód osobisty"),
        ("passport", "Paszport"),
    ]

    order_item = models.ForeignKey(
        OrderItem,
        related_name="participants_data",
        on_delete=models.CASCADE
    )

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()

    document_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default="id")
    document_number = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (item {self.order_item_id})"
