# Убедитесь, что импортируете модель Category
from courses.models import Category
from django.shortcuts import get_object_or_404, redirect
from courses.models import Course
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, DetailView, FormView, View
from django.views.generic.edit import UpdateView, CreateView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Prefetch, Count, Q, F
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
import markdown
import json
from pygments.formatters import HtmlFormatter
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils import timezone
from django.db import transaction

# Локальные модули проекта
from .forms import RegistrationForm, LoginForm
from courses.models import Course, Lesson, Test, Question, Answer
from payments.models import Payment
from progress.models import Progress
from reviews.models import Review
from users.models import Profile
from .services import get_user_courses_with_progress
from django.conf import settings

import logging
logger = logging.getLogger(__name__)


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
            # Устанавливаем роль пользователя
            user.profile.role = form.cleaned_data.get('role')
            user.profile.save()
            
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
        """
        Получает контекст для шаблона dashboard.
        
        Оптимизированная версия:
        1. Уменьшено количество запросов к БД для преподавателей
        2. Использование аннотаций для подсчета количества студентов
        3. Более эффективное вычисление общей длительности курсов
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = get_object_or_404(Profile, user=user)

        # Получаем данные о курсах
        courses_data = get_user_courses_with_progress(user)

        # Преобразуем данные для JSON-сериализации
        courses_info = [
            {
                'title': course.get('title', 'Без названия'),
                'price': float(course.get('price', 0)) if 'price' in course else None,
                'progress_percentage': float(course.get('progress', {}).get('progress_percentage', 0)),
            }
            for course in courses_data.get('courses_info', [])
        ]

        # Используем DjangoJSONEncoder для сериализации
        context['courses_info_json'] = json.dumps(
            courses_info, cls=DjangoJSONEncoder)

        # Добавляем остальные данные в контекст
        context['title'] = 'Learnify | Dashboard'
        context['user_profile'] = profile
        context.update(courses_data)

        if profile.role == 'teacher':
            # Оптимизированное получение данных для преподавателя
            # Получаем все курсы преподавателя одним запросом с подсчетом уроков
            teacher_courses = Course.objects.filter(teacher=user).annotate(
                lessons_count=Count('lessons')
            )
            
            # Получаем количество активных курсов
            active_courses_count = teacher_courses.count()
            
            # Получаем количество студентов одним запросом с использованием аннотации
            total_students_count = Payment.objects.filter(
                course__teacher=user, status='success'
            ).values('user').distinct().count()
            
            # Вычисляем общую длительность всех курсов преподавателя
            total_duration = sum(course.lessons_count for course in teacher_courses)
            
            context['active_courses_count'] = active_courses_count
            context['total_students_count'] = total_students_count
            context['total_duration'] = total_duration

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
            Course.objects.select_related('teacher', 'category')  # Загружаем преподавателя и категорию
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
        """
        Проверяет доступ пользователя к курсу.
        
        Оптимизированная версия:
        1. Улучшенное кэширование
        2. Более четкая логика проверки доступа
        3. Возвращает результат проверки для более гибкого использования
        
        :param course: объект Course
        :param user: объект User
        :return: объект redirect или None, если доступ разрешен
        """
        cache_key = f"course_access_{user.id}_{course.id}"
        has_access = cache.get(cache_key)
        
        if has_access is None:
            # Проверяем, является ли пользователь преподавателем курса
            if course.teacher_id == user.id:  # Используем _id для избежания лишних запросов
                has_access = True
            # Проверяем, является ли курс бесплатным
            elif course.price == 0:
                has_access = True
            # Проверяем, оплачен ли курс
            else:
                has_access = Payment.objects.filter(
                    user_id=user.id, 
                    course_id=course.id, 
                    status='success'
                ).exists()
            
            # Кэшируем результат на 1 час
            cache.set(cache_key, has_access, timeout=60 * 60)

        if not has_access:
            # Если доступа нет, возвращаем объект redirect
            messages.warning(
                self.request,
                "У вас нет доступа к этому курсу. Пожалуйста, оплатите его."
            )
            return redirect('payments:payment', course_id=course.id)
        
        # Если доступ есть, возвращаем None
        return None

    def get(self, request, *args, **kwargs):
        """
        Переопределяем метод get для проверки доступа перед отображением курса.
        
        Оптимизированная версия:
        1. Использует результат check_course_access для определения дальнейших действий
        2. Более эффективная обработка ошибок
        """
        course = self.get_object()
        user = request.user
        
        # Проверяем доступ к курсу
        redirect_response = self.check_course_access(course, user)
        if redirect_response:
            return redirect_response
            
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
            completed_lessons = progress.completed_lessons.all()  # Завершенные уроки
            completed_lessons_count = completed_lessons.count()  # Количество завершенных уроков
        except Progress.DoesNotExist:
            completed_lessons = []
            completed_lessons_count = 0

        # Общее количество уроков в курсе
        total_lessons_count = lessons.count()

        # Вычисляем процент выполнения курса
        if total_lessons_count > 0:
            progress_percentage = (
                completed_lessons_count / total_lessons_count) * 100
        else:
            progress_percentage = 0

        # Получаем отзыв на текущий курс текущего пользователя
        review = Review.objects.filter(
            user=user, course=course).first()

        # Добавляем данные в контекст
        context.update({
            'title': f'Learnify | {course.title}',
            'lessons': lessons,
            'lessons_count': total_lessons_count,
            'completed_lessons': completed_lessons,
            'completed_lessons_count': completed_lessons_count,
            'progress_percentage': round(progress_percentage),
            'user_review': review,
        })
        return context


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'users/lesson_detail.html'
    context_object_name = 'lesson'

    def check_lesson_access(self, lesson, user):
        """
        Проверяет доступ пользователя к уроку.
        
        Оптимизированная версия:
        1. Улучшенное кэширование
        2. Более четкая логика проверки доступа
        3. Возвращает результат проверки для более гибкого использования
        """
        course = lesson.course
        cache_key = f"course_access_{user.id}_{course.id}"
        has_access = cache.get(cache_key)

        if has_access is None:
            # Проверяем, является ли пользователь преподавателем курса
            if course.teacher_id == user.id:
                has_access = True
            # Проверяем, является ли курс бесплатным
            elif course.price == 0:
                has_access = True
            # Проверяем, оплачен ли курс
            else:
                has_access = Payment.objects.filter(
                    user_id=user.id, 
                    course_id=course.id, 
                    status='success'
                ).exists()
            
            # Кэшируем результат на 1 час
            cache.set(cache_key, has_access, timeout=60 * 60)

        if not has_access:
            messages.warning(
                self.request,
                "У вас нет доступа к этому уроку. Пожалуйста, оплатите курс."
            )
            return redirect('courses:course_detail', pk=course.id)
        
        # Если доступ есть, возвращаем None
        return None

    def get_queryset(self):
        """
        Оптимизирует запросы для загрузки связанных данных.
        """
        return (
            Lesson.objects.select_related('course', 'course__teacher')  # Загружаем связанный курс и преподавателя
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
        """
        Обрабатывает GET-запрос, проверяя доступ к уроку.
        """
        lesson = self.get_object()
        user = request.user
        # Проверяем доступ к уроку
        redirect_response = self.check_lesson_access(lesson, user)
        if redirect_response:
            return redirect_response
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Добавляет дополнительные данные в контекст шаблона.
        """
        context = super().get_context_data(**kwargs)
        lesson = self.get_object()
        user = self.request.user

        # Получаем курс, к которому относится урок
        course = lesson.course

        # Получаем все уроки курса, отсортированные по порядку
        lessons = list(course.lessons.order_by('order'))
        total_lessons = len(lessons)

        # Находим порядковый номер текущего урока
        try:
            current_lesson_index = lessons.index(lesson) + 1
        except ValueError:
            current_lesson_index = 1

        # Инициализируем progress перед try-except
        progress = None

        # Вычисляем процент прохождения уроков
        try:
            progress = Progress.objects.get(user=user, course=course)
            completed_lessons_count = progress.completed_lessons.count()
            progress_percentage = (
                completed_lessons_count / total_lessons) * 100 if total_lessons > 0 else 0
        except Progress.DoesNotExist:
            completed_lessons_count = 0
            progress_percentage = 0

        # Проверяем, завершен ли текущий урок
        is_current_lesson_completed = False
        if progress and hasattr(progress, 'completed_lessons'):
            is_current_lesson_completed = progress.completed_lessons.filter(
                id=lesson.id).exists()

        # Находим предыдущий и следующий уроки
        previous_lesson = lessons[current_lesson_index - 2] if current_lesson_index > 1 else None
        next_lesson = lessons[current_lesson_index] if current_lesson_index < total_lessons else None

        # Ссылки на предыдущий и следующий уроки
        previous_lesson_url = reverse('users:lesson_detail', kwargs={
                                      'pk': previous_lesson.pk}) if previous_lesson else None
        next_lesson_url = reverse('users:lesson_detail', kwargs={
                                  'pk': next_lesson.pk}) if next_lesson else None

        # Ссылка на текущий курс
        course_url = reverse('users:course_detail', kwargs={'pk': course.pk})

        # Преобразование Markdown в HTML с подсветкой синтаксиса
        html_content = self.convert_markdown_to_html(lesson.content)

        # Получение CSS-стилей для подсветки синтаксиса
        formatter = HtmlFormatter(style="colorful")
        css_styles = formatter.get_style_defs('.codehilite')

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
            'current_lesson_index': current_lesson_index,  # Порядковый номер текущего урока
            'total_lessons': total_lessons,  # Общее количество уроков
            # Процент прохождения уроков
            'progress_percentage': round(progress_percentage),
            'course_url': course_url,  # Ссылка на текущий курс
            'previous_lesson_url': previous_lesson_url,  # Ссылка на предыдущий урок
            'next_lesson_url': next_lesson_url,  # Ссылка на следующий урок
            'is_current_lesson_completed': is_current_lesson_completed,  # Завершен ли текущий урок
        })

        return context

    def convert_markdown_to_html(self, content):
        """
        Преобразует Markdown-контент в HTML с подсветкой синтаксиса.
        
        Оптимизированная версия:
        1. Улучшенное кэширование
        2. Более эффективная обработка кодовых блоков
        3. Улучшенная обработка ошибок
        """
        if not content or not content.strip():
            return ""

        try:
            # Используем более надежный ключ кэша
            cache_key = f"markdown_{hash(content)}_{settings.SECRET_KEY[:5]}"
            html_content = cache.get(cache_key)

            if not html_content:
                # Преобразуем Markdown в HTML
                html_content = markdown.markdown(
                    content,
                    extensions=['fenced_code', 'codehilite', 'extra', 'tables']
                )

                # Оптимизированная обработка кодовых блоков с использованием компилированных регулярных выражений
                import re
                code_block_pattern = re.compile(
                    r'<pre><code class="(.+?)">(.*?)</code></pre>', re.DOTALL)

                def replace_match(match):
                    language = match.group(1).split()[0]  # Берем только первое слово (язык)
                    code = match.group(2)
                    try:
                        lexer = get_lexer_by_name(language)
                    except ClassNotFound:
                        lexer = get_lexer_by_name('text')
                    formatter = HtmlFormatter(style="colorful", linenos=False)
                    highlighted_code = highlight(code, lexer, formatter)
                    return highlighted_code

                html_content = code_block_pattern.sub(replace_match, html_content)
                
                # Кэшируем на 24 часа для статического контента
                cache.set(cache_key, html_content, timeout=60 * 60 * 24)

            return mark_safe(html_content)

        except Exception as e:
            logger.error(f"Ошибка при преобразовании Markdown: {str(e)}")
            return mark_safe(f"<p>Ошибка при преобразовании контента. Пожалуйста, сообщите администратору.</p>")


@csrf_exempt
def lesson_detail(request, lesson_id):
    """
    Обрабатывает запросы к API урока.
    
    Оптимизированная версия:
    1. Улучшенная обработка ошибок
    2. Более эффективная работа с данными
    3. Транзакционная обработка обновления прогресса
    """
    try:
        lesson = Lesson.objects.select_related('course').get(id=lesson_id)
    except Lesson.DoesNotExist:
        logger.error(f"Урок с ID {lesson_id} не найден")
        return JsonResponse({'status': 'error', 'message': 'Урок не найден'}, status=404)

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Метод не разрешен'}, status=405)
    
    try:
        # Получаем данные из JSON-тела запроса
        data = json.loads(request.body)
        
        # Извлекаем данные из JSON
        user_answers = {key: value for key, value in data.items() 
                        if key.startswith('question_')}
        test_id = data.get('test_id')

        if not test_id:
            return JsonResponse({
                'status': 'error', 
                'message': 'ID теста отсутствует в запросе'
            }, status=400)

        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return JsonResponse({
                'status': 'error', 
                'message': f'Тест с ID {test_id} не найден'
            }, status=400)

        # Вычисляем результаты теста
        correct_answers, percentage = calculate_test_score(test, user_answers)

        # Обновляем прогресс пользователя в транзакции
        with transaction.atomic():
            user = request.user
            course = lesson.course
            progress, created = Progress.objects.get_or_create(
                user=user, course=course)
            
            # Добавляем урок в завершенные
            progress.completed_lessons.add(lesson)
            
            # Обновляем счет
            progress.score += correct_answers
            
            # Проверяем, завершен ли курс
            if not progress.completed_at:
                completed_lessons_count = progress.completed_lessons.count()
                total_lessons_count = course.lessons.count()
                
                if completed_lessons_count == total_lessons_count:
                    progress.completed_at = timezone.now()
            
            progress.save()

        return JsonResponse({
            'status': 'success',
            'correct_answers': correct_answers,
            'total_questions': test.questions.count(),
            'percentage': percentage,
            'message': 'Результаты теста успешно обработаны',
        })

    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON")
        return JsonResponse({'status': 'error', 'message': 'Некорректный JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Внутренняя ошибка сервера'}, status=500)


def calculate_test_score(test, user_answers):
    """
    Подсчитывает результат теста на основе выбранных пользователем ответов.
    
    Оптимизированная версия:
    1. Загружает все ответы одним запросом
    2. Использует словарь для быстрого поиска
    3. Удалены отладочные print-выражения
    
    :param test: объект Test
    :param user_answers: словарь {question_id: selected_answer_id}
    :return: количество правильных ответов, процент правильных ответов
    """
    # Получаем все вопросы теста одним запросом
    questions = test.questions.all()
    total_questions = len(questions)
    
    if total_questions == 0:
        return 0, 0
    
    # Получаем все ID ответов, выбранных пользователем
    selected_answer_ids = [int(answer_id) for answer_id in user_answers.values() if answer_id]
    
    # Если нет выбранных ответов, возвращаем 0
    if not selected_answer_ids:
        return 0, 0
    
    # Получаем все правильные ответы одним запросом
    correct_answers_count = Answer.objects.filter(
        id__in=selected_answer_ids, 
        is_correct=True
    ).count()
    
    # Вычисляем процент правильных ответов
    percentage = (correct_answers_count / total_questions) * 100
    
    return correct_answers_count, percentage


@csrf_exempt
def mark_lesson_complete(request, lesson_id):
    """
    Отмечает урок как завершенный.
    
    Оптимизированная версия:
    1. Использование транзакций
    2. Улучшенная обработка ошибок
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Метод не разрешен'}, status=405)
    
    try:
        with transaction.atomic():
            lesson = get_object_or_404(Lesson, id=lesson_id)
            user = request.user
            course = lesson.course
            
            # Получаем или создаем объект прогресса
            progress, created = Progress.objects.get_or_create(
                user=user, course=course)
            
            # Проверяем, не завершен ли уже урок
            if not progress.completed_lessons.filter(id=lesson.id).exists():
                # Добавляем урок в завершенные
                progress.completed_lessons.add(lesson)
                
                # Проверяем, завершен ли курс
                if not progress.completed_at:
                    completed_lessons_count = progress.completed_lessons.count()
                    total_lessons_count = course.lessons.count()
                    
                    if completed_lessons_count == total_lessons_count:
                        progress.completed_at = timezone.now()
                
                progress.save()
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Урок успешно отмечен как завершенный!'
                })
            else:
                return JsonResponse({
                    'status': 'info', 
                    'message': 'Урок уже отмечен как завершенный.'
                })
    except Exception as e:
        logger.error(f"Ошибка при отметке урока как завершенного: {str(e)}")
        return JsonResponse({
            'status': 'error', 
            'message': f'Произошла ошибка: {str(e)}'
        }, status=500)


@login_required
def add_review(request, course_id):
    """
    Добавляет или обновляет отзыв пользователя о курсе.
    
    Оптимизированная версия:
    1. Использование транзакций
    2. Улучшенная валидация данных
    3. Более четкая логика обработки
    """
    course = get_object_or_404(Course, id=course_id)

    if request.method != 'POST':
        return redirect('users:course_detail', pk=course_id)
    
    try:
        # Получаем данные из запроса
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        # Валидация данных
        if not rating or not comment:
            messages.error(request, "Пожалуйста, заполните все поля.")
            return redirect('users:course_detail', pk=course_id)

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError("Неверная оценка. Выберите значение от 1 до 5.")
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('users:course_detail', pk=course_id)

        # Обновля  str(e))
            return redirect('users:course_detail', pk=course_id)

        # Обновляем или создаем отзыв в транзакции
        with transaction.atomic():
            # Проверяем, есть ли уже отзыв от этого пользователя для данного курса
            user_review = Review.objects.filter(
                user=request.user, course=course).first()
                
            if user_review:
                # Если отзыв уже существует, обновляем его
                user_review.rating = rating
                user_review.comment = comment
                user_review.save()
                messages.success(request, "Ваш отзыв успешно обновлен!")
            else:
                # Если отзыва нет, создаем новый
                Review.objects.create(
                    user=request.user,
                    course=course,
                    rating=rating,
                    comment=comment
                )
                messages.success(request, "Ваш отзыв успешно отправлен!")

        return redirect('users:course_detail', pk=course_id)
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении отзыва: {str(e)}")
        messages.error(request, f"Произошла ошибка: {str(e)}")
        return redirect('users:course_detail', pk=course_id)


@login_required
def delete_review(request, course_id):
    """
    Представление для удаления отзыва пользователя для данного курса.
    
    Оптимизированная версия:
    1. Использование транзакций
    2. Улучшенная обработка ошибок
    """
    try:
        with transaction.atomic():
            course = get_object_or_404(Course, id=course_id)
            user = request.user

            # Находим отзыв пользователя для данного курса
            review = Review.objects.filter(user=user, course=course).first()

            if review:
                # Удаляем отзыв
                review.delete()
                messages.success(
                    request, "Ваш отзыв успешно удален. Вы можете оставить новый.")
            else:
                messages.warning(request, "У вас нет отзыва для этого курса.")

        # Перенаправляем пользователя на страницу курса
        return redirect('users:course_detail', pk=course_id)
    
    except Exception as e:
        logger.error(f"Ошибка при удалении отзыва: {str(e)}")
        messages.error(request, f"Произошла ошибка: {str(e)}")
        return redirect('users:course_detail', pk=course_id)


class CourseEditView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования курса.
    """
    model = Course
    template_name = 'users/course_edit.html'
    context_object_name = 'course'
    fields = ['title', 'description',
              'full_description', 'category', 'level', 'image', 'price']
    success_url = reverse_lazy('users:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()

        # Получаем все категории
        categories = Category.objects.all()

        # Получаем все уроки, связанные с данным курсом
        lessons = course.lessons.all().order_by('order')

        context['title'] = f'Learnify | Редактирование: {course.title}'
        context['categories'] = categories
        context['lessons'] = lessons  # Добавляем уроки в контекст
        return context

    def form_valid(self, form):
        """
        Обработка валидной формы.
        """
        try:
            with transaction.atomic():
                course = form.save(commit=False)
                course.save()
                messages.success(self.request, "Изменения успешно сохранены.")
                return super().form_valid(form)
        except Exception as e:
            logger.error(f"Ошибка при сохранении курса: {str(e)}")
            messages.error(self.request, f"Произошла ошибка: {str(e)}")
            return self.form_invalid(form)

    def get(self, request, *args, **kwargs):
        """
        Переопределяем метод get для проверки доступа перед отображением курса.
        """
        course = self.get_object()
        user = request.user

        # Проверяем, является ли пользователь преподавателем курса
        if course.teacher != user:
            messages.warning(
                self.request,
                "У вас нет прав для редактирования этого курса."
            )
            return redirect('users:dashboard')

        return super().get(request, *args, **kwargs)


class CourseDeleteView(LoginRequiredMixin, View):
    """
    Представление для удаления курса.
    
    Оптимизированная версия:
    1. Использование транзакций
    2. Улучшенная обработка ошибок
    """
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                course_id = kwargs.get('pk')
                course = get_object_or_404(Course, id=course_id)

                # Проверяем, является ли пользователь преподавателем курса
                if course.teacher != request.user:
                    messages.warning(
                        request,
                        "У вас нет прав для удаления этого курса."
                    )
                    return redirect('users:dashboard')

                # Удаляем курс
                course.delete()
                messages.success(request, "Курс успешно удален.")
            
            return redirect('users:dashboard')
        
        except Exception as e:
            logger.error(f"Ошибка при удалении курса: {str(e)}")
            messages.error(request, f"Произошла ошибка при удалении курса: {str(e)}")
            return redirect('users:dashboard')


class CourseCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания нового курса.
    
    Оптимизированная версия:
    1. Использование транзакций
    2. Улучшенная обработка ошибок
    """
    model = Course
    template_name = 'users/course_create.html'
    fields = ['title', 'description', 'full_description',
              'category', 'level', 'image', 'price']
    success_url = reverse_lazy('users:dashboard')

    def form_valid(self, form):
        """
        Обработка валидной формы.
        """
        try:
            with transaction.atomic():
                course = form.save(commit=False)
                # Устанавливаем текущего пользователя как преподавателя курса
                course.teacher = self.request.user
                course.save()
                messages.success(self.request, "Курс успешно создан.")
                return super().form_valid(form)
        except Exception as e:
            logger.error(f"Ошибка при создании курса: {str(e)}")
            messages.error(self.request, f"Произошла ошибка: {str(e)}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем все категории
        context['categories'] = Category.objects.all()
        return context


class LessonCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания нового урока.
    
    Оптимизированная версия:
    1. Использование транзакций
    2. Улучшенная обработка ошибок
    """
    model = Lesson
    template_name = 'users/lesson_create.html'
    fields = ['title', 'content', 'video_url', 'order']

    def form_valid(self, form):
        """
        Обработка валидной формы.
        """
        try:
            with transaction.atomic():
                lesson = form.save(commit=False)
                course_id = self.kwargs.get('course_id')
                course = get_object_or_404(Course, id=course_id)

                # Проверяем, является ли пользователь преподавателем курса
                if course.teacher != self.request.user:
                    messages.warning(
                        self.request,
                        "У вас нет прав для добавления уроков в этот курс."
                    )
                    return redirect('users:dashboard')

                lesson.course = course
                lesson.save()
                messages.success(self.request, "Урок успешно создан.")
                return super().form_valid(form)
        except Exception as e:
            logger.error(f"Ошибка при создании урока: {str(e)}")
            messages.error(self.request, f"Произошла ошибка: {str(e)}")
            return self.form_invalid(form)

    def get_success_url(self):
        """
        Перенаправляем на страницу курса после создания урока.
        """
        return reverse('users:course_edit_detail', kwargs={'pk': self.kwargs.get('course_id')})


class LessonEditView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования урока.
    
    Оптимизированная версия:
    1. Использование транзакций
    2. Улучшенная обработка ошибок
    """
    model = Lesson
    template_name = 'users/lesson_edit.html'
    fields = ['title', 'content', 'video_url', 'order']

    def form_valid(self, form):
        """
        Обработка валидной формы.
        """
        try:
            with transaction.atomic():
                lesson = form.save()
                messages.success(self.request, "Урок успешно обновлен.")
                return super().form_valid(form)
        except Exception as e:
            logger.error(f"Ошибка при обновлении урока: {str(e)}")
            messages.error(self.request, f"Произошла ошибка: {str(e)}")
            return self.form_invalid(form)

    def get_success_url(self):
        """
        Перенаправляем на страницу курса после редактирования урока.
        """
        return reverse_lazy('users:course_edit_detail', kwargs={'pk': self.object.course.id})


class LessonDeleteView(LoginRequiredMixin, View):
    """
    Представление для удаления урока.
    
    Оптимизированная версия:
    1. Использование транзакций
    2. Улучшенная обработка ошибок
    """
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                lesson_id = kwargs.get('pk')
                lesson = get_object_or_404(Lesson, id=lesson_id)

                # Проверяем, является ли пользователь преподавателем курса
                if lesson.course.teacher != request.user:
                    messages.warning(
                        request,
                        "У вас нет прав для удаления этого урока."
                    )
                    return redirect('users:dashboard')

                course_id = lesson.course.id
                # Удаляем урок
                lesson.delete()
                messages.success(request, "Урок успешно удален.")
            
            return redirect('users:course_edit_detail', pk=course_id)
        
        except Exception as e:
            logger.error(f"Ошибка при удалении урока: {str(e)}")
            messages.error(request, f"Произошла ошибка при удалении урока: {str(e)}")
            return redirect('users:dashboard')