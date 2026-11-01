from decimal import Decimal, DecimalException, ROUND_HALF_UP, localcontext


SQLITE_MIN_INT = -(2**63)
SQLITE_MAX_INT = 2**63 - 1


def validate_cents(cents: int) -> int:
    if isinstance(cents, bool) or not isinstance(cents, int) or not SQLITE_MIN_INT <= cents <= SQLITE_MAX_INT:
        raise ValueError("amount is outside the supported range")
    return cents


def cents_abs(cents: int) -> str:
    abs_cents = abs(cents)
    dollars = abs_cents // 100
    c = abs_cents % 100
    return f"${dollars:,}.{c:02d}"


def cents_dollars(cents: int) -> str:
    if cents < 0:
        return f"-{cents_abs(cents)}"
    return cents_abs(cents)


def cents_display(cents: int) -> str:
    if cents >= 0:
        return f"+{cents_abs(cents)}"
    return f"-{cents_abs(cents)}"


def cents_diff(cents: int) -> str:
    if cents > 0:
        return f"+{cents_abs(cents)}"
    if cents < 0:
        return f"-{cents_abs(cents)}"
    return cents_abs(cents)


def cents_input(cents: int) -> str:
    abs_cents = abs(cents)
    dollars = abs_cents // 100
    c = abs_cents % 100
    return f"{dollars}.{c:02d}"


def parse_cents(s: str) -> int:
    try:
        amount = Decimal(s.replace("$", "").replace(",", "").strip())
        if not amount.is_finite() or abs(amount) > Decimal(2**63) / 100:
            raise ValueError("amount must be a finite number within the supported range")
        with localcontext() as context:
            context.prec = 40
            cents = int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return validate_cents(cents)
    except (DecimalException, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError("amount must be a valid number within the supported range") from exc
