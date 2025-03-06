from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from .models import Course, Category
from users.models import Profile
from payments.models import Payment
from progress.models import Progress
from django.contrib.auth.models import User
from django.db.models import Avg, Value, FloatField
from django.db.models import Count, Q
from django.db.models.functions import Coalesce
from django.db import models
import markdown


class CoursesView(ListView):
    model = Course
    template_name = 'courses/courses.html'
    context_object_name = 'courses'
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Learnify | Курсы'
        context['categorys'] = Category.objects.all()
        context['teachers'] = Profile.objects.filter(role='teacher')
        return context


def load_courses(request):
    page_number = request.GET.get('page', 1)
    category = request.GET.get('category', None)
    level = request.GET.get('level', None)
    price = request.GET.get('price', None)
    teacher = request.GET.get('teacher', None)
    view = request.GET.get('view', None)
    sort = request.GET.get('sort', None)
    min_price = request.GET.get('min_price', None)
    max_price = request.GET.get('max_price', None)
    search_query = request.GET.get('search', None)

    # Базовый запрос курсов
    courses = Course.objects.select_related(
        'teacher', 'category').prefetch_related('lessons').filter(is_published=True)

    # Поиск
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(teacher__first_name__icontains=search_query) |
            Q(teacher__last_name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Фильтрация
    if category:
        courses = courses.filter(category__name=category)
    if level and level != 'all':
        courses = courses.filter(level=level)
    if price and price != 'all':
        if price == 'free':
            courses = courses.filter(price=0)
        elif price == 'paid':
            courses = courses.filter(price__gt=0)
    if teacher and teacher != 'all':
        courses = courses.filter(teacher__last_name__icontains=teacher)
    if min_price and max_price:
        try:
            min_price = float(min_price)
            max_price = float(max_price)
            courses = courses.filter(price__range=(min_price, max_price))
        except ValueError:
            pass

    # Аннотация данных
    courses = courses.annotate(
        students_count=Count('progresses'),
        completed_students_count=Count('progresses', filter=models.Q(
            progresses__completed_at__isnull=False)),
        average_rating=Coalesce(Avg('reviews__rating'), Value(0), output_field=FloatField())
    )

    # Сортировка
    if view == 'popular':
        courses = courses.annotate(students_count=Count(
            'progresses')).order_by('-students_count')
    elif view == 'new':
        courses = courses.order_by('-created_at')
    if sort == 'price_asc':
        courses = courses.order_by('price')
    elif sort == 'price_desc':
        courses = courses.order_by('-price')
    elif sort == 'rating':
        courses = courses.order_by('-average_rating')

    # Пагинация
    paginator = Paginator(courses, 6)
    page = paginator.get_page(page_number)

    # Формирование данных для JSON
    data = {
        'courses': [
            {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'price': course.price,
                'image_url': course.image.url if course.image else None,
                'teacher_name': course.teacher.get_full_name(),
                'teacher_avatar': course.teacher.profile.avatar.url if course.teacher.profile.avatar else None,
                'category_name': course.category.name if course.category else "Без категории",
                'detail_url': reverse('courses:course_detail', args=[course.id]),
                'students_count': course.students_count,
                'completed_students_count': course.completed_students_count,
                'lessons_count': course.lessons.count(),
                'average_rating': course.average_rating or 0,
            }
            for course in page.object_list
        ],
        'has_next': page.has_next(),
    }

    return JsonResponse(data)


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object

        # Преобразование Markdown в HTML
        if course.full_description:
            html_content = markdown.markdown(course.full_description)
        else:
            html_content = None  # Если Markdown-текста нет

        # Количество студентов, изучающих курс
        students_count = Progress.objects.filter(course=course).count()

        # Получение всех отзывов для данного курса
        reviews = course.reviews.all()  # Используем related_name='reviews'

        # Количество отзывов
        reviews_count = reviews.count()

        # Общий средний рейтинг курса
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

        # Разделите отзывы на основные и дополнительные
        primary_reviews = reviews[:1]  # Первый отзыв
        additional_reviews = reviews[1:]  # Остальные отзывы

        # Добавление данных в контекст
        context.update({
            'title': f'Learnify | {course.title}',
            'categorys': Category.objects.all(),
            'lessons': course.lessons.all(),
            'lessons_count': course.lessons.count(),
            'html_content': html_content,
            'students_count': students_count,
            'primary_reviews': primary_reviews,
            'additional_reviews': additional_reviews,
            'reviews_count': reviews_count,  # Количество отзывов
            # Средний рейтинг (округленный до одного знака после запятой)
            'average_rating': round(average_rating, 1),
        })

        return context
