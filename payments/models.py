# Create your models here.
from django.db import models

class Payment(models.Model):
    address = models.CharField(max_length=255)
    private_key = models.CharField(max_length=255)
    #seller_address = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='pending')  # novo campo
    amount_received = models.DecimalField(max_digits=20, decimal_places=6, default=0)  # opcional
    created_at = models.DateTimeField(auto_now_add=True)

    def transfer(self):
        if self.status == "confirmed":
            pass
