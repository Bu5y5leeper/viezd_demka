from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from os import getenv
import logging

app = Flask(__name__)
DB_HOST = getenv('DB_HOST', 'localhost')
DB_NAME = getenv('DB_NAME', 'postgres')
DB_USER = getenv('DB_USER', 'postgres')
DB_PASSWORD = getenv('DB_PASSWORD')

def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        logging.info("Успешное подключение к базе данных")
        return conn
    except Exception as e:
        logging.error(f"Ошибка при подключении к БД: {str(e)}")
        raise

@app.route('/')
def index():
    token = request.cookies.get('token')
    if not token:
        return redirect(url_for('login'), 301)
    return redirect(url_for('notes'), 301)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        if not all(key in data for key in ('username', 'email', 'password')):
            return jsonify({'error': 'Не все поля заполнены'}), 400
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            #Проверка существования пользователя
            cur.execute("""
                SELECT id FROM users 
                WHERE username = %s OR email = %s
            """, (data['username'], data['email']))
            if cur.fetchone():
                return jsonify({'error': 'Пользователь уже существует'}), 400
            # Создание нового пользователя
            hashed_password = generate_password_hash(data['password'])
            cur.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (data['username'], data['email'], hashed_password))
            user_id = cur.fetchone()[0]
            conn.commit()
            token = jwt.encode({
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(days=1)
            }, str(app.config['SECRET_KEY']), algorithm='HS256')
            return jsonify({'token': token})
        except Exception as e:
            if conn:
                conn.rollback()
            logging.error(f"Ошибка при регистрации: {str(e)}")
            return jsonify({'error': 'Произошла ошибка при регистрации'}), 500
        finally:
            if conn:
                cur.close()
                conn.close()
    elif request.method == 'GET':
        return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        data = request.json
        if not all(key in data for key in ('username', 'password')):
            return jsonify({'error': 'Не все поля заполнены'}), 400

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT id, password_hash
                FROM users
                WHERE username = %s
            """, (data['username'],))

            user = cur.fetchone()
            if not user or not check_password_hash(user[1], data['password']):
                return jsonify({'error': 'Неверные учетные данные'}), 401

            token = jwt.encode({
                'user_id': user[0],
                'exp': datetime.utcnow() + timedelta(days=1)
            }, str(app.config['SECRET_KEY']), algorithm='HS256')
            resp = make_response()
            resp.set_cookie('token', token)
            return resp
        except Exception as e:
            logging.warning(f"Ошибка при входе: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            if conn:
                cur.close()
                conn.close()
    elif request.method == 'GET':
        return render_template('login.html')

@app.route('/create_notes', methods=['POST', 'GET'])
def create_note():
    if request.method=='GET':
         return render_template('create_notes.html')
    elif request.method=='POST':
        token = request.cookies.get('token')
        if not token:
            return jsonify({'error': 'Токен отсутствует'}), 401
        try:
            payload = jwt.decode(token, str(app.config['SECRET_KEY']), algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Токен истёк'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Неверный токен'}), 401

        data = request.json
        if not all(key in data for key in ('title', 'content')):
            return jsonify({'error': 'Не все поля заполнены'}), 400

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Проверка существования пользователя
            cur.execute("SELECT id FROM users WHERE id = %s", (payload['user_id'],))
            user = cur.fetchone()
            if not user:
                return jsonify({'error': 'Пользователь не найден'}), 404

            # Создание заметки
            cur.execute("""
                INSERT INTO notes (user_id, title, content, created_at, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, title, content, created_at
            """, (payload['user_id'], data['title'], data['content']))

            note_data = cur.fetchone()
            conn.commit()
            return jsonify({'status': 'created'})
        except Exception as e:
            if conn:
                conn.rollback()
            logging.error(f"Ошибка при создании заметки: {str(e)}")
            return jsonify({'error': 'Произошла ошибка при создании заметки'}), 500
        finally:
            if conn:
                cur.close()
                conn.close()

@app.route('/notes', methods=['GET'])
def show_notes():
    token = request.cookies.get('token')
    if not token:
        return redirect(url_for('login'), 301)
    try:
        payload = jwt.decode(token, str(app.config['SECRET_KEY']), algorithms=['HS256'])

        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT id, title, content, created_at
                FROM notes
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (payload['user_id'],))

            notes_data = cur.fetchall()
            titles=[]
            for i in notes_data:
                titles.append([str(i[0]), i[1]])
            return render_template('notes.html', data=titles)
        except Exception as e:
            logging.error(f"Ошибка при получении заметок: {str(e)}")
            return jsonify({'error': 'Произошла ошибка при получении заметок'}), 500
        finally:
            if conn:
                cur.close()
                conn.close()

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Токен истёк'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Неверный токен'}), 401

@app.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    token = request.cookies.get('token')
    if not token:
        return jsonify({'error': 'Токен отсутствует'}), 401

    try:
        payload = jwt.decode(token, str(app.config['SECRET_KEY']), algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Токен истёк'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Неверный токен'}), 401

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, title, content, created_at, updated_at
            FROM notes
            WHERE id = %s AND user_id = %s""", (note_id, payload['user_id']))
        note_data=cur.fetchone()
        if not note_data:
                return render_template('404.html'), 404

        note = {
            'id': note_data[0],
            'title': note_data[1],
            'content': note_data[2],
            'created_at': note_data[3].strftime('%d.%m.%Y %H:%M'),
            'updated_at': note_data[4].strftime('%d.%m.%Y %H:%M')
        }
        return render_template('display_note.html', note=note)
    except Exception as e:
        logging.error(f"Ошибка при получении заметки: {str(e)}")
        return jsonify({'error': 'Произошла ошибка при получении заметки'}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
