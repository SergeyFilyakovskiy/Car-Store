import hashlib
import hmac
import json

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .exceptions import TopUpAlreadyProcessedError, TopUpInvalidStatusError
from .models import BalanceTopUp
from .services import BalanceTopUpService


def verify_signature(request: HttpRequest) -> bool:
    """Verifies the webhook's HMAC signature."""
    received_signature = request.headers.get("X-Signature")
    if not received_signature:
        return False

    expected_signature = hmac.new(
        key=settings.PAYMENT_WEBHOOK_SECRET.encode("utf-8"),
        msg=request.body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, received_signature)


@csrf_exempt
@require_POST
def payment_webhook(request: HttpRequest) -> JsonResponse:
    """Webhook from the payment system."""

    if not verify_signature(request):
        return JsonResponse({"error": "Invalid signature"}, status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    external_id = payload.get("transaction_id")
    topup_id = payload.get("metadata", {}).get("topup_id")
    status = payload.get("status")

    if not all([external_id, topup_id, status]):
        return JsonResponse({"error": "Missing required fields"}, status=400)

    try:
        topup = BalanceTopUp.objects.get(id=topup_id)
    except BalanceTopUp.DoesNotExist:
        return JsonResponse({"error": "TopUp not found"}, status=404)

    try:
        if status == "success":
            BalanceTopUpService.confirm_topup(
                topup_id=topup.id,
                external_id=external_id,
                provider_response=payload,
            )
        elif status == "failed":
            BalanceTopUpService.fail_topup(topup.id, reason=payload.get("error", ""))
    except TopUpAlreadyProcessedError:
        pass
    except TopUpInvalidStatusError as e:
        return JsonResponse({"error": str(e)}, status=409)

    return JsonResponse({"status": "ok"})
