from django.urls import path
from . import views

urlpatterns = [
    # ログイン・ログアウト
    path('login/', views.voter_login, name='login'),
    path('logout/', views.voter_logout, name='logout'),

    # 投票者のマイページ
    path('dashboard/', views.dashboard, name='dashboard'),

    # 選挙一覧
    path('election_list/', views.election_list, name='election_list'),

    # 投票のステップページ
    path('vote/<int:election_id>/', views.vote_page, name='vote_page'),

    # 投票確認
    path('vote_confirm/<int:election_id>/', views.vote_confirm, name='vote_confirm'),

    # 投票完了
    path('vote_complete/', views.vote_complete, name='vote_complete'),
    
]
