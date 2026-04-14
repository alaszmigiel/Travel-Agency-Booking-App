import hashlib
from django.conf import settings

def extract_signature(header_value: str) -> str:
    if not header_value:
        return ""
    parts = [p.strip() for p in header_value.split(";") if p.strip()]
    kv = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            kv[k.strip().lower()] = v.strip()
    return kv.get("signature", "")


def verify_notification_signature(raw_body: bytes, signature_header: str) -> bool:
    incoming = extract_signature(signature_header)
    if not incoming:
        return False
    expected = hashlib.md5(raw_body + settings.PAYU_SECOND_KEY.encode("utf-8")).hexdigest()
    return expected == incoming
