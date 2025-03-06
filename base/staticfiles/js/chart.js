document.addEventListener('DOMContentLoaded', function () {
    const chartDataElement = document.getElementById('chartData');
    const courses = JSON.parse(chartDataElement.textContent);
    const courseNames = courses.map(course => course.title);
    const progressPercentages = courses.map(course => course.progress_percentage);

    const ctx = document.getElementById('progressChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar', // Тип графика остаётся 'bar'
        data: {
            labels: courseNames,
            datasets: [{
                label: 'Прогресс (%)',
                data: progressPercentages,
                backgroundColor: 'rgba(79, 70, 229, 0.6)',
                borderColor: 'rgba(79, 70, 229, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y', // Изменяем ось индексов на 'y' для горизонтальных столбцов
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100
                },
                y: {
                    ticks: {
                        callback: function (value, index, values) {
                            return `Курс: ${courseNames[index]}`;
                        }
                    }
                }
            }
        }
    });
});