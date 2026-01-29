from django.contrib import admin
from .models import Administrator
from .forms import AdministratorAdminForm

# Register your models here.

admin.site.register(Administrator)

@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    form = AdministratorAdminForm