from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from .models import Room, Booking
from .serializers import (
    RegisterSerializer,
    RoomSerializer,
    BookingReadSerializer,
    BookingCreateSerializer,
    AvailableRoomsQuerySerializer,
)


@extend_schema(tags=["auth"])
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=["rooms"])
class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RoomSerializer

    def get_queryset(self) -> QuerySet[Room]:
        qs = Room.objects.all()
        capacity = self.request.query_params.get("capacity")
        min_price = self.request.query_params.get("min_price")
        ordering = self.request.query_params.get("ordering")

        if capacity:
            try:
                qs = qs.filter(capacity=int(capacity))
            except ValueError:
                pass

        if min_price:
            try:
                qs = qs.filter(cost_per_day__gte=min_price)  
            except ValueError:
                pass

        if ordering in ["cost_per_day", "-cost_per_day", "capacity", "-capacity"]:
            qs = qs.order_by(ordering)

        return qs


@extend_schema(tags=["bookings"])
class BookingCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingCreateSerializer

    @transaction.atomic
    def perform_create(self, serializer: BookingCreateSerializer) -> None:
        room = serializer.validated_data["room"]
        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        # Lock the room 
        Room.objects.select_for_update().get(pk=room.pk)

        
        conflict_exists = Booking.objects.filter(
            room=room,
            is_canceled=False,
            start_date__lte=end_date,
            end_date__gte=start_date,
        ).exists()

        if conflict_exists:
            raise ValidationError("Room is already booked.")

        serializer.save(user=self.request.user)


@extend_schema(tags=["bookings"])
class BookingMyListView(generics.ListAPIView):
    serializer_class = BookingReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Booking]:
        # ✅ IMPORTANT: call select_related("room") (don't return the method!)
        return (
            Booking.objects
            .filter(user=self.request.user)
            .select_related("room")     # fixes N+1 (serializer uses room.name)
            .order_by("-create_at")
        )


@extend_schema(tags=["bookings"])
class CancelApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk: int) -> Response:
        qs = Booking.objects.select_for_update()

        if request.user.is_superuser:
            booking = get_object_or_404(qs, pk=pk)
        else:
            booking = get_object_or_404(qs, pk=pk, user=request.user)

        if booking.is_canceled:
            return Response(
                {"detail": "Booking is already canceled пэпэ."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.is_canceled = True
        booking.save(update_fields=["is_canceled"])

        return Response({"status": "canceled"}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["rooms"],
    parameters=[AvailableRoomsQuerySerializer],
    responses={200: RoomSerializer(many=True)},
)
class AvailableRoomsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request) -> Response:
        serializer = AvailableRoomsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        # Exclude rooms 
        available_rooms = (
            Room.objects.exclude(
                bookings__is_canceled=False,
                bookings__start_date__lte=end_date,
                bookings__end_date__gte=start_date,
            )
            .distinct()  # avoid duplicate
        )

        return Response(RoomSerializer(available_rooms, many=True).data, status=status.HTTP_200_OK)
