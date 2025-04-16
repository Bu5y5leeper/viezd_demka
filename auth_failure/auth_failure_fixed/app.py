from flask import Flask, request, make_response, redirect, url_for, render_template
from os import getenv
import jwt

app = Flask(__name__)
app.secret_key = getenv('JWT_KEY', 'secret-key')
# Флаг, который нужно будет показать при admin=True
FLAG = "FLAG{Y0r_Cook1e_Ta5K}"
ADMIN_USERNAME=getenv('ADMIN_USR', 'admin')
ADMIN_PASS=getenv('ADMIN_PASS', 'admin')

# Главная страница
@app.route('/')
def index():
    # Получаем значение cookie 'admin'
    admin_cookie = request.cookies.get('token')
    # Проверяем значение cookie
    if admin_cookie:
        try:
            if jwt.decode(admin_cookie, app.secret_key, algorithms='HS256')['user'] == 'admin':
                return render_template('index.html', flag=FLAG)  # Показываем флаг, если admin=True
        except:
            return render_template('index.html', flag=None)
    return render_template('index.html', flag=None)  # Страница без флага

# Маршрут для установки начальной cookie
@app.route('/setcookie', methods=['POST'])
def set_cookie():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Пожалуйста, заполните все поля', 'error')
        return redirect(url_for('index'))
    # Создаем ответ
    resp = make_response(redirect(url_for('index')))
    if username == ADMIN_USERNAME and password == ADMIN_PASS:
        resp.set_cookie('token', jwt.encode({'user':'admin'}, app.secret_key, algorithm='HS256'))
        return resp
    # Устанавливаем cookie admin=False
    resp.set_cookie('token', '')

    return resp

# Запускаем сервер
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=0)
