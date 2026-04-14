from django.urls import path
from .views import OfferListView, OfferDetailView

app_name = "offers"

urlpatterns = [
    path("", OfferListView.as_view(), name="list"),
    path("<int:offer_id>/", OfferDetailView.as_view(), name="detail"),
]
