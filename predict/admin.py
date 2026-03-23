from .models import TradingStrategy
from django.contrib import admin

admin.site.register(TradingStrategy)

from .models import Trade

admin.site.register(Trade)