# services.py
from django.db.models import Prefetch
from courses.models import Course, Lesson
from progress.models import Progress
from payments.models import Payment


def get_user_courses_with_progress(user):
    if user.profile.role == 'teacher':
        # Если пользователь преподаватель, получаем курсы, которые он создал
        courses = Course.objects.filter(teacher=user)
        active_courses_count = courses.count()
        completed_courses_count = 0  # Для преподавателя это значение не актуально
        total_training_time = 0  # Для преподавателя это значение не актуально
    else:
        # Если пользователь студент, получаем купленные курсы
        purchased_courses = Payment.objects.filter(
            user=user, status='success').select_related('course')
        active_courses_count = 0
        completed_courses_count = 0
        total_training_time = 0
        courses = []
        for payment in purchased_courses:
            course = payment.course
            courses.append(course)
            try:
                progress = Progress.objects.get(user=user, course=course)
                completed_lessons_count = progress.completed_lessons.count()
                total_lessons_count = course.lessons.count()
                progress_percentage = (
                    (completed_lessons_count / total_lessons_count) * 100
                    if total_lessons_count > 0
                    else 0
                )
                is_completed = progress.completed_at is not None
                if is_completed:
                    completed_courses_count += 1
                else:
                    active_courses_count += 1
                total_training_time += completed_lessons_count
            except Progress.DoesNotExist:
                completed_lessons_count = 0
                total_lessons_count = course.lessons.count()
                progress_percentage = 0
                is_completed = False
                active_courses_count += 1

    courses_info = []
    for course in courses:
        try:
            progress = Progress.objects.get(user=user, course=course)
            completed_lessons_count = progress.completed_lessons.count()
            total_lessons_count = course.lessons.count()
            progress_percentage = (
                (completed_lessons_count / total_lessons_count) * 100
                if total_lessons_count > 0
                else 0
            )
            is_completed = progress.completed_at is not None
        except Progress.DoesNotExist:
            completed_lessons_count = 0
            total_lessons_count = course.lessons.count()
            progress_percentage = 0
            is_completed = False

        course_data = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "teacher": course.teacher.get_full_name() if course.teacher else "Не указан",
            "price": course.price,
            "level": course.get_level_display(),
            "category": course.category.name if course.category else "Без категории",
            "created_at": course.created_at,
            "is_published": course.is_published,
            "image": course.image,
            "total_lessons_count": course.lessons.count(),
            "progress": {
                "completed_lessons_count": completed_lessons_count,
                "total_lessons_count": total_lessons_count,
                "progress_percentage": round(progress_percentage),
                "is_completed": is_completed,
            },
        }
        courses_info.append(course_data)

    return {
        "active_courses_count": active_courses_count,
        "completed_courses_count": completed_courses_count,
        "total_training_time": total_training_time,
        "courses_info": courses_info,
    }
