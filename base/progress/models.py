from django.db import models
from django.contrib.auth.models import User
from courses.models import Course, Lesson

class Progress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progresses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='progresses')
    completed_lessons = models.ManyToManyField(Lesson, blank=True)
    score = models.IntegerField(default=0)  # Общий балл за тесты
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
