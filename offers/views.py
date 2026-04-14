from decimal import Decimal

from django.shortcuts import render
from django.views import View

from .services import OfferService

class OfferListView(View):
    service = OfferService()

    def get(self, request):
        filters = self.service.filters_from_request(request)
        qs = self.service.base_queryset()
        qs = self.service.apply_filters(qs, filters)
        regions = self.service.get_regions()
        show_filters = self.service.show_filters_panel(filters)
        top_offers = self.service.get_top_offers(limit=6)

        context = {
            "offers": qs,
            "top_offers": top_offers,
            "regions": regions,
            "show_filters": show_filters,
            "show_results": show_filters,

            **self.service.filters_to_context(filters),
        }

        return render(request, "offers/offer_list.html", context)


class OfferDetailView(View):
    service = OfferService()

    def get(self, request, offer_id: int):
        offer = self.service.get_offer_details(offer_id)
        show_cart_popup = request.session.pop("show_cart_popup", False)

        total_price = (offer.base_price or Decimal("0")) * Decimal(offer.available_seats or 0)
        back_url = request.META.get("HTTP_REFERER")

        return render(request, "offers/offer_detail.html", {
            "offer": offer,
            "back_url": back_url,
            "show_cart_popup": show_cart_popup,
            "total_price": total_price,
        })
