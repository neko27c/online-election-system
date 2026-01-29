from django.contrib import admin
from .models import Administrator
from .forms import AdministratorAdminForm

# Register your models here.

@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    form = AdministratorAdminForm