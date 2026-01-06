from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, RoomViewSet, BookingCreateView,
    BookingMyListView, CancelApiView, AvailableRoomsView
)

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='rooms')

urlpatterns = [
    
    path('rooms/available/', AvailableRoomsView.as_view(), name='available_rooms'),

    path('booking/create', BookingCreateView.as_view()),
    path('booking/list/me', BookingMyListView.as_view(), name='my_bookings'),
    path('booking/cancel/<int:pk>', CancelApiView.as_view()),

    path('auth/register/', RegisterView.as_view(), name='register'),

    
    path('', include(router.urls)),
]
