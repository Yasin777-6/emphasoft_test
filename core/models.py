from django.db import models

class room(models.Model):
    name = models.CharField(max_length=25)
    number_of_space= models.DecimalField()
    cost_per_day=models.DecimalField()
    
