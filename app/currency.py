from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def format_inr(value: float | int | Decimal | None) -> str:
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return "₹0"

    if not amount.is_finite():
        return "₹0"

    is_negative = amount < 0
    amount = abs(amount)
    integer_part = str(int(amount))

    if len(integer_part) > 3:
        grouped = integer_part[-3:]
        remaining = integer_part[:-3]
        while remaining:
            grouped = remaining[-2:] + "," + grouped
            remaining = remaining[:-2]
    else:
        grouped = integer_part

    fraction = f"{amount:.2f}".split(".")[1]
    formatted = f"₹{grouped}"
    if fraction != "00":
        formatted += f".{fraction}"

    return f"-{formatted}" if is_negative else formatted
