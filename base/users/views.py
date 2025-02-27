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
from django.db.models import Prefetch, Count
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
            # Получаем количество активных курсов
            active_courses_count = Course.objects.filter(teacher=user).count()

            # Получаем количество студентов, записанных на курсы преподавателя
            total_students_count = Payment.objects.filter(
                course__teacher=user, status='success'
            ).aggregate(total_students=Count('user', distinct=True))['total_students']

            # Получаем общую длительность всех курсов преподавателя
            total_duration = sum(course.lessons.count()
                                 for course in Course.objects.filter(teacher=user))

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
            # Проверяем, является ли пользователь преподавателем курса
            if course.teacher == user:
                has_access = True
            else:
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
            completed_lessons = progress.completed_lessons.all()  # Завершенные уроки
            completed_lessons_count = completed_lessons.count()  # Количество завершенных уроков
        except Progress.DoesNotExist:
            completed_lessons = []
            completed_lessons_count = 0

        # Общее количество уроков в курсе
        total_lessons_count = course.lessons.count()

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
            'lessons_count': lessons.count(),
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
        """
        course = lesson.course
        cache_key = f"course_access_{user.id}_{course.id}"
        has_access = cache.get(cache_key)

        if has_access is None:
            has_access = course.price == 0 or Payment.objects.filter(
                user=user, course=course, status='success'
            ).exists()
            # Кэшируем на 1 час
            cache.set(cache_key, has_access, timeout=60 * 60)

        if not has_access:
            messages.warning(
                self.request,
                "У вас нет доступа к этому уроку. Пожалуйста, оплатите курс."
            )
            return redirect('courses:course_detail', pk=course.id)

    def get_queryset(self):
        """
        Оптимизирует запросы для загрузки связанных данных.
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
        lessons = course.lessons.order_by('order')
        total_lessons = lessons.count()

        # Находим порядковый номер текущего урока
        current_lesson_index = list(lessons).index(lesson) + 1

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
        previous_lesson = lessons[current_lesson_index -
                                  2] if current_lesson_index > 1 else None
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
        """
        if not content or not content.strip():
            return None

        try:
            # Используем кэширование для Markdown-контента
            cache_key = f"markdown_{hash(content)}"
            html_content = cache.get(cache_key)

            if not html_content:
                # Преобразуем Markdown в HTML
                html_content = markdown.markdown(
                    content,
                    extensions=['fenced_code', 'codehilite', 'extra']
                )

                # Добавляем подсветку синтаксиса для кодовых блоков
                def process_code_blocks(html):
                    import re
                    code_block_pattern = re.compile(
                        r'<pre><code class="(.+?)">(.*?)</code></pre>', re.DOTALL)

                    def replace_match(match):
                        language = match.group(1)
                        code = match.group(2)
                        try:
                            lexer = get_lexer_by_name(language)
                        except ClassNotFound:
                            # Если язык не найден, используем plain text
                            lexer = get_lexer_by_name('text')
                        formatter = HtmlFormatter()
                        highlighted_code = highlight(code, lexer, formatter)
                        return f'<div class="highlight">{highlighted_code}</div>'

                    return code_block_pattern.sub(replace_match, html)

                html_content = process_code_blocks(html_content)
                # Кэшируем на 1 час
                cache.set(cache_key, html_content, timeout=60 * 60)

            return mark_safe(html_content)  # Отмечаем HTML как безопасный

        except Exception as e:
            # В случае ошибки выводим сообщение об ошибке
            return mark_safe(f"<p>Ошибка при преобразовании Markdown: {escape(str(e))}</p>")


@csrf_exempt
def lesson_detail(request, lesson_id):
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        logger.error(f"Урок с ID {lesson_id} не найден")
        return JsonResponse({'status': 'error', 'message': 'Lesson not found'}, status=404)

    if request.method == 'POST':
        try:
            # Получаем данные из JSON-тела запроса
            data = json.loads(request.body)
            logger.debug(f"Received POST data: {data}")

            # Извлекаем данные из JSON
            user_answers = {key: value for key,
                            value in data.items() if key.startswith('question_')}
            test_id = data.get('test_id')

            if not test_id:
                logger.error("Test ID is missing in the request data")
                return JsonResponse({'status': 'error', 'message': 'Test ID is missing'}, status=400)

            try:
                test = Test.objects.get(id=test_id)
            except Test.DoesNotExist:
                logger.error(f"Test with ID {test_id} not found")
                return JsonResponse({'status': 'error', 'message': 'Test not found'}, status=400)

            # Вычисляем результаты теста
            correct_answers, percentage = calculate_test_score(
                test, user_answers)

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

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    else:
        logger.error("Method not allowed")
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


@login_required
def add_review(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Проверяем, есть ли уже отзыв от этого пользователя для данного курса
    user_review = Review.objects.filter(
        user=request.user, course=course).first()

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if not rating or not comment:
            messages.error(request, "Пожалуйста, заполните все поля.")
            return redirect('users:course_detail', pk=course_id)

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError(
                    "Неверная оценка. Выберите значение от 1 до 5.")
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('users:course_detail', pk=course_id)

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

    # Если метод не POST, перенаправляем на страницу курса
    return redirect('users:course_detail', pk=course_id)


@login_required
def delete_review(request, course_id):
    """
    Представление для удаления отзыва пользователя для данного курса.
    """
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
        course = form.save(commit=False)
        course.save()
        messages.success(self.request, "Изменения успешно сохранены.")
        return super().form_valid(form)

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
    """

    def post(self, request, *args, **kwargs):
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


class CourseCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания нового курса.
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
        course = form.save(commit=False)
        # Устанавливаем текущего пользователя как преподавателя курса
        course.teacher = self.request.user
        course.save()
        messages.success(self.request, "Курс успешно создан.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем все категории
        context['categories'] = Category.objects.all()
        return context


class LessonCreateView(LoginRequiredMixin, CreateView):
    """
    Представление для создания нового урока.
    """
    model = Lesson
    template_name = 'users/lesson_create.html'
    fields = ['title', 'content', 'video_url', 'order']

    def form_valid(self, form):
        """
        Обработка валидной формы.
        """
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

    def get_success_url(self):
        """
        Перенаправляем на страницу курса после создания урока.
        """
        return reverse('users:course_edit_detail', kwargs={'pk': self.kwargs.get('course_id')})


class LessonEditView(LoginRequiredMixin, UpdateView):
    """
    Представление для редактирования урока.
    """
    model = Lesson
    template_name = 'users/lesson_edit.html'
    fields = ['title', 'content', 'video_url', 'order']

    def get_success_url(self):
        """
        Перенаправляем на страницу курса после редактирования урока.
        """
        return reverse_lazy('users:course_edit_detail', kwargs={'pk': self.object.course.id})


class LessonDeleteView(LoginRequiredMixin, View):
    """
    Представление для удаления урока.
    """

    def post(self, request, *args, **kwargs):
        lesson_id = kwargs.get('pk')
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Проверяем, является ли пользователь преподавателем курса
        if lesson.course.teacher != request.user:
            messages.warning(
                request,
                "У вас нет прав для удаления этого урока."
            )
            return redirect('users:dashboard')

        # Удаляем урок
        lesson.delete()
        messages.success(request, "Урок успешно удален.")
        return redirect('users:course_edit_detail', pk=lesson.course.id)
