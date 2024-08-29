from flask import Flask, render_template, url_for, make_response
from dotenv import load_dotenv
from flask import request, redirect, flash, get_flashed_messages
import os
from page_analyzer.utils import validate_url, normalize_url
from page_analyzer.db import (
    get_urls_db, get_url_db, get_url_checks_db, get_id_url_db, add_new_url_db,
    get_name_url_db, add_new_check_db, last_check_db)
from page_analyzer.parser import (
    get_status_code, get_raise_for_status, parser_url)


load_dotenv()
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
def page_not_found():
    return render_template('pages/error.html'), 404


@app.route('/urls')
def get_urls():
    all_urls = get_urls_db()
    return render_template(
        'pages/urls.html',
        urls=all_urls
    )


@app.route('/urls/<int:id>')
def get_url(id):
    good_messages = get_flashed_messages(
        with_categories=True, category_filter='success')
    info_messages = get_flashed_messages(
        with_categories=True, category_filter='info')
    bad_messages = get_flashed_messages(
        with_categories=True, category_filter='error')
    url = get_url_db(id)
    if url is None:
        return page_not_found()
    checks = get_url_checks_db(id)
    return render_template(
        'pages/url.html',
        url=url,
        checks=checks,
        good_messages=good_messages,
        info_messages=info_messages,
        bad_messages=bad_messages
    )


@app.post('/urls')
def urls_post():
    data = request.form.to_dict()
    if validate_url(data['url']):
        url = normalize_url(data['url'])
        id_url = get_id_url_db(url)
        if id_url is not None:
            flash('Страница уже существует', 'info')
            return redirect(url_for('get_url', id=id_url))
        id_url = add_new_url_db(url)
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
        ), 422


@app.post('/urls/<int:id>/checks')
def post_check(id):
    url = get_url_db(id)
    if url is None:
        return page_not_found()
    url = get_name_url_db(id)
    try:
        status = get_status_code(url)
        if get_raise_for_status(url) is None:
            parsed_url = parser_url(url)
            created_at = add_new_check_db(id, status, parsed_url)
            last_check_db(id, created_at, status)
            response = make_response(redirect(url_for('get_url', id=id)))
            flash('Страница успешно проверена', 'success')
            return response
        else:
            response = make_response(redirect(url_for('get_url', id=id)))
            flash('Произошла ошибка при проверке', 'error')
            return response
    except Exception:
        response = make_response(redirect(url_for('get_url', id=id)))
        flash('Произошла ошибка при проверке', 'error')
        return response


if __name__ == '__main__':
    app.run()
