
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class BaseModel(models.Model):
    """A simple reusable base model for all apps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True 
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.__class__.__name__} (id={self.pk})"
from django.db import models


class Shop(BaseModel):


    COUNTRY_CHOICES = [
        ('BD', 'Bangladesh'),
    ]


    DISTRICT_CHOICES = [
        ('Dhaka', 'Dhaka'),
        ('Chattogram', 'Chattogram'),
        ('Khulna', 'Khulna'),
        ('Rajshahi', 'Rajshahi'),
        ('Sylhet', 'Sylhet'),
        ('Barishal', 'Barishal'),
        ('Rangpur', 'Rangpur'),
    ]

    name = models.CharField(max_length=255)

    profile_pic = models.ImageField(
        upload_to='shops/profile_pics/',
        blank=True,
        null=True
    )

    shop_photo = models.ImageField(
        upload_to='shops/photos/',
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=5,
        choices=COUNTRY_CHOICES,
        default='BD'
    )

    district = models.CharField(
        max_length=50,
        choices=DISTRICT_CHOICES
    )

    location = models.CharField(
        max_length=255,
        help_text="Shop address / area"
    )

    google_map_link = models.URLField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name



class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, null=True, blank=True)
    number = models.CharField(max_length=50)
    balance = models.FloatField(default=00)
    shopping_balance = models.IntegerField(default=0)
    refer_link = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)
    reset_code = models.CharField(max_length=100, null=True, blank=True)
    referred_by = models.ForeignKey(User, related_name='teams', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user.username)


    def total_refer(self):
        return Referral.objects.filter(referrer=self, generation=1).count()

    def total_team(self):
        return Referral.objects.filter(referrer=self).count()
        
    def totalwithdraw(self):
        w = Withdraw.objects.filter(profile=self)
        money = sum([i.amount for i in w])
        
        print(money)
        return money
        
        
    
    def total_refer_income(self):
        tf = Referral.objects.filter(referrer=self, generation=1).count()
        return 10 * tf


    def total_gen_income(self):
      
        referrals = Referral.objects.filter(referrer=self, generation__lte=25)
        generation_counts = {i: 0 for i in range(1, 26)}
        
        for referral in referrals:
            generation_counts[referral.generation] += 1
        
        multipliers = {
        1: 2,
    2: 2, 3: 2, 4: 2, 5: 2,
    6: 2, 7: 2, 8: 2, 9: 2, 10: 2,
    11: 2, 12: 2, 13: 2, 14: 2, 15: 2,
    16: 2, 17: 2, 18: 2, 19: 2, 20: 2,
    21: 2, 22: 2, 23: 2, 24: 2, 25: 2,
            }
        sums = sum(generation_counts[g] * multipliers[g] for g in generation_counts)

        return sums
        
    def lti(self):
        if self.balance == 0:
            return 00
        referrals = Referral.objects.filter(referrer=self, generation__lte=25)
        generation_counts = {i: 0 for i in range(1, 26)}
        
        for referral in referrals:
            generation_counts[referral.generation] += 1
        
        multipliers = {
            1: 100,
    2: 2, 3: 2, 4: 2, 5: 2,
    6: 2, 7: 2, 8: 2, 9: 2, 10: 2,
    11: 2, 12: 2, 13: 2, 14: 2, 15: 2,
    16: 2, 17: 2, 18: 2, 19: 2, 20: 2,
    21: 2, 22: 2, 23: 2, 24: 2, 25: 2,
                }
        sums = sum(generation_counts[g] * multipliers[g] for g in generation_counts)
        return sums


class LuckyPackage(BaseModel):
    name = models.CharField(max_length=50)
    price = models.IntegerField(default=0)
    reward = models.IntegerField(default=0)


    def __str__(self):
        return self.name

class LuckyFund(BaseModel):
    number = models.CharField(max_length=20)
    agent = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='fund_agent', null=True, blank=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='lucky_funding')
    package = models.ForeignKey(LuckyPackage, on_delete=models.CASCADE, 
    related_name='pack',
    null=True,
    blank=True
    )
    balance = models.IntegerField(default=00)
    is_rewarded = models.BooleanField(default=False)

    def __str__(self):
        return f'funding by {str(self.number)} on {str(self.package.name)}'

class LuckyProfit(BaseModel):
    number = models.CharField(max_length=20)
    invest = models.IntegerField(default=1)
    profit = models.IntegerField(default=1)

    def __str__(self):
        return self.number
class HonorableFund(BaseModel):
    amount = models.IntegerField(default=0)

    def __str__(self):
        return f'Collection is {str(self.amount)}'

class AdminFund(BaseModel):
    amount = models.IntegerField(default=0)

    def __str__(self):
        return f'Collection is {str(self.amount)}'

class ShopkeeperFund(BaseModel):
    amount = models.IntegerField(default=0)

    def __str__(self):
        return f'Collection is {str(self.amount)}'


class GovernmentFund(BaseModel):
    amount = models.IntegerField(default=0)

    def __str__(self):
        return f'Collection is {str(self.amount)}'


class OrganizerFund(BaseModel):
    amount = models.IntegerField(default=0)

    def __str__(self):
        return f'Collection is {str(self.amount)}'


class UnemploymentFund(BaseModel):
    amount = models.IntegerField(default=0)

    def __str__(self):
        return f'Collection is {str(self.amount)}'


class ScholarshipFund(BaseModel):
    amount = models.IntegerField(default=0)

    def __str__(self):
        return f'Collection is {str(self.amount)}'


class LuckyGift(BaseModel):
    
    number = models.CharField(max_length=20)
    agent = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='gifts_agent', null=True, blank=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='lucky_gifts')

    def __str__(self):
        return f'{str(self.number)}'

class PoorFund(BaseModel):
    amount = models.IntegerField(default=0)

    def __str__(self):
        return f'Collection is {str(self.amount)}'




class packageSetting(BaseModel):
    current_serial = models.IntegerField(default=1)
    increase = models.IntegerField(default=1)
    package = models.ForeignKey(LuckyPackage, on_delete=models.CASCADE, null=True, blank=True)
  
    def __str__(self):
        return self.package.name





"""

def transfer_fund_auto(pid, number):
    print("transfering the fund....")
    pack = LuckyPackage.objects.filter(id__gt=pid)[0]

    try:
        LuckyFund.objects.create(package=pack,  number=number, balance=pack.price)
    except Exception as e:
        print("arey buij", e)

"""


class Referral(models.Model):
    referrer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='referrals_made')
    referred_user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='referrals_received')
    generation = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.referrer} referred {self.referred_user} (Generation {self.generation})"




@receiver(post_save, sender=Profile)
def create_referral(sender, instance, created, **kwargs):
    print("i just fenned")
    if not created and instance.is_verified:
        referrer_user = instance.referred_by

        reward = {
    1: 100,
    2: 2, 3: 2, 4: 2, 5: 2,
    6: 2, 7: 2, 8: 2, 9: 2, 10: 2,
    11: 2, 12: 2, 13: 2, 14: 2, 15: 2,
    16: 2, 17: 2, 18: 2, 19: 2, 20: 2,
    21: 2, 22: 2, 23: 2, 24: 2, 25: 2,
    }
        

        generation = 1  # Initialize generation counter

        while referrer_user and generation <= 25:
            try:
                referrer_profile = Profile.objects.get(user=referrer_user)
            except Profile.DoesNotExist:
                break  # No valid referrer profile, stop the loop

            # Create a referral record if not exists
            referral, created = Referral.objects.get_or_create(
                referrer=referrer_profile,
                referred_user=instance,
                generation=generation
            )

            if created:
                # Update the balance for the current generation
                referrer_profile.balance += reward[generation]
                referrer_profile.save()

            # Move up one generation
            referrer_user = referrer_profile.referred_by

            # Increment generation counter
            generation += 1






"""

@receiver(post_save, sender=LuckyFund)
def giving_reward(sender, instance, created, **kwargs):

    if not LuckyProfit.objects.filter(number=instance.number).exists():
        LuckyProfit.objects.create(number=instance.number)
    
    if created:
        try:
            ff = LuckyFund.objects.filter(package=instance.package, is_rewarded=False).exclude(id=instance.id).order_by('-id')
            xxx = packageSetting.objects.get(package=instance.package)
            get_rwrd_id = ff[xxx.current_serial]
            fx = LuckyFund.objects.get(id=get_rwrd_id.id)
            fx.balance = fx.balance + instance.package.price
            fx.is_rewarded = True
            fx.save()
            xxx.current_serial = xxx.current_serial + xxx.increase
            xxx.save()

            pro = LuckyProfit.objects.get(number=get_rwrd_id.number)
            print("this nigga", pro)
            pro.invest = pro.invest + instance.package.price 
            pro.profit = pro.profit + instance.package.price
            pro.save()
            id = instance.package.id

            transfer_fund(pid=id, number=get_rwrd_id.number)
            print("fun called")
        except Exception as e:
            print(e, "while rewqrd")
            if not packageSetting.objects.filter(package=instance.package).exists():
                packageSetting.objects.create(package=instance.package)

"""

class FundSettings(BaseModel):
    number = models.IntegerField(default=1)


from django.db.models import Count, F




@receiver(post_save, sender=LuckyFund)
def giving_reward(sender, instance, created, **kwargs):

    LuckyProfit.objects.get_or_create(number=instance.number)
    
    fund_setting_number = FundSettings.objects.filter().first()

    if not created:
        return

    try:
        # STEP 1: numbers having 2+ funds in this package
        eligible_numbers = (
            LuckyFund.objects
            .filter(package=instance.package)
            .values('number')
            .annotate(total=Count('id'))
            .filter(total__gte=fund_setting_number.number)
            .values_list('number', flat=True)
        )

        if not eligible_numbers:
            return

        # STEP 2: pick OLDEST fund (bottom one) per number
        ff = []
        for num in eligible_numbers:
            fund = (
                LuckyFund.objects
                .filter(
                    package=instance.package,
                    number=num,
                    is_rewarded=False
                )
                .exclude(id=instance.id)
                .order_by('id')  
                .first()
            )
            if fund:
                ff.append(fund)

        if not ff:
            return

        # STEP 3: serial logic (unchanged)
        setting, _ = packageSetting.objects.get_or_create(
            package=instance.package,
            defaults={'current_serial': 0, 'increase': 1}
        )

        if setting.current_serial >= len(ff):
            return

        winner_fund = ff[setting.current_serial]

        # STEP 4: get FIRST 2 fund IDs (OLDEST)
        reward_fund_ids = list(
            LuckyFund.objects
            .filter(
                package=instance.package,
                number=winner_fund.number,
                is_rewarded=False
            )
            .order_by('id')
            .values_list('id', flat=True)[:fund_setting_number.number]
        )

        if len(reward_fund_ids) < fund_setting_number.number:
            return
 
        # STEP 5: reward (balance added ONCE)
        winner_fund.balance += instance.package.price
        winner_fund.save()

        # mark BOTH funds rewarded (NO SLICE HERE)
        LuckyFund.objects.filter(id__in=reward_fund_ids).update(is_rewarded=True)


        # update serial
        setting.current_serial += setting.increase
        setting.save()

        # STEP 6: profit
        pro = LuckyProfit.objects.get(number=winner_fund.number)
        pro.invest += instance.package.price
        pro.profit += instance.package.reward
        pro.save()
        
        """

    
        transfer_fund_auto(
            pid=instance.package.id,
            number=winner_fund.number
        )

        print(
            f"reward given to {winner_fund.number}, "
            f"funds={[f.id for f in reward_funds]}"
        )"""

    except Exception as e:
        print(e, "while reward")

def transfer_fund_auto(pid, number):
    print("transfering the fund....")
    try:
        pack = LuckyPackage.objects.filter(id__gt=pid).order_by('id').first()
        if not pack:
            return

        LuckyFund.objects.create(
            package=pack,
            number=number,
            balance=pack.price
        )
    except Exception as e:
        print("arey buij", e)






class Withdraw(BaseModel):
    amount = models.IntegerField(default=0)
    method = models.CharField(max_length=100)
    profile = models.ForeignKey(Profile, related_name='cashout', on_delete=models.CASCADE)
    number = models.CharField(max_length=100)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return self.number


class LuckyWinner(BaseModel):
    number = models.CharField(max_length=20)
    fund = models.ForeignKey(LuckyFund, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return self.number