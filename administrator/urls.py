from django.urls import path
from . import views

app_name="administrator"

urlpatterns = [
   path('login/', views.AdministratorLoginView.as_view(), name='login'),
   path('logout/', views.AdministratorLogoutView.as_view(), name='logout'),
   path('top/', views.AdministratorMenuView.as_view(), name='main_menu'),
   path('voter/create/', views.VoterCreateView.as_view(), name='voter_create'),
   path('voter/create/success/', views.VoterCreateSuccessView.as_view(), name='voter_create_success'),
   path("voter/delete/list/", views.VoterDeleteListView.as_view(), name='voter_delete_list'),
   path('voter/delete/<int:pk>/', views.VoterDeleteView.as_view(), name='voter_delete'),
   path('election/create/', views.ElectionCreateView.as_view(), name='election_create'),
   #path('election/create/confirm/', views.ElectionConfirmView.as_view(), name='election_create_confirm'),
   path('election/view/', views.ElectionListView.as_view(), name='election_list'),
   path('election/<int:pk>/', views.ElectionDetailView.as_view(), name='election_detail'),
   path("election/<int:pk>/edit/", views.ElectionUpdateView.as_view(), name="election_edit"),
   #path('election/<int:pk>/candidate/add/', views.CandidateCreateView.as_view(), name='candidate_add'),
   path("election/<int:election_id>/result/", views.ElectionResultView.as_view(), name="election_result")

]
