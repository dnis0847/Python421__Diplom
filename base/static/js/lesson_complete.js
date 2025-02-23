document.addEventListener('DOMContentLoaded', function () {
  const markLessonCompleteButton = document.getElementById(
    'mark-lesson-complete'
  )
  if (markLessonCompleteButton) {
    markLessonCompleteButton.addEventListener('click', function () {
      const lessonId = this.getAttribute('data-lesson-id')
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')
      if (csrfToken) {
        fetch(`/users/lesson/mark_complete/${lessonId}/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken.value,
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.status === 'success') {
                markLessonCompleteButton.classList.remove('secondary-btn')
            } else {
              alert('Ошибка: ' + data.message)
            }
          })
          .catch((error) => {
            console.error('Ошибка:', error)
          })
      } else {
        console.error('CSRF token not found')
      }
    })
  }
})
