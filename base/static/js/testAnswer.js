document.addEventListener('DOMContentLoaded', function () {
  // Функция для получения CSRF-токена из cookies
  function getCSRFToken() {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
              const cookie = cookies[i].trim();
              if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken=')) {
                  cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
  }

  // Функция для отправки POST-запроса
  function sendPostRequest(url, data, onSuccess, onError) {
      const csrfToken = getCSRFToken();
      if (!csrfToken) {
          console.error('CSRF token not found');
          return;
      }

      fetch(url, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify(data),
      })
      .then((response) => response.json())
      .then((data) => {
          if (data.status === 'success') {
              onSuccess(data);
          } else {
              onError(data.message || 'Произошла ошибка');
          }
      })
      .catch((error) => {
          console.error('Ошибка:', error);
          onError('Сетевая ошибка');
      });
  }

  // Обработка формы теста
  const quizForm = document.getElementById('quiz-form');
  if (quizForm) {
      quizForm.addEventListener('submit', function (e) {
          e.preventDefault();

          const lessonId = this.getAttribute('data-lesson-id');
          const formData = new FormData(this);

          // Преобразуем FormData в объект
          const answers = {};
          formData.forEach((value, key) => {
              answers[key] = value;
          });

          sendPostRequest(
              `/users/lesson/api/${lessonId}/`,
              answers,
              (data) => {
                  document.getElementById('quiz-result').style.display = 'block';
                  document.getElementById('result-score').textContent = `Вы набрали ${data.correct_answers} из ${data.total_questions} (${data.percentage.toFixed(2)}%)`;
              },
              (message) => {
                  alert('Ошибка: ' + message);
              }
          );
      });
  }

  // Обработка кнопки "Отметить урок как завершенный"
  const markLessonCompleteButton = document.getElementById('mark-lesson-complete');
  if (markLessonCompleteButton) {
      markLessonCompleteButton.addEventListener('click', function () {
          const lessonId = this.getAttribute('data-lesson-id');

          sendPostRequest(
              `/users/lesson/mark_complete/${lessonId}/`,
              {},
              (data) => {
                  alert('Урок успешно отмечен как завершенный!');
                  // Обновите интерфейс, если необходимо
              },
              (message) => {
                  alert('Ошибка: ' + message);
              }
          );
      });
  }
});