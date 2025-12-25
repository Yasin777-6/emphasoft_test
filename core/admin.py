from django.contrib import admin

# Register your models here.

from .models import Room, Booking

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "capacity", "cost_per_day")
    search_fields = ("name",)
    list_filter = ("capacity",)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "user", "start_date", "end_date", "is_canceled", "create_at")
    list_filter = ("is_canceled", "start_date", "end_date")
    search_fields = ("room__name", "user__username")
