document.addEventListener('DOMContentLoaded', function () {
  const textarea = document.getElementById('content')
  const preview = document.getElementById('preview')

  textarea.addEventListener('input', function () {
    const markdownText = textarea.value
    const html = marked(markdownText)
    preview.innerHTML = html
  })
})
