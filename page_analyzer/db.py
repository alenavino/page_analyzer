from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import RealDictCursor


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def connect_db():
    return psycopg2.connect(DATABASE_URL)


def get_dict(sql, param=None):
    if param is None:
        conn = connect_db()
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(sql)
            all = curs.fetchall()
        conn.commit()
        conn.close()
        return all
    else:
        conn = connect_db()
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(sql, param)
            all = curs.fetchall()
        conn.commit()
        conn.close()
        return all


def get_element(sql, param):
    conn = connect_db()
    with conn.cursor() as curs:
        curs.execute(sql, param)
        res = curs.fetchone()
    elem = res[0] if res else None
    conn.commit()
    conn.close()
    return elem


def get_urls_db():
    sql = "SELECT urls.name, urls.id, last_url_checks.created_at,\
        last_url_checks.status_code FROM urls\
        LEFT JOIN last_url_checks\
        ON urls.id = last_url_checks.url_id\
        ORDER BY urls.id DESC;"
    return get_dict(sql)


def get_url_db(id):
    sql = "SELECT * FROM urls WHERE id=%s;"
    param = (id, )
    all = get_dict(sql, param)
    url = all[0] if all else None
    return url


def get_url_checks_db(id):
    sql = "SELECT * FROM url_checks WHERE url_id=%s \
        ORDER BY id DESC;"
    param = (id, )
    return get_dict(sql, param)


def get_id_url_db(url):
    sql = "SELECT id FROM urls WHERE name=%s;"
    param = (url, )
    return get_element(sql, param)


def add_new_url_db(url):
    sql = "INSERT INTO urls (name, created_at) VALUES (%s, now()) \
        RETURNING id;"
    param = (url, )
    return get_element(sql, param)


def get_name_url_db(id):
    sql = "SELECT name FROM urls WHERE id=%s;"
    param = (id, )
    return get_element(sql, param)


def add_new_check_db(id, status, parsed_url):
    sql = "INSERT INTO url_checks\
        (url_id, created_at, status_code, h1, title, description)\
        VALUES (%s, now(), %s, %s, %s, %s) RETURNING created_at;"
    param = (id, status, parsed_url['h1'], parsed_url['title'], parsed_url['description'])
    return get_element(sql, param)


def get_last_check_db(id):
    sql = "SELECT id FROM last_url_checks WHERE url_id=%s;"
    param = (id, )
    return get_element(sql, param)


def update_last_check_db(id, created_at, status):
    sql = "UPDATE last_url_checks SET created_at=%s, status_code=%s\
        WHERE url_id=%s RETURNING id;"
    param = (created_at, status, id)
    return get_element(sql, param)


def add_last_check_db(id, created_at, status):
    sql = "INSERT INTO last_url_checks (url_id, created_at, status_code)\
        VALUES (%s, %s, %s) RETURNING id;"
    param = (id, created_at, status)
    return get_element(sql, param)


def last_check_db(id, created_at, status):
    check = get_last_check_db(id)
    if check is not None:
        update_last_check_db(id, created_at, status)
    else:
        add_last_check_db(id, created_at, status)
