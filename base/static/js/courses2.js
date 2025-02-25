let currentPage = 1;
let currentCategory = null;
const loadMoreBtn = document.getElementById('load-more');
const coursesContainer = document.getElementById('courses-container');
const existingCourseIds = new Set();
const catCards = document.querySelectorAll('.category-card');
const allCategoriesBtn = document.getElementById('all-categories');
const titleCourses = document.querySelector('.courses__main__title');

// Функция загрузки курсов
async function loadCourses() {
  try {
    const categoryParam = currentCategory
      ? `&category=${encodeURIComponent(currentCategory)}`
      : '';
    const level = document.getElementById('level-select').value;
    const price = document.getElementById('price-select').value;
    const teacher = document.getElementById('teacher-select').value;
    const view = document.getElementById('view-select').value;
    const sort = document.getElementById('sort-select').value;

    const response = await fetch(
      `/courses/load-courses/?page=${currentPage}${categoryParam}&level=${level}&price=${price}&teacher=${teacher}&view=${view}`
      // `/courses/load-courses/?page=${currentPage}${categoryParam}&level=${level}&price=${price}&teacher=${teacher}&view=${view}&sort=${sort}`
    );

    if (!response.ok) {
      throw new Error(`Ошибка HTTP: ${response.status}`);
    }

    const data = await response.json();

    // Очищаем контейнер, если это первая страница
    if (currentPage === 1) {
      coursesContainer.innerHTML = '';
      existingCourseIds.clear();
    }

    // Добавляем новые карточки
    data.courses.forEach((course) => {
      if (!existingCourseIds.has(course.id)) {
        existingCourseIds.add(course.id);
        const courseHTML = createCourseCard(course);
        coursesContainer.insertAdjacentHTML('beforeend', courseHTML);
      }
    });

    // Проверяем, есть ли курсы
    if (!data.courses.length) {
      if (!coursesContainer.querySelector('p')) {
        coursesContainer.innerHTML = '<p>Курсов данной категории пока нет</p>';
      }
    }

    // Скрываем или показываем кнопку "Загрузить еще"
    if (!data.courses.length || !data.has_next) {
      loadMoreBtn.style.display = 'none';
    } else {
      loadMoreBtn.style.display = 'block';
    }

    currentPage++;
  } catch (error) {
    console.error('Ошибка при загрузке курсов:', error);
    coursesContainer.innerHTML =
      '<p>Произошла ошибка при загрузке курсов. Пожалуйста, попробуйте позже.</p>';
  }
}

// Функция склонения числительных
function pluralize(count, one, few, many) {
  if (count % 10 === 1 && count % 100 !== 11) {
    return one;
  } else if (
    [2, 3, 4].includes(count % 10) &&
    ![12, 13, 14].includes(count % 100)
  ) {
    return few;
  } else {
    return many;
  }
}

// Функция создания HTML-карточки курса
function createCourseCard(course) {
  return `
    <div class="courses__card">
      <div class="courses__card__image">
        <img src="${
          course.image_url || '/static/images/default_course.jpg'
        }" alt="${course.title}">
        <div class="courses__card__category">${course.category_name}</div>
      </div>
      <div class="courses__card__content">
        <h3>${course.title}</h3>
        <p>${course.description}</p>
        <div class="courses__card__content__instructor">
          <img src="${
            course.teacher_avatar || '/static/images/default_avatar.png'
          }" alt="${course.teacher_name}">
          <span>${course.teacher_name}</span>
        </div>
        <div class="courses__card__content__price__rating">
          <div class="courses__card__content__price">${course.price} ₽</div>
          <div class="courses__card__content__rating">
            <img src="/static/images/rating.svg" alt="rating">
            <div>4.5</div>
          </div>
        </div>
        <div class="courses__card__content__studies__info">
          <div>
            <img src="/static/images/time.svg" alt="time">
            <span>${course.lessons_count} ${
    pluralize(course.lessons_count, 'час', 'часа', 'часов') || '6 недель'
  }</span>
          </div>
          <div>
            <img src="/static/images/peoples.svg" alt="peoples">
            <span>${course.students_count} ${
    pluralize(course.students_count, 'студент', 'студента', 'студентов') ||
    '1234 студента'
  }</span>
          </div>
          <div>
            <img src="/static/images/books.svg" alt="books">
            <span>${course.lessons_count} ${
    pluralize(course.lessons_count, 'урок', 'урока', 'уроков') || '24 урока'
  }</span>
          </div>
        </div>
      </div>
      <a href="${course.detail_url}">
        <button>
          <span>Записаться на курс</span>
          <img src="/static/images/white_arrow.svg" alt="arrow">
        </button>
      </a>
    </div>
  `;
}

// Фильтрация курсов по категории
function filterCoursesByCategory(categoryName) {
  currentCategory = categoryName;
  currentPage = 1;
  existingCourseIds.clear();
  loadCourses();
  if (currentCategory) {
    titleCourses.innerHTML = currentCategory;
  }
}

// Обработчики событий
loadMoreBtn.addEventListener('click', loadCourses);

catCards.forEach((card) => {
  card.addEventListener('click', (e) => {
    catCards.forEach((c) => c.classList.remove('active'));
    allCategoriesBtn.classList.remove('active');
    e.currentTarget.classList.add('active');
    const categoryName = e.currentTarget.querySelector('h3').innerText;
    filterCoursesByCategory(categoryName);
  });
});

allCategoriesBtn.addEventListener('click', () => {
  catCards.forEach((c) => c.classList.remove('active'));
  allCategoriesBtn.classList.add('active');
  currentCategory = null;
  currentPage = 1;
  loadCourses();
  titleCourses.innerHTML = 'Все курсы';
});

document.getElementById('apply-filters').addEventListener('click', () => {
  coursesContainer.innerHTML = '';
  existingCourseIds.clear();
  currentPage = 1;
  loadCourses();
});

document.getElementById('reset-filters').addEventListener('click', () => {
  coursesContainer.innerHTML = '';
  existingCourseIds.clear();
  document.getElementById('level-select').value = 'all';
  document.getElementById('price-select').value = 'all';
  document.getElementById('teacher-select').value = 'all';
  document.getElementById('view-select').value = 'all';
  document.getElementById('sort-select').value = 'all';
  currentCategory = null;
  currentPage = 1;
  loadCourses();
  titleCourses.innerHTML = 'Все курсы';
});

// Загружаем первые курсы при загрузке страницы
window.addEventListener('load', () => {
  // Устанавливаем значения фильтров по умолчанию
  document.getElementById('level-select').value = 'all';
  document.getElementById('price-select').value = 'all';
  document.getElementById('teacher-select').value = 'all';
  document.getElementById('view-select').value = 'all';
  document.getElementById('sort-select').value = 'all';

  // Загружаем первые курсы
  currentPage = 1;
  loadCourses();
});