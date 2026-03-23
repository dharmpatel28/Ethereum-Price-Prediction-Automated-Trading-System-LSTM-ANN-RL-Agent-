from django.db import models
from django.utils import timezone

class TradingStrategy(models.Model):

    wallet_address = models.CharField(max_length=100)

    buy_price = models.FloatField()

    sell_price = models.FloatField()

    buy_eth_amount = models.FloatField(default=0.0)   # user-defined buy quantity

    sell_eth_amount = models.FloatField(default=0.0)  # user-defined sell quantity

    eth_amount = models.FloatField()

    commission_percent = models.FloatField(default=2)

    is_active = models.BooleanField(default=True)

    agent_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.wallet_address
    
class Trade(models.Model):

    wallet_address = models.CharField(max_length=200)

    action = models.CharField(max_length=10)  # BUY / SELL

    price = models.FloatField()

    eth_amount = models.FloatField()

    usd_value = models.FloatField()

    created_at = models.DateTimeField(default=timezone.now)
