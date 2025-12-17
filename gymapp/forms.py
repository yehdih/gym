from django import forms
from django.core.exceptions import ValidationError
from .models import Member, Payment

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['full_name', 'phone_number', 'monthly_fee']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control apple-input',
                'placeholder': 'Enter full name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control apple-input',
                'placeholder': 'Enter phone number'
            }),
            'monthly_fee': forms.NumberInput(attrs={
                'class': 'form-control apple-input',
                'placeholder': 'Enter monthly fee',
                'step': '0.01'
            }),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        qs = Member.objects.filter(phone_number=phone, is_active=True)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('يوجد بالفعل عضو مسجّل بنفس رقم الهاتف.')
        return phone

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment amount',
                'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional notes',
                'rows': 3
            }),
        }

    # لا نعيّن تواريخ هنا لأن save() في الموديل يتعامل معها تلقائيًا
