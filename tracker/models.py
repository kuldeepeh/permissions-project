from django.db import models


class CapturedEvent(models.Model):
    """
    One row per permission interaction: a request, a grant/deny decision,
    and (if granted) a snapshot of whatever data that permission exposed.
    """

    PERMISSION_CHOICES = [
        ("camera", "Camera"),
        ("microphone", "Microphone"),
        ("location", "Location"),
    ]

    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("granted", "Granted"),
        ("denied", "Denied"),
    ]

    permission_type = models.CharField(max_length=20, choices=PERMISSION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Captured payloads (only populated when status == "granted")
    photo = models.ImageField(upload_to="captures/photos/", null=True, blank=True)
    audio = models.FileField(upload_to="captures/audio/", null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_accuracy_m = models.FloatField(null=True, blank=True)

    extra_data = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.permission_type} - {self.status} - {self.timestamp:%Y-%m-%d %H:%M:%S}"
