from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from .models import Course, Category
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
        return context


def load_courses(request):
    page_number = request.GET.get('page', 1)
    category = request.GET.get('category', None)
    level = request.GET.get('level', None)
    price = request.GET.get('price', None)
    teacher = request.GET.get('teacher', None)
    view = request.GET.get('view', None)
    sort = request.GET.get('sort', None)

    courses = Course.objects.all()

    if category:
        courses = courses.filter(category__name=category)
    if level:
        courses = courses.filter(level=level)
    if price:
        courses = courses.filter(price=price)
    if teacher:
        courses = courses.filter(teacher__last_name=teacher)
    if view == 'popular':
        courses = courses.order_by('-students_count')
    elif view == 'new':
        courses = courses.order_by('-created_at')
    if sort == 'price_asc':
        courses = courses.order_by('price')
    elif sort == 'price_desc':
        courses = courses.order_by('-price')

    paginator = Paginator(courses, 6)
    page = paginator.get_page(page_number)

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
        
        context['title'] = f'Learnify | {course.title}' 
        context['categorys'] = Category.objects.all()
        context['lessons'] = course.lessons.all()
        context['html_content'] = html_content
        return context