try:
    import whois
except ImportError:  # pragma: no cover
    whois = None


class WhoisService:
    def has_valid_domain(self, domain: str) -> bool:
        if whois is None or not domain:
            return False
        try:
            result = whois.whois(domain)
        except Exception:
            return False
        return bool(getattr(result, "domain_name", None))
