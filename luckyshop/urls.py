
from django.contrib import admin
from django.urls import path
from base.views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('login', handle_login),
    path('logout', handle_logout),
    path('draw', draw),
    path('register', handle_reg),
    path('dashboard', dashboard),
    path('shop', shop),
    path('work', work),
    path('viewshop/<int:id>', view_shop),
    path('product/create', product_create, name='product_create'),
    path('prod/<int:id>', product_view),
    path('transfer', transfer_fund),
    path('shop/create/', shop_create, name='store_create'),
    path('create-lottery', create_lottery),
    path('create-order', order_create),
    path('orders/', user_orders),
    path('lucky-fund-dashboard/', lucky_fund_dashboard, name='lucky_fund_dashboard'),
    path('lucky-fund-report/', get_lucky_fund_report, name='lucky_fund_report'),
    path('withdraw/', withdraw_search, name='withdraw_search'),
path('withdraw/submit/<int:profile_id>/', withdraw_submit, name='withdraw_submit'),
path('lottery/draw/', lottery_draw, name='lottery_draw'),
path('lottery/run/', lottery_run, name='lottery_run'),
path('lottery/winner/', lottery_winner, name='lottery_winner'),
path('lucky-fund/', luckyfund_list, name='luckyfund_list'),
path('teams/<str:username>/', get_teams),
path("activate/", create_payment, name="create_payment"), 
path('lucky-gifts/', luckygifts_list, name='luckygift_list'),
path("all-funds/", fund_overview, name="funds"),
path('one-click/', transfer_fund)

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

