document.querySelector('#registerForm form').addEventListener('submit', async function(event) {
    event.preventDefault(); // Предотвращаем стандартное поведение отправки формы

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    document.getElementById('loadingIcon').style.display = 'block';

    try {
        const response = await fetch('/users/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        console.log(response);

        if (response.ok) {
            console.log('Регистрация успешна');
            // Добавьте эту строку для редиректа
            window.location.href = '/users/confirm-email';
        } else {
            console.log('Ошибка при регистрации');
            const error = await response.json();
            alert('Ошибка: ' + error.detail);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при отправке данных');
    } finally {
        // Скрываем иконку загрузки
        document.getElementById('loadingIcon').style.display = 'none';
    }
});

document.querySelector('#loginForm form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    document.getElementById('loadingIcon').style.display = 'block';

    try {
        const response = await fetch('/users/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            window.location.href = '/analysis';
        } else {
            const error = await response.json();
            alert('Ошибка: ' + error.detail);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при отправке данных');
    } finally {
        // Скрываем иконку загрузки
        document.getElementById('loadingIcon').style.display = 'none';
    }
});