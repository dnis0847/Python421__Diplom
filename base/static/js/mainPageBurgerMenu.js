document.addEventListener('DOMContentLoaded', function () {
  const mobileMenuToggle = document.querySelector('.mobile-menu-toggle')
  const nav = document.querySelector('.hero__nav')
  const reg_menu = document.querySelector('.user_nav')

  mobileMenuToggle.addEventListener('click', function () {
    nav.classList.toggle('show')
    reg_menu.classList.toggle('show_menu')
    mobileMenuToggle.classList.toggle('active')
  })
})
