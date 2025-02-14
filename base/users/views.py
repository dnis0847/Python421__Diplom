# users/views.py
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, logout
from .forms import RegistrationForm, LoginForm
from django.shortcuts import redirect

class RegisterView(FormView):
    template_name = 'users/registration.html'
    form_class = RegistrationForm
    # Перенаправление после успешной регистрации
    success_url = reverse_lazy('courses:courses')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Learnify | Регистрация'
        return context

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class UserLoginView(LoginView):
    template_name = 'users/login.html'
    form_class = LoginForm

    def get_success_url(self):
        return reverse_lazy('courses:courses')


def custom_logout(request):
    logout(request)
    return redirect('mainPage:home')
