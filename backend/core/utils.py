from django.conf import settings


def get_client_ip(request) -> str:
    """
    The real client IP, for rate-limiting and audit-logging purposes.

    X-Forwarded-For is normally set by a trusted reverse proxy to carry the
    real client IP through to the app — but it's also just a plain HTTP
    header, which means anyone can set it directly on their own request
    unless a proxy in front of Django is specifically configured to
    strip/overwrite any client-supplied value before forwarding. Trusting
    it unconditionally means an attacker can bypass IP-based rate limiting
    entirely just by rotating this header on every request, and can poison
    the login-attempt audit log with fake IPs — both confirmed exploitable
    in security testing.

    Defaults to REMOTE_ADDR (the actual TCP connection IP, which a client
    cannot spoof at the HTTP layer) unless TRUST_PROXY_HEADERS is
    explicitly enabled in settings — turn that on only once you've
    confirmed your production reverse proxy actually overwrites
    X-Forwarded-For rather than passing through whatever the client sent.
    """
    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")