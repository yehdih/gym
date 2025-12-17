from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.db import IntegrityError, transaction

from .models import Member, Payment
from .forms import MemberForm, PaymentForm

def home(request):
    """Dashboard with statistics"""
    now = timezone.now()

    total_members = Member.objects.filter(is_active=True).count()
    active_members = Member.objects.filter(
        is_active=True,
        validity_end_date__gt=now
    ).count()
    expired_members = Member.objects.filter(
        is_active=True,
        validity_end_date__lte=now
    ).count()
    
    # Members paid this month — استبعد مدفوعات الأعضاء غير النشطين
    paid_this_month = Payment.objects.filter(
        payment_date__year=now.year,
        payment_date__month=now.month,
        member__is_active=True
    ).count()
    
    context = {
        'total_members': total_members,
        'active_members': active_members,
        'expired_members': expired_members,
        'paid_this_month': paid_this_month,
    }
    return render(request, 'gym/home.html', context)

def add_member(request):
    """Add new member with initial payment"""
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # احفظ العضو ثم أنشئ دفعة أولية
                    member = form.save(commit=False)
                    member.is_active = True
                    member.save()

                    # أنشئ دفعة أولية (موديل Payment سيضبط validity تلقائيًا)
                    Payment.objects.create(
                        member=member,
                        amount=member.monthly_fee
                    )

                messages.success(request, f'تمت إضافة العضو {member.full_name} بنجاح!')
                return redirect('member_profile', pk=member.pk)
            except IntegrityError as e:
                # احتمال تكرار رقم الهاتف رغم التحقق (سببه تسابق أو قيد قاعدة بيانات)
                messages.error(request, 'خطأ: لا يمكن إضافة العضو — رقم الهاتف مستخدم بالفعل.')
                return render(request, 'gym/add_member.html', {'form': form})
        else:
            # إذا الفورم غير صالح، سيعيد العرض مع رسائل التحقق
            return render(request, 'gym/add_member.html', {'form': form})
    else:
        form = MemberForm()
    
    return render(request, 'gym/add_member.html', {'form': form})


def must_pay_list(request):
    """List of members with expired payments"""
    search_query = request.GET.get('search', '')
    
    members = Member.objects.filter(
        is_active=True,
        validity_end_date__lte=timezone.now()
    )
    
    if search_query:
        members = members.filter(
            Q(full_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    context = {
        'members': members,
        'search_query': search_query,
    }
    return render(request, 'gym/must_pay_list.html', context)


def member_profile(request, pk):
    """Member profile with payment history and add payment form"""
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.member = member
            # لا تحتاج لتعيين validity هنا لأن save() في الموديل يفعل ذلك
            payment.save()
            messages.success(request, 'تمت إضافة الدفعة بنجاح!')
            return redirect('member_profile', pk=pk)
        else:
            # فورم غير صالح - أعِد العرض مع الأخطاء
            payments = member.payments.all()
            return render(request, 'gym/member_profile.html', {
                'member': member,
                'payments': payments,
                'form': form,
            })
    else:
        # Pre-fill amount with member's monthly fee
        form = PaymentForm(initial={'amount': member.monthly_fee})
    
    payments = member.payments.all()
    
    context = {
        'member': member,
        'payments': payments,
        'form': form,
    }
    return render(request, 'gym/member_profile.html', context)


def paid_this_month(request):
    """List of members who paid in current month"""
    now = timezone.now()
    
    payments = Payment.objects.filter(
        payment_date__year=now.year,
        payment_date__month=now.month,
        member__is_active=True   # استبعد مدفوعات الأعضاء غير النشطاء
    ).select_related('member')
    
    context = {
        'payments': payments,
        'current_month': now.strftime('%B %Y'),
    }
    return render(request, 'gym/paid_this_month.html', context)


def all_members(request):
    """List all members with filters"""
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    members = Member.objects.filter(is_active=True)
    
    # Apply status filter
    if status_filter == 'active':
        members = members.filter(validity_end_date__gt=timezone.now())
    elif status_filter == 'expired':
        members = members.filter(validity_end_date__lte=timezone.now())
    
    # Apply search filter
    if search_query:
        members = members.filter(
            Q(full_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    context = {
        'members': members,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'gym/all_members.html', context)


def delete_member(request, pk):
    """Delete a member (soft delete by setting is_active to False)"""
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        member_name = member.full_name
        # Soft delete - just mark as inactive
        member.is_active = False
        member.save()

        # ملاحظة: نحتفظ بسجلات المدفوعات في قاعدة البيانات (أفضل للاحتفاظ بالتاريخ).
        # إذا أردت حذف المدفوعات فعليًا، فكِّر جيدًا قبل إلغاء التعليق على السطر التالي:
        # member.payments.all().delete()

        messages.success(request, f'تم حذف العضو {member_name} بنجاح!')
        return redirect('all_members')
    
    # If GET request, show confirmation page
    context = {
        'member': member,
    }
    return render(request, 'gym/delete_member.html', context)
