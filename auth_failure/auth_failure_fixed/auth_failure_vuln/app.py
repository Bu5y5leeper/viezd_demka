from flask import Flask, request, make_response, redirect, url_for, render_template

app = Flask(__name__)

# Флаг, который нужно будет показать при admin=True
FLAG = "FLAG{Y0r_Cook1e_Ta5K}"

# Главная страница
@app.route('/')
def index():
    # Получаем значение cookie 'admin'
    admin_cookie = request.cookies.get('admin', 'False')

    # Проверяем значение cookie
    if admin_cookie == 'True':
        return render_template('index.html', flag=FLAG)  # Показываем флаг, если admin=True
    else:
        return render_template('index.html', flag=None)  # Страница без флага

# Стартовая страница для установки cookie
@app.route('/start')
def start():
    return render_template('start.html')

# Маршрут для установки начальной cookie
@app.route('/setcookie')
def set_cookie():
    # Создаем ответ
    resp = make_response(redirect(url_for('index')))
    
    # Устанавливаем cookie admin=False
    resp.set_cookie('admin', 'False')
    
    return resp

# Запускаем сервер
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=0)
