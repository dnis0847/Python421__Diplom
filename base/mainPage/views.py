from django.views.generic import TemplateView
# from .models import Subscriber  # Импортируем модель Subscriber
from django.db.models import Count
from django.urls import reverse
from django.db import DatabaseError
from .models import HeroBlock, JoinOurCommunity, SubscriptionBenefit, FAQ
from courses.models import Course

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
        
        # # Все курсы
        # courses = Course.objects.all()[:6]
        # for course in courses:
        #     # Добавляем количество уроков
        #     course.lessons_count = course.lessons.count()
        #     # Добавляем количество студентов
        #     course.students_count = course.progresses.count()
        #     # Формируем ссылку на страницу детального просмотра курса
        #     course.detail_url = reverse('users:course_detail', kwargs={'pk': course.pk})
        
        # context['courses'] = courses
        
        # Популярные курсы
        popular_courses = Course.objects.annotate(
            students_count=Count('progresses')
        ).order_by('-students_count')[:6]
        for course in popular_courses:
            # Добавляем количество уроков
            course.lessons_count = course.lessons.count()
            # Формируем ссылку на страницу детального просмотра курса
            course.detail_url = reverse('courses:course_detail', kwargs={'pk': course.pk})
        
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