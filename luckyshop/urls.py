
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
]
