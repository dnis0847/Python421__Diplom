document.addEventListener('DOMContentLoaded', function () {
  const faqItems = document.querySelectorAll('.faq__item')

  faqItems.forEach((item) => {
    const question = item.querySelector('.faq__question')
    question.addEventListener('click', () => {
      item.classList.toggle('active')
    })
  })
})
