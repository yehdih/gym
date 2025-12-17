from django.contrib import admin
from .models import Member, Payment

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone_number', 'monthly_fee', 'validity_end_date', 'is_active', 'is_expired']
    search_fields = ['full_name', 'phone_number']
    list_filter = ['is_active', 'date_joined', 'validity_end_date']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'payment_date', 'validity_end']
    search_fields = ['member__full_name', 'member__phone_number']
    list_filter = ['payment_date']
