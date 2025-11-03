
from django.db import models
from django.contrib.auth.models import User


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


class LuckyFund(BaseModel):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='funding')
    package = models.ForeignKey(LuckyPackage, on_delete=models.CASCADE, related_name='pack')
    balance = models.IntegerField(default=00)
    is_rewarded = models.BooleanField(default=False)

    def __str__(self):
        return f'funding by {str(self.profile.name)} on {str(self.package.name)}'


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






