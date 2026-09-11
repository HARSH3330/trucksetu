from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import (
    BookingCreate,
    AnalyticsEventCreate,
    CapacityReservationCreate,
    CancellationCreate,
    ConversationCreate,
    DisputeCreate,
    DisputeMessageCreate,
    DriverAssignment,
    MessageCreate,
    OfflinePaymentCreate,
    OtpVerify,
    ReviewCreate,
    SafetyReportCreate,
    TransportRequestCreate,
    TripStatusUpdate,
)


IDENTITY_FIELDS = {
    AnalyticsEventCreate: {"user_id"},
    TransportRequestCreate: {"customer_id"},
    BookingCreate: {"customer_id"},
    DriverAssignment: {"actor_id"},
    TripStatusUpdate: {"actor_id"},
    OtpVerify: {"actor_id"},
    OfflinePaymentCreate: {"actor_id"},
    ReviewCreate: {"reviewer_id", "reviewer_role"},
    DisputeCreate: {"raised_by"},
    DisputeMessageCreate: {"sender_id"},
    CancellationCreate: {"cancelled_by"},
    SafetyReportCreate: {"reporter_id"},
    ConversationCreate: {"requester_id"},
    MessageCreate: {"sender_id"},
    CapacityReservationCreate: {"customer_id"},
}


def test_authenticated_identity_is_not_accepted_from_mutation_bodies() -> None:
    for schema, forbidden_fields in IDENTITY_FIELDS.items():
        assert forbidden_fields.isdisjoint(schema.model_fields)


def test_sensitive_routes_reject_anonymous_callers_before_database_access() -> None:
    resource_id = uuid.uuid4()
    calls = [
        ("patch", f"/api/v1/quotes/{resource_id}"),
        ("get", f"/api/v1/requests/{resource_id}/quotes"),
        ("get", "/api/v1/requests/mine"),
        ("get", "/api/v1/providers/me"),
        ("get", "/api/v1/carrier-vehicles"),
        ("get", f"/api/v1/providers/{resource_id}/drivers"),
        ("get", "/api/v1/payments"),
        ("get", "/api/v1/invoices"),
        ("post", f"/api/v1/invoices/{resource_id}/issue"),
        ("post", f"/api/v1/quotes/{resource_id}/counter-offers"),
        ("post", f"/api/v1/trips/{resource_id}/status"),
        ("post", f"/api/v1/trips/{resource_id}/otp/pickup"),
        ("post", f"/api/v1/trips/{resource_id}/otp/verify"),
        ("post", f"/api/v1/bookings/{resource_id}/payments/online"),
        ("post", f"/api/v1/bookings/{resource_id}/payments/offline"),
        ("post", f"/api/v1/payments/{resource_id}/confirm-offline"),
        ("post", f"/api/v1/bookings/{resource_id}/settlement-eligibility"),
        ("post", f"/api/v1/bookings/{resource_id}/invoice"),
        ("get", "/api/v1/notifications"),
        ("get", "/api/v1/conversations"),
        ("get", "/api/v1/users/me/notification-preferences"),
        ("put", "/api/v1/users/me/notification-preferences"),
        ("post", "/api/v1/conversations"),
        ("get", f"/api/v1/conversations/{resource_id}/messages"),
        ("post", f"/api/v1/conversations/{resource_id}/messages"),
        ("post", f"/api/v1/bookings/{resource_id}/reviews"),
        ("get", "/api/v1/trust/activity"),
        ("get", "/api/v1/dashboard/summary"),
        ("get", "/api/v1/admin/marketplace-health"),
        ("get", "/api/v1/kyc/applications/me"),
        ("get", "/api/v1/kyc/admin/applications"),
        ("get", "/api/v1/kyc/admin/expiring-documents"),
        ("get", f"/api/v1/bookings/{resource_id}/cancellation-preview"),
        ("post", f"/api/v1/bookings/{resource_id}/disputes"),
        ("post", f"/api/v1/disputes/{resource_id}/messages"),
        ("post", f"/api/v1/bookings/{resource_id}/cancel"),
        ("post", "/api/v1/safety-reports"),
        ("post", f"/api/v1/admin/disputes/{resource_id}/resolve"),
        ("post", "/api/v1/admin/capacity/release-expired"),
        ("post", f"/api/v1/bookings/{resource_id}/refunds/manual"),
        ("get", "/api/v1/bookings"),
    ]
    with TestClient(app, base_url="http://localhost") as client:
        for method, path in calls:
            response = client.request(method, path, json={})
            assert response.status_code == 401, (method, path, response.text)


def test_sensitive_routes_declare_bearer_security_in_openapi() -> None:
    schema = app.openapi()
    protected_paths = {
        "/api/v1/quotes/{quote_id}",
        "/api/v1/trips/{trip_id}/status",
        "/api/v1/bookings/{booking_id}/payments/online",
        "/api/v1/notifications",
        "/api/v1/conversations",
        "/api/v1/bookings/{booking_id}/disputes",
        "/api/v1/safety-reports",
    }
    for path in protected_paths:
        for operation in schema["paths"][path].values():
            assert operation.get("security"), path
