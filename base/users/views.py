# Стандартные библиотеки Python
# from typing import Optional
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, FormView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Prefetch
from django.core.cache import cache
from django.http import JsonResponse
import markdown
from pygments.formatters import HtmlFormatter
from django.utils import timezone

# Локальные модули проекта
from .forms import RegistrationForm, LoginForm
from courses.models import Course, Lesson, Test, Question, Answer
from payments.models import Payment
from progress.models import Progress
from users.models import Profile
from .services import get_user_courses_with_progress


class RegisterView(FormView):
    """
    Представление для регистрации нового пользователя.
    После успешной регистрации пользователь автоматически авторизуется
    и перенаправляется на страницу курсов.
    """
    template_name = 'users/registration.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('courses:courses')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Learnify | Регистрация'
        return context

    def form_valid(self, form):
        try:
            user = form.save()
            login(self.request, user)
            messages.success(self.request, 'Вы успешно зарегистрировались!')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Ошибка регистрации: {str(e)}')
            return self.form_invalid(form)


class UserLoginView(LoginView):
    """
    Представление для входа пользователя в систему.
    """
    template_name = 'users/login.html'
    form_class = LoginForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Learnify | Вход'
        return context

    def get_success_url(self):
        return '/courses/'


@login_required
def custom_logout(request):
    """
    Представление для выхода пользователя из системы.
    """
    logout(request)
    return redirect('mainPage:home')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = get_object_or_404(Profile, user=user)

        # Общая информация
        context['title'] = 'Learnify | Dashboard'
        context['user_profile'] = profile

        # Получаем данные через сервис
        courses_data = get_user_courses_with_progress(user)
        context.update(courses_data)

        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
    """
    Представление для отображения детальной информации о курсе.
    """
    model = Course
    template_name = 'users/course_detail.html'
    context_object_name = 'course'

    def get_queryset(self):
        """
        Оптимизируем запросы для загрузки связанных данных.
        """
        return (
            Course.objects.select_related('teacher')  # Загружаем преподавателя
            .prefetch_related(
                Prefetch(
                    'lessons',
                    queryset=Lesson.objects.order_by('order').prefetch_related(
                        Prefetch(
                            'tests',
                            queryset=Test.objects.prefetch_related(
                                'questions__answers')
                        )
                    )
                )
            )
        )

    def check_course_access(self, course, user):
        cache_key = f"course_access_{user.id}_{course.id}"
        has_access = cache.get(cache_key)
        if has_access is None:
            # Проверяем, является ли курс бесплатным или оплаченным
            has_access = course.price == 0 or Payment.objects.filter(
                user=user, course=course, status='success'
            ).exists()
            # Кэшируем результат на 1 час
            cache.set(cache_key, has_access, timeout=60 * 60)

        if not has_access:
            # Если доступа нет, перенаправляем на страницу оплаты
            messages.warning(
                self.request,
                "У вас нет доступа к этому курсу. Пожалуйста, оплатите его."
            )
            return redirect('payments:payment', course_id=course.id)

    def get(self, request, *args, **kwargs):
        """
        Переопределяем метод get для проверки доступа перед отображением курса.
        """
        course = self.get_object()
        user = request.user
        # Проверяем доступ к курсу
        self.check_course_access(course, user)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        user = self.request.user

        # Получаем все уроки курса с тестами и вопросами (уже оптимизировано в get_queryset)
        lessons = course.lessons.all()

        # Проверяем прогресс пользователя по курсу
        try:
            progress = Progress.objects.get(user=user, course=course)
            completed_lessons = progress.completed_lessons
        except Progress.DoesNotExist:
            completed_lessons = []

        # Добавляем данные в контекст
        context.update({
            'title': f'Learnify | {course.title}',
            'lessons': lessons,
            'completed_lessons': completed_lessons,
        })
        return context


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'users/lesson_detail.html'
    context_object_name = 'lesson'

    def check_lesson_access(self, lesson, user):
        course = lesson.course
        cache_key = f"course_access_{user.id}_{course.id}"
        has_access = cache.get(cache_key)
        if has_access is None:
            has_access = course.price == 0 or Payment.objects.filter(
                user=user, course=course, status='success'
            ).exists()
            cache.set(cache_key, has_access, timeout=60 * 60)
        if not has_access:
            messages.warning(
                self.request,
                "У вас нет доступа к этому уроку. Пожалуйста, оплатите курс."
            )
            return redirect('courses:course_detail', pk=course.id)

    def get_queryset(self):
        """
        Оптимизируем запросы для загрузки связанных данных.
        """
        return (
            Lesson.objects.select_related('course')  # Загружаем связанный курс
            .prefetch_related(
                Prefetch(
                    'tests',  # Загружаем тесты
                    queryset=Test.objects.prefetch_related(
                        Prefetch(
                            'questions',  # Загружаем вопросы
                            queryset=Question.objects.prefetch_related(
                                'answers')  # Загружаем ответы
                        )
                    )
                )
            )
        )

    def get(self, request, *args, **kwargs):
        lesson = self.get_object()
        user = request.user
        # Проверяем доступ к уроку
        redirect_response = self.check_lesson_access(lesson, user)
        if redirect_response:
            return redirect_response
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.get_object()

        # Преобразование Markdown в HTML с подсветкой синтаксиса
        if lesson.content:
            html_content = markdown.markdown(
                lesson.content,
                extensions=['fenced_code', 'codehilite']
            )
        else:
            html_content = None

        # Получение CSS-стилей для подсветки синтаксиса
        css_styles = HtmlFormatter().get_style_defs('.codehilite')

        # Добавляем данные о тестах, вопросах и ответах
        tests = lesson.tests.all()  # Получаем все тесты, связанные с уроком
        test_data = []
        for test in tests:
            questions = test.questions.all()  # Получаем все вопросы для теста
            question_data = []
            for question in questions:
                answers = question.answers.all()  # Получаем все ответы для вопроса
                question_data.append({
                    'id': question.id,
                    'text': question.text,
                    'type': question.type,
                    'answers': [
                        {'id': answer.id, 'text': answer.text,
                            'is_correct': answer.is_correct}
                        for answer in answers
                    ]
                })
            test_data.append({
                'id': test.id,
                'title': test.title,
                'description': test.description,
                'questions': question_data
            })

        # Добавление данных в контекст
        context.update({
            'title': f'Learnify | {lesson.title}',
            'html_content': html_content,
            'css_styles': css_styles,  # Стили Pygments
            'tests': test_data,  # Добавляем тесты в контекст
        })
        return context


@csrf_exempt
def lesson_detail(request, lesson_id):
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Lesson not found'}, status=404)

    if request.method == 'POST':

        # Получаем данные из POST-запроса
        user_answers = {key: value for key, value in request.POST.items(
        ) if key.startswith('question_')}
        test_id = request.POST.get('test_id')

        if not test_id:
            return JsonResponse({'status': 'error', 'message': 'Test ID is missing'}, status=400)

        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Test not found'}, status=400)

        # Вычисляем результаты теста
        correct_answers, percentage = calculate_test_score(test, user_answers)

        # Обновляем прогресс пользователя
        user = request.user
        course = lesson.course
        progress, created = Progress.objects.get_or_create(
            user=user, course=course)
        progress.completed_lessons.add(lesson)
        progress.score += correct_answers
        if not progress.completed_at and progress.completed_lessons.count() == course.lessons.count():
            progress.completed_at = timezone.now()
        progress.save()

        return JsonResponse({
            'status': 'success',
            'correct_answers': correct_answers,
            'total_questions': test.questions.count(),
            'percentage': percentage,
            'message': 'Test results processed successfully',
        })

    else:
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


def calculate_test_score(test, user_answers):
    """
    Подсчитывает результат теста на основе выбранных пользователем ответов.
    :param test: объект Test
    :param user_answers: словарь {question_id: selected_answer_id}
    :return: количество правильных ответов, процент правильных ответов
    """
    total_questions = test.questions.count()
    correct_answers = 0

    print("Total questions:", total_questions)
    print("User answers:", user_answers)

    for question in test.questions.all():
        selected_answer_id = user_answers.get(f'question_{question.id}')
        if selected_answer_id:
            try:
                selected_answer = Answer.objects.get(id=selected_answer_id)
                print(
                    f"Question {question.id}: Selected answer {selected_answer_id}, Correct: {selected_answer.is_correct}")
                if selected_answer.is_correct:
                    correct_answers += 1
            except Answer.DoesNotExist:
                print(f"Answer {selected_answer_id} does not exist")

    percentage = (correct_answers / total_questions) * \
        100 if total_questions > 0 else 0
    print(f"Correct answers: {correct_answers}, Percentage: {percentage}")
    return correct_answers, percentage


@csrf_exempt
def mark_lesson_complete(request, lesson_id):
    if request.method == 'POST':
        try:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            user = request.user
            course = lesson.course
            progress, created = Progress.objects.get_or_create(
                user=user, course=course)
            if lesson not in progress.completed_lessons.all():
                progress.completed_lessons.add(lesson)
                progress.save()
                return JsonResponse({'status': 'success', 'message': 'Урок успешно отмечен как завершенный!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Урок уже отмечен как завершенный.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
