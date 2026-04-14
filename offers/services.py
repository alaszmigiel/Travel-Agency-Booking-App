from dataclasses import dataclass
from typing import Dict, Any

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404

from .models import Offer

@dataclass
class OfferFilters:
    query: str = ""
    region: str = ""
    people: str = ""
    sort: str = ""

    price_min: str = ""
    price_max: str = ""
    date_from: str = ""
    date_to: str = ""
    promoted: str = ""
    tag: str = ""


class OfferService:
    @staticmethod
    def base_queryset() -> QuerySet:
        return Offer.objects.filter(is_active=True)

    @staticmethod
    def get_top_offers(limit: int = 6) -> QuerySet:
        return Offer.objects.filter(
            is_active=True,
            promoted=True
        ).order_by("-created_at")[:limit]

    @staticmethod
    def get_regions() -> QuerySet:
        return (
            Offer.objects.filter(is_active=True)
            .exclude(region="")
            .values_list("region", flat=True)
            .distinct()
            .order_by("region")
        )

    @staticmethod
    def apply_filters(qs: QuerySet, f: OfferFilters) -> QuerySet:

        if f.tag:
            if f.tag == "narty":
                qs = qs.filter(
                    Q(title__icontains="narty") |
                    Q(description__icontains="narty")
                )
            elif f.tag == "allinclusive":
                qs = qs.filter(
                    Q(title__icontains="all inclusive") |
                    Q(description__icontains="all inclusive") |
                    Q(description__icontains="all-inclusive")
                )
            elif f.tag == "citybreak":
                qs = qs.filter(
                    Q(title__icontains="city break") |
                    Q(description__icontains="city break") |
                    Q(title__icontains="citybreak") |
                    Q(description__icontains="citybreak")
                )
            elif f.tag == "zdziecmi":
                qs = qs.filter(
                    Q(title__icontains="dzieci") |
                    Q(description__icontains="dzieci") |
                    Q(description__icontains="family") |
                    Q(description__icontains="rodzin")
                )

        if f.query:
            q = f.query
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(region__icontains=q) |

                Q(hotel__name__icontains=q) |
                Q(hotel__region__icontains=q) |
                Q(hotel__location__icontains=q) |

                Q(room__name__icontains=q) |
                Q(room__beds_description__icontains=q) |
                Q(room__view_type__icontains=q)
            )

        if f.region:
            qs = qs.filter(region=f.region)

        if f.people and f.people.isdigit():
            qs = qs.filter(available_seats=int(f.people))

        if f.promoted == "1":
            qs = qs.filter(promoted=True)

        if f.price_min:
            try:
                qs = qs.filter(base_price__gte=float(f.price_min))
            except ValueError:
                pass

        if f.price_max:
            try:
                qs = qs.filter(base_price__lte=float(f.price_max))
            except ValueError:
                pass

        if f.date_from:
            qs = qs.filter(start_date__gte=f.date_from)
        if f.date_to:
            qs = qs.filter(end_date__lte=f.date_to)

        if f.sort == "price_asc":
            qs = qs.order_by("base_price")
        elif f.sort == "price_desc":
            qs = qs.order_by("-base_price")
        elif f.sort == "date_asc":
            qs = qs.order_by("start_date")
        elif f.sort == "date_desc":
            qs = qs.order_by("-start_date")

        return qs

    @staticmethod
    def get_offer_details(offer_id: int) -> Offer:
        return get_object_or_404(Offer, id=offer_id, is_active=True)

    @staticmethod
    def show_filters_panel(f: OfferFilters) -> bool:
        return any([
            f.query, f.region, f.people, f.sort,
            f.price_min, f.price_max, f.date_from, f.date_to,
            f.promoted, f.tag,
        ])

    @staticmethod
    def filters_from_request(request) -> OfferFilters:
        return OfferFilters(
            query=(request.GET.get("query") or "").strip(),
            region=(request.GET.get("region") or "").strip(),
            people=(request.GET.get("people") or "").strip(),
            sort=(request.GET.get("sort") or "").strip(),
            price_min=(request.GET.get("price_min") or "").strip(),
            price_max=(request.GET.get("price_max") or "").strip(),
            date_from=(request.GET.get("date_from") or "").strip(),
            date_to=(request.GET.get("date_to") or "").strip(),
            promoted=(request.GET.get("promoted") or "").strip(),
            tag=(request.GET.get("tag") or "").strip().lower(),
        )

    @staticmethod
    def filters_to_context(f: OfferFilters) -> Dict[str, Any]:
        return {
            "query": f.query,
            "region": f.region,
            "people": f.people,
            "sort": f.sort,
            "price_min": f.price_min,
            "price_max": f.price_max,
            "date_from": f.date_from,
            "date_to": f.date_to,
            "promoted": f.promoted,
            "tag": f.tag,
        }