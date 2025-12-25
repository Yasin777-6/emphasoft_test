from django.shortcuts import render
from rest_framework import generics, permissions,status,viewsets
from .serializers import RegisterSerializer,RoomSerializer,BookingReadSerializer,BookingCreateSerializer
from .models import Room,Booking
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import date
from django.shortcuts import get_object_or_404


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes=[permissions.AllowAny]
class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=RoomSerializer
    def get_queryset(self):
        qs = Room.objects.all()
        capacity = self.request.query_params.get("capacity")
        min_price = self.request.query_params.get("min_price")
        ordering = self.request.query_params.get("ordering")

        if capacity:
            qs = qs.filter(capacity=int(capacity))

        if min_price:
            qs = qs.filter(cost_per_day__gte=min_price)

        if ordering in ["cost_per_day", "-cost_per_day", "capacity", "-capacity"]:
            qs = qs.order_by(ordering)

        return qs

class BookingCreateView(generics.CreateAPIView):
    permission_classes=[permissions.IsAuthenticated] 
    serializer_class = BookingCreateSerializer
    
    def perform_create(self,serializer):
        serializer.save(user=self.request.user)


class BookingMyListView(generics.ListAPIView):
    serializer_class = BookingReadSerializer
    permission_classes=[permissions.IsAuthenticated]
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

        
class CancelApiView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self,request,pk):
        booking = get_object_or_404(Booking,pk=pk)
        qr=Booking.objects.filter(user=booking.user,pk=pk)
        if booking.user ==request.user:
            qr.update(is_canceled=True)
        return Response({'status':'canceled'})



class AvailableRoomsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        start_str = request.query_params.get("start_date")
        end_str = request.query_params.get("end_date")

        if not start_str or not end_str:
            return Response(
                {"error": "start_date and end_date are required "},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = date.fromisoformat(start_str)
            end_date = date.fromisoformat(end_str)
        except ValueError:
            return Response(
                {"error": "Invalid date format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        if start_date > end_date:
            return Response(
                {"error": "start_date cannot be after end_date mann"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        

        available_rooms = Room.objects.exclude(
            bookings__is_canceled=False,
            bookings__start_date__lte=end_date,
            bookings__end_date__gte=start_date,
        )

        return Response(RoomSerializer(available_rooms, many=True).data)

