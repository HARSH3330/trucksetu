from decimal import Decimal
import asyncio

from app.api.pricing import DEFAULT_RULE, SuggestionInput, compute_route
from app.domain import trip_price_suggestion


def test_marketplace_suggestion_keeps_charges_separate() -> None:
    result = trip_price_suggestion(Decimal("100"), 1, 4, True, True, 10, True, Decimal("2"), DEFAULT_RULE)
    assert result["base_trip"] == Decimal("5000.00")
    assert result["loading"] == Decimal("170.00")
    assert result["unloading"] == Decimal("170.00")
    assert result["extra_stops"] == Decimal("1000.00")
    assert result["night"] == Decimal("500.00")
    assert result["waiting"] == Decimal("500.00")


def test_first_two_stops_have_no_extra_charge() -> None:
    result = trip_price_suggestion(Decimal("10"), 1, 2, False, False, 0, False, Decimal("0"), DEFAULT_RULE)
    assert result["extra_stops"] == Decimal("0.00")


def test_manual_distance_fallback_does_not_require_google_maps() -> None:
    route = asyncio.run(compute_route(SuggestionInput(pickup="Delhi", destination="Jaipur", distance_km=Decimal("280"))))
    assert route["distance_km"] == Decimal("280.00")
    assert route["duration_minutes"] == 420
    assert route["source"] == "manual_distance"


def test_provider_kyc_documents_match_launch_policy() -> None:
    from app.api.kyc import REQUIRED
    assert REQUIRED["driver"] == {"aadhaar", "pan", "driving_licence"}
    assert REQUIRED["owner"] == {"aadhaar", "pan", "vehicle_rc"}
