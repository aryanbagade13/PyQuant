import math


def normal_pdf(x: float) -> float:
    return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def calculate_d1(
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float,
) -> float:
    numerator = (
        math.log(spot / strike)
        + (risk_free_rate - dividend_yield + 0.5 * volatility**2) * time_to_expiry
    )

    denominator = volatility * math.sqrt(time_to_expiry)

    return numerator / denominator


def calculate_d2(
    d1: float,
    volatility: float,
    time_to_expiry: float,
) -> float:
    return d1 - volatility * math.sqrt(time_to_expiry)
