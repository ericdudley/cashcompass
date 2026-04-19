import math
from datetime import date, datetime, timezone, timedelta


def preset_to_dates(preset: str) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    year, month = now.year, now.month

    if preset == "this_month":
        first = date(year, month, 1)
        if month == 12:
            next_month_first = date(year + 1, 1, 1)
        else:
            next_month_first = date(year, month + 1, 1)
        last = next_month_first - timedelta(days=1)
        return first.strftime("%Y_%m_%d"), last.strftime("%Y_%m_%d")

    if preset == "last_month":
        if month == 1:
            first = date(year - 1, 12, 1)
            this_month_first = date(year, 1, 1)
        else:
            first = date(year, month - 1, 1)
            this_month_first = date(year, month, 1)
        last = this_month_first - timedelta(days=1)
        return first.strftime("%Y_%m_%d"), last.strftime("%Y_%m_%d")

    if preset == "this_year":
        return date(year, 1, 1).strftime("%Y_%m_%d"), date(year, 12, 31).strftime("%Y_%m_%d")

    return "", ""


def iso_to_display(d: str) -> str:
    try:
        t = datetime.strptime(d[:10], "%Y-%m-%d")
        return t.strftime("%b %d, %Y")
    except Exception:
        return d


def fmt_date(yyyy_mm_dd: str) -> str:
    s = yyyy_mm_dd.replace("_", "-")[:10]
    try:
        t = datetime.strptime(s, "%Y-%m-%d")
        return t.strftime("%b %d, %Y")
    except Exception:
        return yyyy_mm_dd


def parse_date(s: str, timezone_str: str = "") -> tuple[str, str]:
    s = s.strip()
    if len(s) < 10:
        raise ValueError(f"invalid date: {s!r}")

    if len(s) == 10:
        datetime.strptime(s, "%Y-%m-%d")
        return s, s.replace("-", "_")

    # Full timestamp
    import pytz
    for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"]:
        try:
            t = datetime.strptime(s, fmt)
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"invalid date: {s!r}")

    if timezone_str:
        try:
            import pytz
            loc = pytz.timezone(timezone_str)
            if t.tzinfo is None:
                t = pytz.utc.localize(t)
            t = t.astimezone(loc)
        except Exception:
            pass

    date_part = t.strftime("%Y-%m-%d")
    return date_part, date_part.replace("-", "_")
