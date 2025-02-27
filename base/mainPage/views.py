from django.views.generic import TemplateView
# from .models import Subscriber  # Импортируем модель Subscriber
from django.db.models import Count
from django.urls import reverse
from django.db import DatabaseError
from .models import HeroBlock, JoinOurCommunity, SubscriptionBenefit, FAQ
from courses.models import Course
from django.db.models import Avg, Value, FloatField
from django.db.models import Count
from django.db.models.functions import Coalesce

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

        # Популярные курсы
        popular_courses = Course.objects.annotate(
            students_count=Count('progresses'),
            average_rating=Coalesce(Avg('reviews__rating'), Value(0), output_field=FloatField())
        ).order_by('-students_count')[:6]

        for course in popular_courses:
            course.lessons_count = course.lessons.count()
            course.detail_url = reverse('courses:course_detail', kwargs={'pk': course.pk})
            course.average_rating = course.average_rating or 0

        context['popular_courses'] = popular_courses

        return context


    # def post(self, request, *args, **kwargs):
    #     email = request.POST.get('email')  # Получаем email из формы
    #     if email:
    #         # Сохраняем email в базу данных
    #         Subscriber.objects.create(email=email)
    #         return redirect('success_page')  # Перенаправляем на страницу успеха
    #     else:
    #         return HttpResponse("Email не указан!", status=400)
    
    
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