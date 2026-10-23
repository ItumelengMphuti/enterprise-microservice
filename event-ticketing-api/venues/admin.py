
from django.contrib import admin
from .models import Venue, Seat


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city")
    search_fields = ("name", "city")


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("id", "venue", "row_label", "seat_number")
    list_filter = ("venue",)
    search_fields = ("venue__name", "row_label")
