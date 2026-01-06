from django.contrib.auth.models import User
from .models import Room, Booking
from rest_framework import serializers
from typing import Any

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']
    
    def create(self, validated_data: dict[str, Any]) -> User:
        return User.objects.create_user(**validated_data)

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class BookingReadSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

class BookingCreateSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())

    class Meta:
        model = Booking
        fields = ['room', 'start_date', 'end_date']

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        start_date = attrs['start_date']
        end_date = attrs['end_date']
        room = attrs['room']
        
        if start_date > end_date:
            raise serializers.ValidationError('The start date cannot be after the end date.')
        
        overlapping_bookings = Booking.objects.filter(
            room=room,
            is_canceled=False,
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        if overlapping_bookings.exists():
            raise serializers.ValidationError('Sorry, this room is already booked for the selected dates.')
            
        return attrs

class AvailableRoomsQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError('start_date cannot be after end_date')
        return attrs