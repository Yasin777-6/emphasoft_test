from django.db import models
from django.contrib.auth.models import User
class Room(models.Model):
    name = models.CharField(max_length=25,unique=True)
    capacity = models.PositiveSmallIntegerField()
    cost_per_day=models.DecimalField(max_digits=10,decimal_places=2)

    def __str__(self):
        return f'{self.name}'
class Booking(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    room = models.ForeignKey(Room,on_delete=models.CASCADE,related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    is_canceled =models.BooleanField(default=False)
    create_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.room} - {self.start_date} - {self.end_date}'




