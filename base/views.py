from django.shortcuts import render, redirect, get_object_or_404
from .models import * 
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from .decor import agent_required 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.db.models.functions import RowNumber
from django.db.models.expressions import Window
from django.core.paginator import Paginator
import requests


import random
import math
from django.db.models import Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import DriverSerializer, RideSerializer, RideCreateSerializer, EarningSerializer
import firebase_admin
from firebase_admin import credentials, messaging


cred = credentials.Certificate("luckyshop-69-firebase-adminsdk-fbsvc-a388834f06.json")
firebase_admin.initialize_app(cred)

registration_token = "dY35qD_ujNXH4-lVP92r1d:APA91bFCjYUu7Z37GeE_3ML9xqtXXVery4hdXkndZ9wiiivCsiZW27MWkf4eUT8qyeS5bnejrm4Gzl2W6trquzOCgDSLoVhVlZX6porzXlWuYlzDgYUoVlE"


def push_noti():
    message = messaging.Message(
        notification=messaging.Notification(
            title="LuckyGO",
            body="A ride request has been crated. If you are a driver check it now."
        ),
        token=registration_token,
    )
    response = messaging.send(message)
    print("Successfully sent message:", response)


def calc_dist(lat1, lng1, lat2, lng2):
    """Haversine distance in km."""
    R = 6371
    to_rad = math.radians
    d_lat = to_rad(lat2 - lat1)
    d_lng = to_rad(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(to_rad(lat1)) * math.cos(to_rad(lat2))
         * math.sin(d_lng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


VEHICLE_MULT = {'bike': 1.0, 'car': 2.2, 'cng': 1.5}


@api_view(['GET'])
def list_drivers(request):
    """Return all drivers (optionally filter by ?online=true)."""
    qs = Driver.objects.all()
    if request.query_params.get('online') == 'true':
        qs = qs.filter(is_online=True)
    return Response(DriverSerializer(qs, many=True).data)


@api_view(['POST'])
def toggle_driver_online(request, driver_id):
    """Toggle a driver's online status."""
    try:
        driver = Driver.objects.get(pk=driver_id)
    except Driver.DoesNotExist:
        return Response({'error': 'Driver not found'}, status=status.HTTP_404_NOT_FOUND)

    driver.is_online = not driver.is_online
    driver.save()
    return Response({'driver_id': driver.id, 'is_online': driver.is_online})


@api_view(['PATCH'])
def update_driver_location(request, driver_id):
    """Update driver GPS location.  Body: { lat, lng }"""
    try:
        driver = Driver.objects.get(pk=driver_id)
    except Driver.DoesNotExist:
        return Response({'error': 'Driver not found'}, status=status.HTTP_404_NOT_FOUND)

    driver.lat = request.data.get('lat', driver.lat)
    driver.lng = request.data.get('lng', driver.lng)
    driver.save()
    return Response({'driver_id': driver.id, 'lat': driver.lat, 'lng': driver.lng})


@api_view(['GET'])
def driver_stats(request, driver_id):
    """Return earnings & rides completed for a driver."""
    try:
        driver = Driver.objects.get(pk=driver_id)
    except Driver.DoesNotExist:
        return Response({'error': 'Driver not found'}, status=status.HTTP_404_NOT_FOUND)

    earnings_qs = DriverEarning.objects.filter(driver=driver)
    total_earnings  = earnings_qs.aggregate(total=Sum('amount'))['total'] or 0
    rides_completed = Ride.objects.filter(driver=driver, status='completed').count()

    return Response({
        'driver_id':        driver.id,
        'name':             driver.name,
        'total_earnings':   total_earnings,
        'rides_completed':  rides_completed,
    })



@api_view(['GET'])
def list_rides(request):
    """List all rides or filter by ?status=pending etc."""
    qs = Ride.objects.select_related('driver').order_by('-requested_at')
    s = request.query_params.get('status')
    if s:
        qs = qs.filter(status=s)
    return Response(RideSerializer(qs, many=True).data)


@api_view(['POST'])
def create_ride(request):
    """
    Rider requests a new ride.
    Body: { rider_name, pickup_lat, pickup_lng, pickup_name,
            dropoff_lat, dropoff_lng, dropoff_name, vehicle_type }
    The fare & distance are calculated server-side.
    """
    data = request.data.copy()

    try:
        dist = calc_dist(
            float(data['pickup_lat']),  float(data['pickup_lng']),
            float(data['dropoff_lat']), float(data['dropoff_lng']),
        )
    except (KeyError, ValueError):
        return Response({'error': 'Invalid coordinates'}, status=status.HTTP_400_BAD_REQUEST)

    mult       = VEHICLE_MULT.get(data.get('vehicle_type', 'car'), 2.2)
    data['fare']        = int(dist * 25 * mult + 80)
    data['distance_km'] = round(dist, 2)

    ser = RideCreateSerializer(data=data)
    if ser.is_valid():
        ride = ser.save(status='pending')

        push_noti()
        return Response(RideSerializer(ride).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def ride_detail(request, ride_id):
    """Get a single ride's current state (poll this for status updates)."""
    try:
        ride = Ride.objects.select_related('driver').get(pk=ride_id)
    except Ride.DoesNotExist:
        return Response({'error': 'Ride not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(RideSerializer(ride).data)


@api_view(['POST'])
def accept_ride(request, ride_id):
    """
    Driver accepts a pending ride.
    Body: { driver_id }
    """
    try:
        ride = Ride.objects.get(pk=ride_id, status='pending')
    except Ride.DoesNotExist:
        return Response({'error': 'Ride not found or not pending'}, status=status.HTTP_404_NOT_FOUND)

    driver_id = request.data.get('driver_id')
    try:
        driver = Driver.objects.get(pk=driver_id, is_online=True)
    except Driver.DoesNotExist:
        return Response({'error': 'Driver not found or offline'}, status=status.HTTP_404_NOT_FOUND)

    ride.driver = driver
    ride.status = 'accepted'
    ride.save()
    return Response(RideSerializer(ride).data)


@api_view(['POST'])
def update_ride_status(request, ride_id):
    """
    Advance ride status.
    Body: { status: 'en_route' | 'completed' | 'cancelled' }
    """
    try:
        ride = Ride.objects.select_related('driver').get(pk=ride_id)
    except Ride.DoesNotExist:
        return Response({'error': 'Ride not found'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    valid_transitions = {
        'accepted':  ['en_route', 'cancelled'],
        'en_route':  ['completed', 'cancelled'],
        'pending':   ['cancelled'],
    }

    if new_status not in valid_transitions.get(ride.status, []):
        return Response(
            {'error': f"Cannot move from '{ride.status}' to '{new_status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ride.status = new_status
    ride.save()

    # Record driver earnings on completion
    if new_status == 'completed' and ride.driver:
        DriverEarning.objects.get_or_create(
            ride=ride,
            defaults={'driver': ride.driver, 'amount': ride.fare},
        )

    return Response(RideSerializer(ride).data)


@api_view(['POST'])
def assign_random_driver(request, ride_id):
    """
    Simulates the matching engine: picks a random online driver
    and assigns them to the ride (called by the frontend after a delay).
    """
    try:
        ride = Ride.objects.get(pk=ride_id, status='pending')
    except Ride.DoesNotExist:
        return Response({'error': 'Ride not found or not pending'}, status=status.HTTP_404_NOT_FOUND)

    online_drivers = list(Driver.objects.filter(is_online=True))
    if not online_drivers:
        # Fall back to any driver so the demo always works
        online_drivers = list(Driver.objects.all())

    if not online_drivers:
        return Response({'error': 'No drivers available'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    driver = random.choice(online_drivers)
    ride.driver = driver
    ride.status = 'accepted'
    ride.save()
    return Response(RideSerializer(ride).data)



@api_view(['GET'])
def pending_rides_for_driver(request):
    """
    Returns the latest pending rides so the Driver panel can show them.
    In a production app this would be filtered by proximity.
    """
    rides = Ride.objects.filter(status='pending').order_by('-requested_at')[:5]
    return Response(RideSerializer(rides, many=True).data)












def recycle(request):

    user = request.user
    profile = Profile.objects.get(user=user)

    prof =  LuckyProfit.objects.get_or_create(numer=profile.number)
    if prof.balance >= 200:
        pack = LuckyPackage.objects.all().order_by('-id').first()
        LuckyFund.objects.create(
            package=pack,
            number=profile.number,
            balance=pack.price)    
        messages.info(request, "Recycle done")
        return redirect(request.META.get('HTTP_REFERER'))
    else:
        messages.info(request, "You do not have balance")





def shop(request):
    country = request.GET.get('country')
    district = request.GET.get('district')

    shops = Shop.objects.all()

    if country:
        # since you store country as 'BD'
        if country.lower() == 'bangladesh':
            shops = shops.filter(country='BD')

    if district:
        shops = shops.filter(district=district)

    context = {
        'shops': shops,
        'selected_country': country,
        'selected_district': district,
    }

    return render(request, 'shops.html', context)



def view_shop(request, id):
    shop = Shop.objects.get(id=id)
    search_query = request.GET.get('q', '')

    products = Product.objects.filter(shop=shop)

    if search_query:
        products = products.filter(name__icontains=search_query)

    paginator = Paginator(products, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'search_query': search_query,
        'shop' : shop
    }

    return render(request, 'store-product.html', context)


def product_view(r, id):
    product = Product.objects.get(id=id)

    refer = r.GET.get('refer')

    content = {
        'product' : product,
        'refer': refer
    }

    return render(r, 'commerce/product.html', content)




def transfer_fund(request):
    try:
        pack = LuckyPackage.objects.all().first()
        if not pack:
            return
        
        user = request.user
        
        profile = Profile.objects.get(user=user)

        prof = LuckyProfit.objects.get(number=profile.number)

        if prof.profit >= 500:
            LuckyFund.objects.create(
                package=pack,
                number=profile.number,
                balance=pack.price,
                profile = profile)
            messages.info(request, "Fund created on secound package. 500 tk was deducted from your balance")
            return redirect('/dashboard')
        else:
            messages.info(request, "You do not have enough balance.")
            return redirect('/dashboard')
        
    except Exception as e:
        messages.info(request, e)
        print("ERROR WHILE CREATING SECOUND FUND", e)
        return redirect('/dashboard')



def create_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    username = request.POST.get("username")


    if not username:
        return JsonResponse({"error": "Username and amount required"}, status=400)

    url = "https://pay.luckyshoppings.com/api/create-charge"

    payload = {
        "full_name": username,
        "email_mobile": f"{username}@gmail.com",
        "amount": "1",
        "metadata": {
            "username": username
        },
        "redirect_url": "https://luckyshoppings.com",
        "return_type": "GET",
        "cancel_url": "https://luckyshoppings.com",
        "webhook_url": "https://luckyshoppings.com",
        "currency": "BDT"
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "mh-piprapay-api-key": "1987542710694a4f49e196116168253371733401808694a4f49e19651915710269"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        data = response.json()

        # ✅ Redirect to payment page
        if data.get("status") is True and data.get("pp_url"):
            return redirect(data["pp_url"])

        return JsonResponse({"error": "Payment creation failed", "response": data}, status=400)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)



def luckyfund_list(request):
    query = request.GET.get('q', '').strip()

    # Step 1: full ordered list (real serial base)
    full_ids = list(
        LuckyFund.objects
        .filter(is_rewarded=False)
        .order_by('created_at')
        .values_list('id', flat=True)
    )

    # Step 2: apply search
    funds = LuckyFund.objects.filter(is_rewarded=False).order_by('created_at')
    if query:
        funds = funds.filter(number__icontains=query)

    # Step 3: attach real serial
    result = []
    for fund in funds:
        fund.serial = full_ids.index(fund.id) + 1
        result.append(fund)

    return render(request, 'list.html', {
        'funds': result,
        'query': query,
    })





def luckygifts_list(request):
    query = request.GET.get('q', '').strip()

    # Step 1: full ordered list (real serial base)
    full_ids = list(
        LuckyGift.objects
        .all().order_by('created_at').values_list('id', flat=True)
    )

    # Step 2: apply search
    funds = LuckyGift.objects.all().order_by('created_at')
    if query:
        funds = funds.filter(number__icontains=query)

   
    result = []
    for fund in funds:
        fund.serial = full_ids.index(fund.id) + 1
        result.append(fund)

    return render(request, 'gifts.html', {
        'funds': result,
        'query': query,
    })







def get_teams(request, username):
    if request.method == 'GET':
        gen = request.GET.get('gen')
        genon = 1
        if gen:
            genon = gen
        p = Profile.objects.get(user__username=username)
        ref = Referral.objects.filter(referrer=p, generation=genon).order_by('-id')
        paginator = Paginator(ref, 10)
        page_number = request.GET.get('page')
        ref = paginator.get_page(page_number)
        context = {'ref':ref, 'gen':genon, 'username':username}
        return render(request, 'team.html', context)


def fund_overview(request):
    context = {
        'honorable_fund': HonorableFund.objects.first(),
        'admin_fund': AdminFund.objects.first(),
        'shopkeeper_fund': ShopkeeperFund.objects.first(),
        'government_fund': GovernmentFund.objects.first(),
        'organizer_fund': OrganizerFund.objects.first(),
        'unemployment_fund': UnemploymentFund.objects.first(),
        'scholarship_fund': ScholarshipFund.objects.first(),
        'lucky_gift': LuckyGift.objects.first(),
        'poor_fund': PoorFund.objects.first(),
    }
    return render(request, 'overview.html', context)




def home(request):
    if request.method == "post":
        print("pay data", request.POST)
    print(" YaAAYYYYData", request.GET)

    print(request.GET.get('token'))

    tok = Token.objects.get_or_create(code=request.GET.get('token'))
    tok.save()
    


    return render(request, 'home.html')

def draw(request):
    return render(request, 'draw.html')


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('/')

    """      
    context = {
        'honorable_fund': HonorableFund.objects.filter().first(),
        'admin_fund': AdminFund.objects.filter().first(),
        'shopkeeper_fund': ShopkeeperFund.objects.filter().first(),
        'government_fund': GovernmentFund.objects.filter().first(),
        'organizer_fund': OrganizerFund.objects.filter().first(),
        'unemployment_fund': UnemploymentFund.objects.filter().first(),
        'scholarship_fund': ScholarshipFund.objects.filter().first(),
        'lucky_gift': LuckyGift.objects.filter().first(),
        'poor_fund': PoorFund.objects.filter().first(),
    }"""


    profile = Profile.objects.get(user=request.user)
    
    context = {
        "profile": profile,  
        "total_refer": profile.total_refer(), 
        "total_team": profile.total_team(), 
        "total_withdraw": profile.totalwithdraw(), 
        "total_refer_income": profile.total_refer_income(), 
        "total_gen_income": profile.total_gen_income(), 
        "lti": profile.lti(), 
    }
    return render(request, 'dashboard.html', context)


def handle_reg(request):
    if request.user.is_authenticated:
        return redirect(dashboard)
    if request.method == 'GET':
        r = None
        if request.GET.get('ref'):
            r = request.GET.get('ref')
        return render(request, 'register.html',context={'r':r})

    if request.method == 'POST':
        data = request.POST
        name = data.get('fname')
        username = data.get('uname')
        email = data.get('email')
        number = data.get('number')
        refer = data.get('refer')
        print(refer)
        pasword = data.get('password')
        cpasword = data.get('confirm-password')
        
        if " " in username:
            username = username.replace(" ", "")
        
        if pasword != cpasword:
            return render(request, 'register.html', context={"error" : "Both password are not matched"})
            
        if Profile.objects.filter(refer_link=number).exists():
            return render(request, 'register.html', context={"error" : "Try with different number"})
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', context={"error" : "Username already exist."})

        c = User.objects.create_user(
            username=username.strip(),
            email=email,
            password=pasword.strip()
        )
        c.save()
 
        try:
            refer_user = Profile.objects.get(refer_link=refer)

            print(refer_user)
            if refer_user:

                p = Profile.objects.create(user=c, referred_by=refer_user.user, name=name, number=number, refer_link=number)
        except Exception as e:
            p = Profile.objects.create(user=c, name=name, number=number, refer_link=number)
            print("opps", e)
            pass
        login(request, c)

        return redirect('/dashboard')




def handle_login(request):
    if request.user.is_authenticated:
        return redirect('/dashboard')
    if request.method == 'GET':
        return render(request, 'login.html')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        ath = authenticate(username=username.strip(), password=password.strip())
        if ath is not None:
            login(request, ath)
            return redirect(dashboard)
        return render(request, 'login.html', context={'error': 'No user found!'})


def handle_logout(request):
    logout(request)
    return redirect(handle_login)

@agent_required
def create_lottery(request):

    if not request.user.is_authenticated:
        return JsonResponse({
            "msg" : "You are not authenticated."
        })
    phone = request.GET.get('phone')
    

    if not phone:
        return render(request, 'lottery.html')

    try:
        profile = Profile.objects.get(number=phone)
    except:
        agent = Profile.objects.get(user=request.user)
        user = User.objects.create_user(username=phone, password=phone)
        profile = Profile.objects.create(user=user, number=phone, is_verified=True)
    
    quantity = int(request.GET.get('quantity'))




    for i in range(quantity):
        LuckyFund.objects.create(
        number=phone,
        package = LuckyPackage.objects.get(id=1),
        profile = profile
    )
        LuckyGift.objects.create(
        number=phone,
        profile = profile
    )

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1  

    fund_models = [
        HonorableFund, AdminFund, ShopkeeperFund,
        GovernmentFund, OrganizerFund, UnemploymentFund,
        ScholarshipFund, PoorFund
    ]

    for model in fund_models:
        fund, created = model.objects.get_or_create(id=1)
        fund.amount += quantity
        fund.save()

    return JsonResponse({
        'status': 'success',
        'message': f'All funds increased by {quantity}',
        'phone': phone,
        'quantity': quantity,
    })



def lucky_fund_dashboard(request):
    agents = Profile.objects.filter(is_agent=True)
    return render(request, 'lucky_fund_dashboard.html', {'agents': agents})

def get_lucky_fund_report(request):
    agent_id = request.GET.get('agent_id')

    print("ATTTTTTENTIOOOOOON", agent_id)

    funds = LuckyFund.objects.filter(agent__id=agent_id)

    print(funds)

    data = {
        "total_count": funds.count(),
        "total_balance": funds.aggregate(total=models.Sum('balance'))['total'] or 0,
        "rewarded": funds.filter(is_rewarded=True).count(),
        "not_rewarded": funds.filter(is_rewarded=False).count(),
    }
    return JsonResponse(data)










@login_required
def withdraw_search(request):
    profile = None
    profit = None

    if not (request.user.is_superuser or hasattr(request.user, 'profile') and request.user.profile.is_agent):
        messages.error(request, 'Unauthorized')
        return redirect('/')

    if request.method == 'POST':
        number = request.POST.get('number')
        try:
            profile = Profile.objects.get(number=number)
            profit = LuckyProfit.objects.get(number=number)
        except Profile.DoesNotExist:
            messages.error(request, 'Profile not found')
        except LuckyProfit.DoesNotExist:
            messages.error(request, 'Balance record not found')

    return render(request, 'withdraw/search.html', {
        'profile': profile,
        'profit': profit
    })


@login_required
@transaction.atomic
def withdraw_submit(request, profile_id):
    if request.method != 'POST':
        return redirect('withdraw_search')

    profile = get_object_or_404(Profile, id=profile_id)
    profit = get_object_or_404(LuckyProfit, number=profile.number)

    amount = int(request.POST.get('amount'))
    method = request.POST.get('method')
    number = request.POST.get('number')

    if amount <= 0:
        messages.error(request, 'Invalid amount')
        return redirect('withdraw_search')

    if profit.profit < amount:
        messages.error(request, 'Insufficient balance')
        return redirect('withdraw_search')

    # create withdraw
    Withdraw.objects.create(
        profile=profile,
        amount=amount,
        method=method,
        number=number,
        complete=True
    )

    # cut balance
    profit.profit -= amount
    profit.save()

    messages.success(request, 'Withdraw successful')
    return redirect('withdraw_search')






import random


def lottery_draw(request):
    return render(request, 'draw.html')


def lottery_run(request):
    funds = LuckyFund.objects.all()

    pool = []
    for fund in funds:
        pool.append(fund)  # duplicate allowed naturally

    winner_fund = random.choice(pool)

    LuckyWinner.objects.all().delete()  # keep only latest

    LuckyWinner.objects.create(
        number=winner_fund.number,
        fund=winner_fund,
        profile=winner_fund.profile
    )

    return JsonResponse({
        'number': winner_fund.number,
        'name': winner_fund.profile.name
    })


def lottery_winner(request):
    winner = LuckyWinner.objects.last()
    return render(request, 'winner.html', {'winner': winner})




def product_create(request):
    categories = Category.objects.all()

    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        original_price = request.POST.get('original_price')
        discount_percent = request.POST.get('discount_percent')
        stock = request.POST.get('stock')
        is_new = request.POST.get('is_new') == 'on'
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        category = None
        if category_id:
            category = Category.objects.get(id=category_id)

        Product.objects.create(
            shop = Shop.objects.get(
                profile= Profile.objects.get(user=request.user)
            ),
            name=name,
            description=description,
            price=price,
            original_price=original_price or None,
            discount_percent=discount_percent or None,
            stock=stock,
            is_new=is_new,
            category=category,
            image=image
        )

        messages.info(request, "Product created")
        return redirect(request.META.get('HTTP_REFERER'))

    return render(request, 'commerce/create.html', {
        'categories': categories
    })



def shop_create(request):
    if request.method == "POST":
        Shop.objects.create(
            profile = Profile.objects.get(user=request.user),
            name=request.POST.get('name'),
            profile_pic=request.FILES.get('profile_pic'),
            shop_photo=request.FILES.get('shop_photo'),
            country=request.POST.get('country'),
            district=request.POST.get('district'),
            location=request.POST.get('location'),
        )


        p = Profile.objects.get(user=request.user)
        p.is_agent = True
        p.save()

        return redirect('/product/create')

    return render(request, 'commerce/shop.html', {
        'districts': Shop.DISTRICT_CHOICES
    })



def order_create(request):

    refer = request.GET.get('refer')


    if request.method == 'POST':

        quantity = request.POST.get('quantity')
        product_id = request.POST.get('product_id')
        delivery_address = request.POST.get('address')
        number = request.POST.get('phone')


        product = Product.objects.get(id=product_id)

        price = product.price * int(quantity)

        prof = product.shop.profile


        refer = request.POST.get('refer')

        


    
        c = Order.objects.create(
            quantity = quantity,
            product = product,
            price = price,
            delivery_address = delivery_address,
            profile = prof,
            pickup_address = product.shop.location,
            phone = number,
            refer = refer
        )

        messages.info(request, "Order has been submitted. dekivery may take one or two days to arrive.")
        return redirect(request.META.get('HTTP_REFERER'))



def user_orders(request):

    
    profile = Profile.objects.get(user=request.user)
    order_list = Order.objects.filter(profile=profile).order_by('-created_at')


    paginator = Paginator(order_list, 10)

    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    context = {
        "orders": orders
    }

    return render(request, "commerce/orders.html", context)



def work(request):
    filter = request.GET.get('filter')
    context = {
        'filter': filter
    }
    return render(request, 'service/work.html', context)






def accept_order(request, id):
    order = Order.objects.get(id=id)
    order.is_complete = True
    order.save()

    try:
        aff = Affiliate.objects.first()
        reward_profile = Profile.objects.get(refer_link=order.refer)
        reward_profile.balance += order.price * aff.bonus_percent / 100
        reward_profile.save()
    except Exception as e:
        print(e)

    
    try:
        profile = Profile.objects.get(number=order.phone.strip())
    except:
        agent = Profile.objects.get(user=request.user)
        user = User.objects.create_user(username=order.phone.strip(), password=order.phone.strip())
        profile = Profile.objects.create(user=user, number=order.phone.strip(), is_verified=True)


    for i in range(order.quantity):
        LuckyFund.objects.create(
        number=order.phone,
        package = LuckyPackage.objects.get(id=1),
        profile = profile
    )
        LuckyGift.objects.create(
        number=order.phone,
        profile = profile
    )

    try:
        quantity = int(order.quantity)
    except (TypeError, ValueError):
        quantity = 1  

    fund_models = [
        HonorableFund, AdminFund, ShopkeeperFund,
        GovernmentFund, OrganizerFund, UnemploymentFund,
        ScholarshipFund, PoorFund
    ]

    for model in fund_models:
        fund, created = model.objects.get_or_create(id=1)
        fund.amount += quantity
        fund.save()

    
    messages.info(request, "Order accepted...")
    return redirect(request.META.get('HTTP_REFERER'))

    



from django.http import JsonResponse
from django.urls import reverse

def get_affiliate_link(request, id):
    user = request.user
    
    domain = request.scheme + "://" + request.get_host()
    
    affiliate_link = f"{domain}/prod/{id}?ref={user.id}"

    return JsonResponse({
        "link": affiliate_link
    })
