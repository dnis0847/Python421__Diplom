function initMap() {
  const map = L.map("map").setView([55.751244, 37.618423], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  L.marker([55.751244, 37.618423]).addTo(map).bindPopup("Learnify").openPopup();
}

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Leaflet library
  const L = window.L

  // Инициализация карты
  const map = L.map("map").setView([55.751244, 37.618423], 13) // Координаты центра Москвы

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map)

  // Добавление маркера на карту
  L.marker([55.751244, 37.618423]).addTo(map).bindPopup("Learnify").openPopup()

  // Обработка отправки формы
  const contactForm = document.getElementById("contact-form")
  contactForm.addEventListener("submit", (e) => {
    e.preventDefault()
    // Здесь можно добавить код для отправки формы через AJAX
    alert("Ваше сообщение отправлено! Мы свяжемся с вами в ближайшее время.")
    contactForm.reset()
  })

  // Анимация появления элементов при прокрутке
  const animateOnScroll = () => {
    const elements = document.querySelectorAll(".contact-card, .faq-item, .social-icon")
    elements.forEach((element) => {
      const elementTop = element.getBoundingClientRect().top
      const windowHeight = window.innerHeight
      if (elementTop < windowHeight - 100) {
        element.classList.add("animate")
      }
    })
  }

  window.addEventListener("scroll", animateOnScroll)
  animateOnScroll() // Вызываем функцию сразу для элементов, видимых при загрузке

  // Плавная прокрутка для якорных ссылок
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault()
      document.querySelector(this.getAttribute("href")).scrollIntoView({
        behavior: "smooth",
      })
    })
  })
})

