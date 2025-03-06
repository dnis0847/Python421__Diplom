document.addEventListener("DOMContentLoaded", () => {
    const mobileMenuToggle = document.querySelector(".mobile-menu-toggle")
    const sidebar = document.querySelector(".sidebar")
  
    mobileMenuToggle.addEventListener("click", () => {
      sidebar.classList.toggle("mobile-open")
    })
  })
  
  