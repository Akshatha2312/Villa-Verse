import pytest

from app.currency import format_inr


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (1000, "₹1,000"),
        (25000, "₹25,000"),
        (150000, "₹1,50,000"),
        (1250000, "₹12,50,000"),
        (1234.5, "₹1,234.50"),
        (1234.56, "₹1,234.56"),
        (1.999, "₹2"),
        (-150000, "-₹1,50,000"),
    ],
)
def test_format_inr_uses_indian_grouping_and_only_needed_decimals(amount, expected):
    assert format_inr(amount) == expected


def test_format_inr_handles_missing_amount():
    assert format_inr(None) == "₹0"
