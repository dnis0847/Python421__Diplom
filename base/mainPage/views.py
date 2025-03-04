from django.views.generic import TemplateView
from django.db.models import Count
from django.urls import reverse
from django.db import DatabaseError
from .models import HeroBlock, JoinOurCommunity, SubscriptionBenefit, FAQ, Subscriber
from courses.models import Course, Category
from django.db.models import Avg, Value, FloatField
from django.db.models import Count
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.shortcuts import redirect

import uuid


class IndexView(TemplateView):
    template_name = 'mainPage/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Курсы для главной страницы
        context['title'] = 'Learnify | Главная'
        context['heroBlock'] = HeroBlock.objects.first() or {}
        context['joinOurCommunity'] = JoinOurCommunity.objects.first() or {}
        context['subscriptionBenefit'] = SubscriptionBenefit.objects.all()[:5]
        context['faqs'] = FAQ.objects.all()[:10]
        context['categorys'] = Category.objects.all()

        # Популярные курсы
        popular_courses = Course.objects.annotate(
            students_count=Count('progresses'),
            average_rating=Coalesce(
                Avg('reviews__rating'), Value(0), output_field=FloatField())
        ).order_by('-students_count')[:6]

        for course in popular_courses:
            course.lessons_count = course.lessons.count()
            course.detail_url = reverse(
                'courses:course_detail', kwargs={'pk': course.pk})
            course.average_rating = course.average_rating or 0

        context['popular_courses'] = popular_courses

        # Добавляем сообщение об успешной подписке, если оно есть
        if 'subscription_success' in self.request.session:
            context['subscription_success'] = self.request.session.pop(
                'subscription_success')

        return context

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        category_name = request.POST.get('category')

        if not email:
            messages.error(request, "Пожалуйста, укажите email.")
            # Исправлено на правильное имя URL
            return redirect('mainPage:home')

        try:
            # Проверяем, существует ли уже такой email
            subscriber = Subscriber.objects.filter(email=email).first()

            if subscriber:
                if subscriber.is_active:
                    messages.info(
                        request, "Вы уже подписаны на нашу рассылку.")
                else:
                    # Если подписка была деактивирована, активируем её снова
                    subscriber.is_active = True
                    subscriber.save()
                    messages.success(
                        request, "Ваша подписка успешно возобновлена!")
            else:
                # Получаем категорию, если она была выбрана
                category = None
                if category_name and category_name != 'all':
                    category = Category.objects.filter(
                        name=category_name).first()

                # Получаем IP-адрес пользователя
                ip_address = self.get_client_ip(request)

                # Генерируем токен подтверждения
                confirmation_token = uuid.uuid4().hex

                # Создаем нового подписчика
                Subscriber.objects.create(
                    email=email,
                    category=category,
                    ip_address=ip_address,
                    confirmation_token=confirmation_token
                )

                # Здесь можно добавиить отправку email с подтверждением подписки
                # send_confirmation_email(email, confirmation_token)

                # Сохраняем сообщение об успехе в сессию
                request.session['subscription_success'] = "Спасибо за подписку! Проверьте вашу почту для подтверждения."

            # Исправлено на правильное имя URL
            return redirect('mainPage:home')

        except Exception as e:
            messages.error(request, f"Произошла ошибка при подписке: {str(e)}")
            # Исправлено на правильное имя URL
            return redirect('mainPage:home')

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AboutView(TemplateView):
    template_name = 'mainPage/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Learnify | О нас'
        return context


class ContactsView(TemplateView):
    template_name = 'mainPage/contacts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Learnify | Контакты'
        return context
