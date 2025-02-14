document.addEventListener("DOMContentLoaded", () => {
    var modal = document.getElementById("paymentModal")
    var btn = document.querySelector(".start__learning")
    var span = document.getElementsByClassName("close")[0]
  
    btn.onclick = (e) => {
      e.preventDefault() // Предотвращаем стандартное действие кнопки
      modal.style.display = "block"
    }
  
    span.onclick = () => {
      modal.style.display = "none"
    }
  
    window.onclick = (event) => {
      if (event.target == modal) {
        modal.style.display = "none"
      }
    }
  })
  
  