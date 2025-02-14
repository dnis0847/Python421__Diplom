from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Ожидание'), ('success', 'Успех'), ('failed', 'Ошибка платежа')],
        default='pending'
    )
    payment_id = models.CharField(max_length=255, blank=True, null=True)  # ID платежа из платежной системы
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.status})"