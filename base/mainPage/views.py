from django.views.generic import TemplateView
# from .models import Subscriber  # Импортируем модель Subscriber
from .models import HeroBlock, JoinOurCommunity, SubscriptionBenefit, FAQ
from courses.models import Course


class IndexView(TemplateView):
    template_name = 'mainPage/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = 'Learnify | Главная'
        context['heroBlock'] = HeroBlock.objects.first()
        context['joinOurCommunity'] = JoinOurCommunity.objects.first()
        context['subscriptionBenefit'] = SubscriptionBenefit.objects.all()
        context['faqs'] = FAQ.objects.all()
        context['courses'] = Course.objects.all()[:6]

        return context

    # def post(self, request, *args, **kwargs):
    #     email = request.POST.get('email')  # Получаем email из формы
    #     if email:
    #         # Сохраняем email в базу данных
    #         Subscriber.objects.create(email=email)
    #         return redirect('success_page')  # Перенаправляем на страницу успеха
    #     else:
    #         return HttpResponse("Email не указан!", status=400)




