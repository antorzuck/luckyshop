from django.shortcuts import render, redirect, get_object_or_404
from .models import * 
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from .decor import agent_required 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction


def home(request):
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
        user = User.objects.create(username=phone, password=phone)
        profile = Profile.objects.create(user=user, number=phone, is_verified=True)
    
    quantity = int(request.GET.get('quantity'))




    for i in range(quantity):
        LuckyFund.objects.create(
        number=phone,
        package = LuckyPackage.objects.get(id=1),
        profile = profile
    )

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1  

    fund_models = [
        HonorableFund, AdminFund, ShopkeeperFund,
        GovernmentFund, OrganizerFund, UnemploymentFund,
        ScholarshipFund, LuckyGift, PoorFund
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