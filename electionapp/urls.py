from django.urls import path
from . import views

app_name="electionapp"

urlpatterns = [
   path('', views.IndexView.as_view(), name='Index'),
]
