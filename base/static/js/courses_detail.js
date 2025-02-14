document.addEventListener("DOMContentLoaded", () => {

  // Tab functionality
  const tabButtons = document.querySelectorAll(".tab-button")
  const tabContents = document.querySelectorAll(".tab-content")

  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const tabId = button.getAttribute("data-tab")

      tabButtons.forEach((btn) => btn.classList.remove("active"))
      tabContents.forEach((content) => content.classList.remove("active"))

      button.classList.add("active")
      document.getElementById(tabId).classList.add("active")
    })
  })

  // Toggle reviews
  const toggleReviewsButton = document.getElementById("toggle-reviews")
  const additionalReviews = document.getElementById("additional-reviews")
  let showAllReviews = false

  toggleReviewsButton.addEventListener("click", () => {
    showAllReviews = !showAllReviews
    if (showAllReviews) {
      additionalReviews.classList.remove("hidden")
      toggleReviewsButton.innerHTML = 'Скрыть отзывы <i data-lucide="chevron-up" class="w-4 h-4 ml-1"></i>'
    } else {
      additionalReviews.classList.add("hidden")
      toggleReviewsButton.innerHTML = 'Показать все отзывы <i data-lucide="chevron-down" class="w-4 h-4 ml-1"></i>'
    }
  })
})

