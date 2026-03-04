

from django.contrib import admin
from .models import *

# Simple reusable base for all models
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'number', 'balance', 'is_verified', 'referred_by')
    search_fields = ('user__username', 'name', 'number')
    list_filter = ('is_verified',)

@admin.register(LuckyPackage)
class LuckyPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at')

@admin.register(LuckyFund)
class LuckyFundAdmin(admin.ModelAdmin):
    list_display = ('number', 'package', 'balance', 'is_rewarded', 'created_at')
    list_filter = ('is_rewarded',)
    search_fields = ('profile__name', 'package__name')

# The following are all simple, so we can auto-register them with a loop
fund_models = [
   packageSetting, HonorableFund, AdminFund, ShopkeeperFund, GovernmentFund,
    OrganizerFund, UnemploymentFund, ScholarshipFund, LuckyGift, PoorFund, LuckyProfit, Withdraw, FundSettings, Shop,  Product, Category, Order, Affiliate
]

for model in fund_models:
    admin.site.register(model)



@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display  = ('name', 'vehicle', 'plate', 'rating', 'is_online')
    list_filter   = ('is_online',)
    search_fields = ('name', 'plate')


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display  = ('id', 'rider_name', 'driver', 'vehicle_type', 'fare', 'status', 'requested_at')
    list_filter   = ('status', 'vehicle_type')
    search_fields = ('rider_name', 'pickup_name', 'dropoff_name')
    readonly_fields = ('requested_at', 'updated_at')


@admin.register(DriverEarning)
class DriverEarningAdmin(admin.ModelAdmin):
    list_display = ('driver', 'ride', 'amount', 'earned_at')