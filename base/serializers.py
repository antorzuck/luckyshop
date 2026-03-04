from rest_framework import serializers
from .models import Driver, Ride, DriverEarning


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Driver
        fields = '__all__'


class RideSerializer(serializers.ModelSerializer):
    driver_info = DriverSerializer(source='driver', read_only=True)

    class Meta:
        model  = Ride
        fields = '__all__'


class RideCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Ride
        fields = [
            'rider_name', 'pickup_lat', 'pickup_lng', 'pickup_name',
            'dropoff_lat', 'dropoff_lng', 'dropoff_name',
            'vehicle_type', 'fare', 'distance_km',
        ]


class EarningSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DriverEarning
        fields = '__all__'