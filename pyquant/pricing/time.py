from datetime import date


def time_to_expiry(expiry: date, valuation_date: date) -> float:
    days_remaining = (expiry - valuation_date).days
    if days_remaining < 0:
        raise ValueError("The option has already expired.")
    return days_remaining / 365.0
