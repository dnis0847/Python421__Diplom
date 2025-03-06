// Автоматическое скрытие сообщений через 5 секунд
document.addEventListener('DOMContentLoaded', function () {
  const messages = document.querySelectorAll(
    '.subscription-success-message, .message'
  )

  messages.forEach(function (message) {
    setTimeout(function () {
      message.style.opacity = '0'
      message.style.transition = 'opacity 0.5s ease-out'

      setTimeout(function () {
        message.style.display = 'none'
      }, 500)
    }, 45000)
  })
})
