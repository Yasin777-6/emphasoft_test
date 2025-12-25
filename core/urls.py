from django.urls import path,include
from .views import RegisterView,RoomViewSet,BookingCreateView,BookingMyListView,CancelApiView,AvailableRoomsView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'rooms',RoomViewSet,basename='rooms')

urlpatterns=[
    path('',include(router.urls)),
    path('booking/create',BookingCreateView.as_view()),
    path('booking/list/me',BookingMyListView.as_view(),name='my_bookings'),
    path('booking/cancel/<int:pk>',CancelApiView.as_view()),
    path('rooms/available/', AvailableRoomsView.as_view(), name='available_rooms'),

    path('auth/register/',RegisterView.as_view(),name='register'),
]