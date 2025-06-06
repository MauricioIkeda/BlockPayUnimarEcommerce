# Create your models here.
from django.db import models

class Payment(models.Model):
    seller_address = models.CharField(max_length=255)
    initial_balance = models.FloatField()
    amount_brl = models.FloatField()
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
