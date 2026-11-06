import json
import pytest
from unittest.mock import patch
from django.urls import reverse
from django.core import mail
from orders.models import Order, OrderItem
from orders.views import send_order_confirmation_email


@pytest.mark.django_db
class TestWebhookSecurityAndSignals:

    def test_valid_cryptographic_signature_marks_order_paid(self, client, test_user, product_s7):
        """9. Valid Stripe webhook cryptographic payload marks order as Paid."""
        order = Order.objects.create(
            user=test_user,
            total_amount=product_s7.price,
            status="New"
        )
        mock_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": str(order.id),
                    "customer_details": {"email": "buyer@stripe.test"},
                    "metadata": {"order_id": str(order.id)}
                }
            }
        }

        with patch("stripe.Webhook.construct_event", return_value=mock_payload):
            response = client.post(
                reverse("stripe_webhook"),
                data=json.dumps(mock_payload),
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="valid_t_signature_hash"
            )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == "Paid"

    def test_invalid_signature_rejection(self, client):
        """10. Webhook rejects fake or missing signature header with HTTP 400."""
        import stripe
        with patch("stripe.Webhook.construct_event", side_effect=stripe.error.SignatureVerificationError("Invalid sig", "sig_header")):
            response = client.post(
                reverse("stripe_webhook"),
                data=json.dumps({"type": "fake.event"}),
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="forged_signature_token"
            )

        assert response.status_code == 400

    def test_payload_tampering_rejection(self, client):
        """11. Payload tampering or malformed JSON triggers immediate rejection."""
        response = client.post(
            reverse("stripe_webhook"),
            data="MALFORMED_NON_JSON_CORRUPT_STRING",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="any_sig"
        )
        assert response.status_code == 400

    def test_order_confirmation_mail_dispatched_via_mailtrap(self, test_user, product_s7):
        """12. Automated order confirmation email dispatch triggered for Mailtrap inbox."""
        order = Order.objects.create(
            user=test_user,
            total_amount=product_s7.price,
            status="Paid"
        )
        OrderItem.objects.create(order=order, product=product_s7, quantity=1, unit_price=product_s7.price)

        mail.outbox.clear()
        send_order_confirmation_email(order, recipient_email="custom_stripe@buyer.com")

        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert f"Order Confirmation #{order.id}" in sent_email.subject
        assert "custom_stripe@buyer.com" in sent_email.to
        assert str(product_s7.name) in sent_email.alternatives[0][0]