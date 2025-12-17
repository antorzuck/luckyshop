
from django.contrib import admin
from django.urls import path
from base.views import *



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('login', handle_login),
    path('logout', handle_logout),
    path('draw', draw),
    path('register', handle_reg),
    path('dashboard', dashboard),
    path('create-lottery', create_lottery),
    path('lucky-fund-dashboard/', lucky_fund_dashboard, name='lucky_fund_dashboard'),
    path('lucky-fund-report/', get_lucky_fund_report, name='lucky_fund_report'),
    path('withdraw/', withdraw_search, name='withdraw_search'),
path('withdraw/submit/<int:profile_id>/', withdraw_submit, name='withdraw_submit'),
path('lottery/draw/', lottery_draw, name='lottery_draw'),
path('lottery/run/', lottery_run, name='lottery_run'),
path('lottery/winner/', lottery_winner, name='lottery_winner'),
]

