from django.db import models
from django.utils import timezone
from datetime import timedelta

class Member(models.Model):
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, unique=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    date_joined = models.DateTimeField(auto_now_add=True)
    validity_end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.full_name
    
    @property
    def is_expired(self):
        if not self.validity_end_date:
            return True
        return timezone.now() > self.validity_end_date
    
    @property
    def days_remaining(self):
        if not self.validity_end_date:
            return 0
        delta = self.validity_end_date - timezone.now()
        return max(0, delta.days)


class Payment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    validity_start = models.DateTimeField(null=True, blank=True)
    validity_end = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.member.full_name} - {self.payment_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        # إذا لم تُعطَ تواريخ الصلاحية فحددها آليًا
        if not self.validity_start:
            now = timezone.now()
            # إذا كان للعضو صلاحية فعّالة فتمدد من نهاية صلاحية العضو
            if self.member.validity_end_date and self.member.validity_end_date > now:
                self.validity_start = self.member.validity_end_date
            else:
                self.validity_start = now
            
            self.validity_end = self.validity_start + timedelta(days=30)
        
        super().save(*args, **kwargs)
        
        # بعد حفظ الدفعة حدّث صلاحيّة العضو
        # (هذا يحفظ عضوك ويضمن أن validity_end_date محدثة)
        self.member.validity_end_date = self.validity_end
        self.member.save()
