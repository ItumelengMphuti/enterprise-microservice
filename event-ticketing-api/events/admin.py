
from django.contrib import admin
from .models import Event, EventSeat


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "venue", "start_time", "status")
    list_filter = ("status", "venue")
    search_fields = ("title", "venue__name")
    list_select_related = ("venue",)


@admin.register(EventSeat)
class EventSeatAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "seat", "price")
    list_select_related = ("event", "seat")
    search_fields = ("event__title", "seat__row_label")
