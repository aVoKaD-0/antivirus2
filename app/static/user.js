document.querySelector('#registerForm form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    document.getElementById('loadingIcon').style.display = 'block';

    try {
        const password = document.getElementById('password').value;
        const message = document.getElementById('message');
        const loading = document.querySelector('.loading');
        flag = 0;
        
        if (!password) {
            message.textContent = 'Пожалуйста, заполните все поля.';
            flag = 1;
        }
        if (password.length < 8) {
            message.textContent = 'Длина пароля должна быть больше 8 символов.';
            flag = 1;
        }
        if (!/[A-Za-z0-9]/.test(password) || !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
            message.textContent = 'Пароль должен содержать прописные, заглавные буквы, цифры и специальные символы.';
            flag = 1;
        }
        if (flag == 1) {
            message.textContent = '';
            message.style.color = 'red';
            loading.style.display = 'block';
            document.getElementById('resetButton').disabled = true;
            flag = 1;
        }

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
        document.getElementById('loadingIcon').style.display = 'none';
    }
});

function changeTitle(title) {
    document.title = title;
    document.getElementById('pageTitle').innerText = title;
}

document.getElementById('registerTab').addEventListener('click', function() {
    document.getElementById('registerForm').style.display = 'block';
    document.getElementById('loginForm').style.display = 'none';
    changeTitle('Регистрация');
});

document.getElementById('loginTab').addEventListener('click', function() {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
    changeTitle('Вход');
});

function togglePassword(fieldId, button) {
    const field = document.getElementById(fieldId);
    if (field.type === "password") {
        field.type = "text";
        button.textContent = "🙈"; // Изменяем иконку на закрытый глаз
    } else {
        field.type = "password";
        button.textContent = "👁"; // Изменяем иконку на открытый глаз
    }
}