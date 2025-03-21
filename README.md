# **Lirnify - платформа обучения**  
![banner](banner.png)

## **О проекте**  
> "Этот проект — в большей степени создан для того что бы ознакомиться с возможностами Django. Он представляет собой платформу для online-обучения учеников, а так же для преподователей, которые хотели бы познакомить учеников со своими курсами."

---

## **Возможности**  
✅ **Выбор курсов для обучения**: После того как ученик зашел на сайт он может ознакомиться со списков всех предоставленных курсов, вабрать его в зависимости от параметров таких как категория, уровень подготовки, преподователя.  
---
✅ **Оплата**: После того, как ученик ознакомился с программой курса он нажимает на кнопку начать обучение происходит имитация оплаты. Если оплата прошла успешно, то далее он может попасть в личный кабинет, где он может начать свое обучение.
---
✅ **Личный кабинет**: В личном кабинете представлена программа курса, а так же прогресс обучения ученика в процентах и количестве уроков.  
---
✅ **Обучение**: После нажатия на первый урок мы поподаем на страницу с уроком, где добавленые материалы урока в формате markdown сериализуются в html, который соответсвенно стилизуется. Тут мы можем посмотреть название урока, прогресс обучения, перейти на следующий урок или предыдущий минуя главную страницу курса, а так же отметить урок как завершенный.
---
✅ **Отзыв и Рейтинг**: После того, как мы приобрели наш курс мы так же можем оставить свой отзыв и поставить оценку курсу в зависимости от того, понравился ли курс, по мере прохождения курса если наша оценка изменилась мы можем удалить отзыв и оценку и оценить заново.
---
✅ **Функционал преподователя**: Если вы зарегестрировались как преподователь, то перейдя в личный кабинет у вас есть возможность создать свой курс, после создания курса вы можете редактировать его и удалять, к каждому курсу можно добавлять уроки, в зависимости от добавленных уроков будет в описание добавляться программа курса. После добавления урока его можно просматривать, редактировать и удалять.
---
---

## **Технологии**  
*Какие инструменты и языки использованы:*  
- **Frontend**: HTML, CSS, JavaScript  
- **Backend**: Python, Django  
- **База данных**: PostgreSQL  
- **Дополнительно**: Облачный сервер на Ubuntu 22.04, Nginx, Gunicorn

---

## **Установка и запуск**  
*Пошаговая инструкция для быстрого старта:*  
1. Клонируйте репозиторий:  
   ```bash
   git clone https://github.com/dnis0847/Python421__Diplom
   ```  
2. Создание и активация виртуальной среды
    Для windows:
    ```bash
     python -m venv env
     env\Scripts\activate
    ```
    Для mac, linux:
    ```bash
     python3 -m venv имя_среды
     source имя_среды/bin/activate
    ```

3. Установите зависимости:  
   ```bash
   pip install -r requirements.txt.
   ```  
3. Запустите проект:  
   ```bash
   cd base && python3 manage.py runserver
   ```  

---

## **Планы на будущее**   
- [ ] Создание ЛК для администратора
- [ ] Отображение большей статистики использования курсов 
- [ ] Улучшение производительности
- [ ] Создание чата для общения между учениками и преподователями
- [ ] Отправка домашних работ на проверку


---

## **Контакты**  
*Как связаться с вами:*  
- Автор: [Семиколенов Денис](https://github.com/dnis0847)  
- Email: Dnis0847@yandex.ru  
