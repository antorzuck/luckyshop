from django.shortcuts import render, redirect
from .models import * 
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse


def home(request):
    return render(request, 'home.html')

def dashboard(request):
    return render(request, 'dashboard.html')


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
            print("ahhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
            refer_user = Profile.objects.get(refer_link=refer)

            print(refer_user)
            print("xxxxxxxxxxxxxxx")
            if refer_user:
                print("yes")

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



from django.http import JsonResponse
from .models import (
    HonorableFund, AdminFund, ShopkeeperFund,
    GovernmentFund, OrganizerFund, UnemploymentFund,
    ScholarshipFund, LuckyGift, PoorFund
)

def create_lottery(request):
    phone = request.GET.get('phone')
    quantity = request.GET.get('quantity')

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1  # fallback if quantity missing or invalid

    # list of all your fund models
    fund_models = [
        HonorableFund, AdminFund, ShopkeeperFund,
        GovernmentFund, OrganizerFund, UnemploymentFund,
        ScholarshipFund, LuckyGift, PoorFund
    ]

    for model in fund_models:
        fund, created = model.objects.get_or_create(id=1)  # single global fund record
        fund.amount += quantity
        fund.save()

    return JsonResponse({
        'status': 'success',
        'message': f'All funds increased by {quantity}',
        'phone': phone,
        'quantity': quantity,
    })

