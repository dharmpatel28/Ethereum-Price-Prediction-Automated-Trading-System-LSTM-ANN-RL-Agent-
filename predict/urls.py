# prediction/urls.py

from django.urls import path
from . import views

urlpatterns = [


    path('', views.home, name='home'),



    # -------------------------
    # ML Prediction Endpoints
    # -------------------------
    path("ml/", views.ml_home, name="ml_home"),              # ML HTML page
    path("ml/get_advice/", views.get_advice, name="get_advice"),  # ML prediction API

    # -------------------------
    # RL Agent Endpoints
    # -------------------------
    path("rl/", views.rl_home, name="rl_home"),                     # RL HTML page
    path("rl/api/bot-status/", views.get_bot_status, name="bot_status"),
    path("rl/api/trades/", views.api_recent_trades, name="recent_trades"),
    path('rl/api/enroll-rl/', views.enroll_rl_bot, name='enroll_rl_bot'),
    path("rl/api/toggle-agent/", views.toggle_agent, name="toggle_agent"),
    path("rl/api/update-strategy/", views.update_strategy, name="update_strategy"),
    path("rl/api/create-full-strategy/", views.create_full_strategy, name="create_full_strategy"),
    path("rl/api/delete-strategy/", views.delete_strategy),
]