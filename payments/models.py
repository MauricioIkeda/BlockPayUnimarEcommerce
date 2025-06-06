# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from Store.models import Order

class Payment(models.Model):
    order = model.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment", null=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments", null=True)
    initial_balance = models.FloatField(default=0)
    amount_brl = models.FloatField()
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
