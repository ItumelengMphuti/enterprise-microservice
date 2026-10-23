
from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event_seat",
        "status",
        "reserved_at",
    )
    list_filter = ("status",)
    search_fields = (
        "user__username",
        "event_seat__event__title",
    )
    list_select_related = ("user", "event_seat")
