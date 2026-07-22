from datetime import date

import pytest

from pyquant.analysis.volatility_surface import VolatilitySurface


def test_surface_returns_expiries():
    class FakeSmile:
        def __init__(self, expiry):
            self.expiry = expiry

    first_smile = FakeSmile(date(2026, 8, 7))
    second_smile = FakeSmile(date(2026, 8, 21))

    surface = VolatilitySurface(
        symbol="AAPL",
        spot=210.0,
        smiles=(first_smile, second_smile),
    )

    assert surface.expiries() == (
        date(2026, 8, 7),
        date(2026, 8, 21),
    )


def test_surface_finds_exact_expiry():
    class FakeSmile:
        def __init__(self, expiry):
            self.expiry = expiry

    first_smile = FakeSmile(date(2026, 8, 7))
    second_smile = FakeSmile(date(2026, 8, 21))

    surface = VolatilitySurface(
        symbol="AAPL",
        spot=210.0,
        smiles=(first_smile, second_smile),
    )

    result = surface.smile_for_expiry(
        date(2026, 8, 21)
    )

    assert result is second_smile


def test_surface_finds_nearest_expiry():
    class FakeSmile:
        def __init__(self, expiry):
            self.expiry = expiry

    first_smile = FakeSmile(date(2026, 8, 7))
    second_smile = FakeSmile(date(2026, 8, 21))

    surface = VolatilitySurface(
        symbol="AAPL",
        spot=210.0,
        smiles=(first_smile, second_smile),
    )

    result = surface.nearest_smile(
        date(2026, 8, 18)
    )

    assert result is second_smile


def test_missing_exact_expiry_raises_error():
    class FakeSmile:
        def __init__(self, expiry):
            self.expiry = expiry

    surface = VolatilitySurface(
        symbol="AAPL",
        spot=210.0,
        smiles=(
            FakeSmile(date(2026, 8, 7)),
        ),
    )

    with pytest.raises(ValueError):
        surface.smile_for_expiry(
            date(2026, 8, 21)
        )