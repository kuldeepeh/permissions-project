import base64
import json
import uuid

from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import CapturedEvent


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def index(request):
    """Main demo page with the permission buttons."""
    return render(request, "tracker/index.html")


def dashboard(request):
    """Simple backend view listing everything captured so far."""
    events = CapturedEvent.objects.all()[:200]
    return render(request, "tracker/dashboard.html", {"events": events})


def _decode_base64_file(data_url, default_name, default_ext):
    """
    Accepts a data URL like 'data:image/png;base64,AAAA...' and returns
    a Django ContentFile plus a generated filename.
    """
    if ";base64," in data_url:
        header, b64data = data_url.split(";base64,", 1)
    else:
        b64data = data_url
    file_bytes = base64.b64decode(b64data)
    filename = f"{default_name}_{uuid.uuid4().hex[:10]}.{default_ext}"
    return ContentFile(file_bytes, name=filename)


@csrf_exempt
@require_POST
def capture_event(request):
    """
    Single endpoint used by the frontend JS to log every stage of a
    permission interaction: request made, granted, denied, or data captured.

    Expected JSON body:
    {
        "permission_type": "camera" | "microphone" | "location",
        "status": "requested" | "granted" | "denied",
        "image_data": "<data:image/png;base64,...>"   (optional, camera)
        "audio_data": "<data:audio/webm;base64,...>"   (optional, microphone)
        "latitude": 12.34, "longitude": 56.78, "accuracy": 15.2 (optional, location)
        "extra": { ... }  (optional, free-form)
    }
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body"}, status=400)

    permission_type = payload.get("permission_type")
    status = payload.get("status", "requested")

    if permission_type not in dict(CapturedEvent.PERMISSION_CHOICES):
        return JsonResponse({"ok": False, "error": "Unknown permission_type"}, status=400)
    if status not in dict(CapturedEvent.STATUS_CHOICES):
        return JsonResponse({"ok": False, "error": "Unknown status"}, status=400)

    event = CapturedEvent(
        permission_type=permission_type,
        status=status,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        extra_data=payload.get("extra"),
    )

    if status == "granted":
        if permission_type == "camera" and payload.get("image_data"):
            event.photo = _decode_base64_file(payload["image_data"], "photo", "png")
        elif permission_type == "microphone" and payload.get("audio_data"):
            event.audio = _decode_base64_file(payload["audio_data"], "audio", "webm")
        elif permission_type == "location":
            event.latitude = payload.get("latitude")
            event.longitude = payload.get("longitude")
            event.location_accuracy_m = payload.get("accuracy")

    event.save()

    return JsonResponse({"ok": True, "event_id": event.id})
