from flask import Flask, render_template, url_for, make_response
from dotenv import load_dotenv
from flask import request, redirect, flash, get_flashed_messages
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import validators
from urllib.parse import urlparse, urlunparse
import requests
from bs4 import BeautifulSoup


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    new_url = {'url': ''}
    return render_template(
        'pages/index.html',
        url=new_url,
    )


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html'), 404


@app.route('/urls')
def get_urls():
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute("SELECT urls.name, urls.id, last_url_checks.created_at,\
                    last_url_checks.status_code FROM urls\
                    LEFT JOIN last_url_checks\
                    ON urls.id = last_url_checks.url_id\
                    ORDER BY urls.id DESC;")
        all_urls = curs.fetchall()
    return render_template(
        'pages/urls.html',
        urls=all_urls
    )


def validate_url(url):
    if validators.url(url) and len(url) <= 255:
        return True
    return False


def normalize_url(url):
    parsed_url = urlparse(url)
    return urlunparse((parsed_url.scheme, parsed_url.hostname, '', '', '', ''))


@app.route('/urls/<int:id>')
def get_url(id):
    good_messages = get_flashed_messages(
        with_categories=True, category_filter='success')
    bad_messages = get_flashed_messages(
        with_categories=True, category_filter='info')
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute("SELECT * FROM urls WHERE id=%s;", (id,))
        url = curs.fetchall()[0]
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute("SELECT * FROM url_checks WHERE url_id=%s \
                    ORDER BY id DESC;", (id,))
        checks = curs.fetchall()
    return render_template(
        'pages/url.html',
        url=url,
        checks=checks,
        good_messages=good_messages,
        bad_messages=bad_messages
        )


@app.post('/urls')
def urls_post():
    data = request.form.to_dict()
    if validate_url(data['url']):
        url = normalize_url(data['url'])
        with conn.cursor() as curs:
            curs.execute(
                "SELECT id FROM urls WHERE name=%s;", (url,))
            res = curs.fetchone()
        id_url = res[0] if res else None
        if id_url is not None:
            flash('Страница уже существует', 'info')
            return redirect(url_for('get_url', id=id_url))
        with conn.cursor() as curs:
            curs.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, now()) \
                    RETURNING id;", (url, ))
            id_url = curs.fetchone()[0]
        conn.commit()
        response = make_response(redirect(url_for('get_url', id=id_url)))
        flash('Страница успешно добавлена', 'success')
        return response
    else:
        flash('Некорректный URL', 'error')
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'pages/index.html',
            url=data,
            messages=messages,
            )


@app.post('/urls/<int:id>/checks')
def post_check(id):
    with conn.cursor() as curs:
        curs.execute(
            "SELECT name FROM urls WHERE id=%s;", (id, ))
        url = curs.fetchone()[0]
    r = requests.get(url)
    status = r.status_code
    if r.raise_for_status() is None:
        soup = BeautifulSoup(r.text, 'html.parser')
        h1 = soup.h1.string if soup.h1 else ''
        title = soup.title.string if soup.title else ''
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'description':
                description = meta.get('content')
        with conn.cursor() as curs:
            curs.execute(
                "INSERT INTO url_checks\
                (url_id, created_at, status_code, h1, title, description)\
                VALUES (%s, now(), %s, %s, %s, %s) RETURNING created_at;",
                (id, status, h1, title, description, ))
            created_at = curs.fetchone()[0]
        conn.commit()
        with conn.cursor() as curs:
            curs.execute(
                "SELECT id FROM last_url_checks WHERE url_id=%s;", (id, ))
            res = curs.fetchone()
        check = res[0] if res else None
        if check is not None:
            with conn.cursor() as curs:
                curs.execute(
                    "UPDATE last_url_checks\
                    SET created_at=%s, status_code=%s\
                    WHERE url_id=%s;", (created_at, status, id, ))
            conn.commit()
        else:
            with conn.cursor() as curs:
                curs.execute(
                    "INSERT INTO last_url_checks\
                    (url_id, created_at, status_code)\
                    VALUES (%s, %s, %s);", (id, created_at, status))
            conn.commit()
        response = make_response(redirect(url_for('get_url', id=id)))
        flash('Страница успешно проверена', 'success')
        return response
    else:
        response = make_response(redirect(url_for('get_url', id=id)))
        flash('Произошла ошибка при проверке', 'error')
        return response
