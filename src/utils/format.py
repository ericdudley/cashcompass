import math


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


def cents_input(cents: int) -> str:
    abs_cents = abs(cents)
    dollars = abs_cents // 100
    c = abs_cents % 100
    return f"{dollars}.{c:02d}"


def parse_cents(s: str) -> int:
    s = s.replace("$", "").replace(",", "").strip()
    f = float(s)
    return int(math.floor(f * 100 + 0.5))
