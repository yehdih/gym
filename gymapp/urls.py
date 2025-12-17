from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add-member/', views.add_member, name='add_member'),
    path('must-pay/', views.must_pay_list, name='must_pay_list'),
    path('member/<int:pk>/', views.member_profile, name='member_profile'),
    path('member/<int:pk>/delete/', views.delete_member, name='delete_member'),
    path('paid-this-month/', views.paid_this_month, name='paid_this_month'),
    path('all-members/', views.all_members, name='all_members'),
]