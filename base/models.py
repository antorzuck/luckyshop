
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

class LuckyPackage(BaseModel):
    name = models.CharField(max_length=50)
    price = models.IntegerField(default=0)


    def __str__(self):
        return self.name

 
class LuckyFund(BaseModel):
    number = models.CharField(max_length=20)
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
    amount = models.IntegerField(default=0)

    def __str__(self):
        return f'Collection is {str(self.amount)}'

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







def transfer_fund_auto(pid, number):
    print("transfering the fund....")
    pack = LuckyPackage.objects.filter(id__gt=pid)[0]

    try:
        LuckyFund.objects.create(package=pack,  number=number, balance=pack.price)
    except Exception as e:
        print("arey buij", e)












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
