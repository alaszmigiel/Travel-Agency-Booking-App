from decimal import Decimal

from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from offers.models import Offer
from orders.models import Order

from shop.cart_service import CartService
from shop.checkout_service import CheckoutService
from shop.payu_service import PayUService
from django.contrib.auth.decorators import login_required

def cart_detail(request):
    cart = CartService()

    if request.user.is_authenticated:
        items = cart.build_items(user=request.user)
        total = cart.calculate_total(user=request.user)
    else:
        offers = cart.session_get_offers(request)
        items = []
        total = Decimal("0.00")
        for o in offers:
            people = int(o.available_seats or 0)
            line_total = o.base_price * people
            items.append({
                "offer": o,
                "people": people,
                "price_per_person": o.base_price,
                "line_total": line_total,
            })
            total += line_total

    return render(request, "shop/cart_detail.html", {"items": items, "total": total})


def add_to_cart(request, offer_id: int):
    offer = get_object_or_404(Offer, id=offer_id, is_active=True)
    cart = CartService()

    if request.user.is_authenticated:
        added, _ = cart.add_offer(user=request.user, offer=offer)
    else:
        added = cart.session_add_offer_id(request, offer_id)

    if not added:
        messages.info(request, "Ta oferta jest już w Twoim koszyku.")
    else:
        request.session["show_cart_popup"] = True

    return redirect(request.META.get("HTTP_REFERER", reverse("offers:list")))


def remove_from_cart(request, offer_id: int):
    if request.method == "POST":
        cart = CartService()

        if request.user.is_authenticated:
            cart.remove_offer(user=request.user, offer_id=offer_id)
        else:
            cart.session_remove_offer_id(request, offer_id)

        cart.clear_offer_checkout_data(request, offer_id)

    return redirect("shop:cart_detail")


def clear_cart(request):
    if request.method == "POST":
        cart = CartService()

        if request.user.is_authenticated:
            cart.clear(user=request.user)
        else:
            cart.session_clear(request)

        request.session.pop("participants", None)
        request.session.pop("reservations", None)
        request.session.pop("personalization_choices", None)
        request.session.modified = True

    return redirect("shop:cart_detail")

@login_required
def checkout_start(request):
    cart = CartService()

    session_offers = cart.session_get_offers(request)
    session_ids = {o.id for o in session_offers}

    db_items_before = cart.get_items(user=request.user)
    db_extra_offer_ids = [ci.offer_id for ci in db_items_before
                          if ci.offer_id not in session_ids]

    if not db_items_before and not session_offers:
        return redirect("shop:cart_detail")

    if session_offers:
        cart.merge_session_into_db(request, user=request.user)

    if (session_offers and db_extra_offer_ids
            and not request.session.get("merge_decided")):
        request.session["merge_extra_offer_ids"] = (
            db_extra_offer_ids)
        request.session.modified = True
        return redirect("shop:merge_cart")

    request.session["checkout_step"] = 0
    request.session.modified = True
    return redirect("shop:checkout_personalization", step=0)


@login_required
def checkout_personalization(request, step: int):
    cart = CartService()
    items = cart.get_items(user=request.user)

    total_steps = len(items)
    if total_steps == 0:
        return redirect("shop:cart_detail")
    if step < 0 or step >= total_steps:
        return redirect("shop:checkout_personalization", step=0)

    ci = items[step]
    offer = ci.offer
    total_price = ci.line_total

    if request.method == "POST":
        choice = request.POST.get("personalization", "none")
        choices = request.session.get("personalization_choices", {})
        choices[str(offer.id)] = choice
        request.session["personalization_choices"] = choices
        request.session.modified = True

        if step + 1 < total_steps:
            return redirect("shop:checkout_personalization", step=step + 1)
        return redirect("shop:checkout_reservation", step=0)

    existing_choice = request.session.get("personalization_choices", {}).get(str(offer.id), "none")

    return render(request, "shop/checkout_personalization.html", {
        "offer": offer,
        "step": step,
        "total_steps": total_steps,
        "existing_choice": existing_choice,
        "total_price": total_price,
    })


@login_required
def checkout_reservation(request, step: int):
    cart = CartService()
    items = cart.get_items(user=request.user)

    total_steps = len(items)
    if total_steps == 0:
        return redirect("shop:cart_detail")
    if step < 0 or step >= total_steps:
        return redirect("shop:checkout_reservation", step=0)

    ci = items[step]
    offer = ci.offer
    total_price = ci.line_total

    profile = getattr(request.user, "profile", None)
    initial = {
        "full_name": f"{profile.first_name} {profile.last_name}".strip() if profile else "",
        "email": request.user.email or "",
        "phone": getattr(profile, "phone", "") if profile else "",
        "notes": "",
    }

    errors = {}
    existing = None

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        notes = request.POST.get("notes", "").strip()

        if not full_name:
            errors["full_name"] = "Imię i nazwisko jest wymagane"
        if not email:
            errors["email"] = "Email jest wymagany"
        if not phone:
            errors["phone"] = "Telefon jest wymagany"

        if not errors:
            reservations = request.session.get("reservations", {})
            reservations[str(offer.id)] = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "notes": notes,
            }
            request.session["reservations"] = reservations
            request.session.modified = True

            if step + 1 < total_steps:
                return redirect("shop:checkout_reservation",
                                step=step + 1)
            return redirect("shop:checkout_participants", step=0)

        existing = {"full_name": full_name, "email": email, "phone": phone, "notes": notes}

    return render(request, "shop/checkout_reservation.html", {
        "offer": offer,
        "step": step,
        "total_steps": total_steps,
        "initial": initial,
        "existing": existing,
        "errors": errors,
        "total_price": total_price,
    })


@login_required
def checkout_participants(request, step: int):
    cart = CartService()
    items = cart.get_items(user=request.user)

    total_steps = len(items)
    if total_steps == 0:
        return redirect("shop:cart_detail")
    if step < 0 or step >= total_steps:
        return redirect("shop:checkout_reservation", step=0)

    ci = items[step]
    offer = ci.offer
    count = ci.participants
    total_price = ci.line_total

    saved = request.session.get("participants", {}).get(str(offer.id), [])

    data_list = []
    for i in range(count):
        base = {"first_name": "", "last_name": "", "birth_date": "", "document_type": "id", "document_number": ""}
        if i < len(saved):
            base.update(saved[i] or {})
        data_list.append(base)

    errors_list = [dict() for _ in range(count)]

    if request.method == "POST":
        has_errors = False

        for i in range(count):
            fn = (request.POST.get(f"first_name_{i}") or "").strip()
            ln = (request.POST.get(f"last_name_{i}") or "").strip()
            bd = (request.POST.get(f"birth_date_{i}") or "").strip()
            dt = (request.POST.get(f"document_type_{i}") or "id").strip()
            dn = (request.POST.get(f"document_number_{i}") or "").strip()

            data_list[i] = {
                "first_name": fn,
                "last_name": ln,
                "birth_date": bd,
                "document_type": dt,
                "document_number": dn,
            }

            if not fn:
                errors_list[i]["first_name"] = "Podaj imię."
                has_errors = True
            if not ln:
                errors_list[i]["last_name"] = "Podaj nazwisko."
                has_errors = True
            if not bd:
                errors_list[i]["birth_date"] = "Podaj datę urodzenia."
                has_errors = True
            if not dn:
                errors_list[i]["document_number"] = "Podaj numer dokumentu."
                has_errors = True

        if has_errors:
            messages.error(request, "Uzupełnij brakujące dane uczestników.")
        else:
            participants_session = request.session.get("participants", {})
            participants_session[str(offer.id)] = data_list
            request.session["participants"] = participants_session
            request.session.modified = True

            if step + 1 < total_steps:
                return redirect("shop:checkout_participants", step=step + 1)
            return redirect("shop:checkout_summary")

    participants = list(zip(data_list, errors_list))
    return render(request, "shop/checkout_participants.html", {
        "offer": offer,
        "count": count,
        "participants": participants,
        "step": step,
        "total_steps": total_steps,
        "total_price": total_price,
    })


@login_required
def checkout_summary(request):
    cart = CartService()
    items_db = cart.get_items(user=request.user)
    if not items_db:
        return redirect("shop:cart_detail")

    reservations = request.session.get("reservations", {})
    participants_map = request.session.get("participants", {})

    total = cart.calculate_total(user=request.user)

    items = []
    for ci in items_db:
        offer = ci.offer
        items.append({
            "offer": offer,
            "people": ci.participants,
            "rd": reservations.get(str(offer.id)),
            "participants": participants_map.get(str(offer.id), []),
            "line_total": ci.line_total,
        })

    return render(request, "shop/checkout_summary.html", {
        "items": items,
        "total": total,
    })


@login_required
def checkout_pay(request):
    if request.method != "POST":
        return redirect("shop:checkout_summary")

    cart = CartService()
    if not cart.get_items(user=request.user):
        return redirect("shop:cart_detail")

    checkout = CheckoutService()
    payu = PayUService()

    order = checkout.create_order_from_cart(user=request.user)

    try:
        payu_order_id, redirect_uri = payu.start_payment(
            order=order, request=request)
    except Exception:
        order.payment_status = "failed"
        order.save(update_fields=["payment_status"])
        messages.error(request, "Nie udało się rozpocząć płatności. Spróbuj ponownie.")
        return redirect("shop:checkout_summary")

    if not payu_order_id or not redirect_uri:
        order.payment_status = "failed"
        order.save(update_fields=["payment_status"])
        messages.error(request, "Nie udało się rozpocząć płatności. Spróbuj ponownie.")
        return redirect("shop:checkout_summary")

    order.payu_order_id = payu_order_id
    order.save(update_fields=["payu_order_id"])

    checkout.clear_checkout_session(request)

    return redirect(redirect_uri)


@login_required
def checkout_confirmation(request, order_id: int):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "shop/checkout_confirmation.html", {"order": order})


@login_required
def payu_return(request, order_id: int):
    return redirect("shop:checkout_confirmation", order_id=order_id)


@login_required
def order_status(request, order_id: int):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payu = PayUService()

    status = payu.refresh_payment_status(order=order)
    return JsonResponse({
        "status": status,
        "label": order.get_payment_status_display(),
    })


@csrf_exempt
def payu_notify(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST")

    payu = PayUService()
    payu.handle_notification(
        raw_body=request.body,
        signature_header=request.headers.get("OpenPayu-Signature",
                                             ""),
    )
    return HttpResponse(status=200)


@login_required
def merge_cart(request):
    cart = CartService()

    extra_ids = request.session.get("merge_extra_offer_ids") or []
    if not extra_ids:
        request.session["merge_decided"] = True
        request.session.modified = True
        return redirect("shop:checkout_start")

    extra_offers = list(Offer.objects.filter(id__in=extra_ids, is_active=True))

    if request.method == "POST":
        decision = request.POST.get("decision")

        if decision == "discard":
            cart.remove_offer_ids(user=request.user, offer_ids=extra_ids)


        request.session["merge_decided"] = True
        request.session.pop("merge_extra_offer_ids", None)
        request.session.modified = True
        return redirect("shop:checkout_start")

    return render(request, "shop/merge_cart.html", {
        "extra_offers": extra_offers,
    })