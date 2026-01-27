from django.contrib import admin
from .models import PersonalInfo, Voter, VoteStatus

# Register your models here.

admin.site.register(PersonalInfo)
admin.site.register(Voter)
admin.site.register(VoteStatus)