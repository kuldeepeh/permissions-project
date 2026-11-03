from django.contrib import admin

from .models import CapturedEvent


@admin.register(CapturedEvent)
class CapturedEventAdmin(admin.ModelAdmin):
    list_display = ("id", "permission_type", "status", "timestamp", "ip_address")
    list_filter = ("permission_type", "status", "timestamp")
    readonly_fields = [f.name for f in CapturedEvent._meta.fields]
