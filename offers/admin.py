from django.contrib import admin
from django import forms

from .models import Offer, Hotel, Room, Flight, MEAL_CHOICES

class HotelAdminForm(forms.ModelForm):
    available_meals_ui = forms.MultipleChoiceField(
        choices=MEAL_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Dostępne wyżywienia"
    )

    class Meta:
        model = Hotel
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["available_meals_ui"].initial = self.instance.available_meals or []

    def clean(self):
        cleaned = super().clean()
        cleaned["available_meals"] = cleaned.get("available_meals_ui", [])
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.available_meals = self.cleaned_data.get("available_meals_ui", [])
        if commit:
            obj.save()
        return obj


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    form = HotelAdminForm
    list_display = ("name", "region", "standard", "location")
    list_filter = ("region", "standard")
    search_fields = ("name", "region", "location")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "name", "hotel", "max_occupancy", "size_m2", "price_per_night",
        "has_kitchen", "has_balcony", "has_air_conditioning", "has_wifi",
    )
    list_filter = (
        "hotel", "max_occupancy", "has_kitchen", "has_balcony",
        "has_air_conditioning", "has_wifi",
    )
    search_fields = ("name", "hotel__name", "beds_description")
    ordering = ("hotel__name", "price_per_night")


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        "flight_number", "carrier", "departure_airport", "arrival_airport",
        "departure_time", "arrival_time", "region", "price_per_person",
    )
    list_filter = ("carrier", "region", "departure_airport", "arrival_airport")
    search_fields = ("flight_number", "carrier", "departure_airport", "arrival_airport")
    ordering = ("-departure_time",)


class OfferAdminForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        hotel = None

        if self.instance and self.instance.pk and self.instance.hotel_id:
            hotel = self.instance.hotel

        if "hotel" in self.data and self.data.get("hotel"):
            try:
                hotel = Hotel.objects.get(pk=self.data.get("hotel"))
            except Hotel.DoesNotExist:
                hotel = None

        if hotel:
            allowed = set(hotel.available_meals or [])
            self.fields["meal_plan"].choices = [("", "---------")] + [
                (code, label) for code, label in MEAL_CHOICES if code in allowed
            ]
        else:
            self.fields["meal_plan"].choices = [("", "---------")]

        if "room" in self.fields:
            if hotel:
                self.fields["room"].queryset = Room.objects.filter(hotel=hotel).order_by("name")
            else:
                self.fields["room"].queryset = Room.objects.none()


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    form = OfferAdminForm
    list_display = ("title", "hotel", "room", "meal_plan", "start_date", "end_date", "base_price", "promoted", "is_active")
    list_filter = ("promoted", "is_active", "region", "meal_plan")
    search_fields = ("title", "region", "description")

