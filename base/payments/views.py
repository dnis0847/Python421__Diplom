# views.py
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import View
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Payment
from courses.models import Course


class SimulatePaymentView(LoginRequiredMixin, View):
    login_url = 'users:login'

    def post(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)

        # Создаем запись о платеже
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            amount=course.price,
            status='pending'  # Начинаем с статуса "ожидание"
        )

        # Имитируем успешный или неудачный платеж
        # Получаем параметр из формы
        success = request.POST.get('success', 'true')
        if success == 'true':
            payment.status = 'success'
            payment.save()
            messages.success(request, 'Оплата успешно завершена! Для прохождения курса перейдите в личный кабинет.')
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, 'Оплата не удалась. Попробуйте снова.')

        # Перенаправляем пользователя на страницу курса
        return HttpResponseRedirect(reverse_lazy('courses:course_detail', kwargs={'pk': course.id}))

    def get(self, request, *args, **kwargs):
        # Если GET-запрос, перенаправляем на список курсов
        return HttpResponseRedirect(reverse_lazy('courses:courses'))

