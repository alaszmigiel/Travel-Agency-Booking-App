from django.db import models
from django.core.exceptions import ValidationError

MEAL_CHOICES = [
    ("RO", "Room only (bez wyżywienia)"),
    ("BB", "BB (śniadania)"),
    ("HB", "HB (śniadania i obiadokolacje)"),
    ("FB", "FB (3 posiłki)"),
    ("AI", "All inclusive"),
]

class Hotel(models.Model):
    name = models.CharField(max_length=120)
    region = models.CharField(max_length=100)
    standard = models.PositiveSmallIntegerField(default=3)
    location = models.CharField(max_length=120, blank=True)

    available_meals = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.name} ({self.region})"


class Room(models.Model):
    hotel = models.ForeignKey(Hotel, related_name="rooms", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)

    max_occupancy = models.PositiveSmallIntegerField(default=2)
    size_m2 = models.PositiveSmallIntegerField(default=20)

    beds_description = models.CharField(max_length=120, blank=True,
    )

    has_kitchen = models.BooleanField(default=False)
    has_balcony = models.BooleanField(default=False)
    has_air_conditioning = models.BooleanField(default=True)
    has_wifi = models.BooleanField(default=True)

    view_type = models.CharField(max_length=50, blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.hotel.name} – {self.name} ({self.max_occupancy} os.)"


class Flight(models.Model):
    flight_number = models.CharField(max_length=30)
    carrier = models.CharField(max_length=80)

    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    departure_airport = models.CharField(max_length=80)
    arrival_airport = models.CharField(max_length=80)

    region = models.CharField(max_length=100, blank=True)
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.flight_number}: {self.departure_airport} → {self.arrival_airport}"


class Offer(models.Model):
    title = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    base_price = models.DecimalField(max_digits=10,
                                     decimal_places=2)
    available_seats = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    image = models.ImageField(upload_to="offers/", null=True, blank=True)

    is_active = models.BooleanField(default=True)
    promoted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    hotel = models.ForeignKey(Hotel, null=True, blank=True,
                              on_delete=models.SET_NULL,
                              related_name="offers")
    room = models.ForeignKey(Room, null=True, blank=True,
                             on_delete=models.SET_NULL,
                             related_name="offers")
    outbound_flight = models.ForeignKey(Flight, null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL,
                                        related_name="offers_out")

    return_flight = models.ForeignKey(Flight, on_delete=models.SET_NULL, null=True, blank=True, related_name="offers_return")
    meal_plan = models.CharField( max_length=2, choices=MEAL_CHOICES, blank=True, default="")

    def clean(self):
        super().clean()
        if self.hotel and self.meal_plan:
            allowed = set(self.hotel.available_meals or [])
            if self.meal_plan not in allowed:
                raise ValidationError({"meal_plan": "To wyżywienie nie jest dostępne dla wybranego hotelu."})

        if self.hotel and self.room and self.room.hotel_id != self.hotel_id:
            raise ValidationError({"room": "Wybrany pokój nie należy do wybranego hotelu."})

    def __str__(self):
        return self.title
