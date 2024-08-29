from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import RealDictCursor


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def connect_db():
    return psycopg2.connect(DATABASE_URL)


def get_urls_db():
    conn = connect_db()
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute("SELECT urls.name, urls.id, last_url_checks.created_at,\
                    last_url_checks.status_code FROM urls\
                    LEFT JOIN last_url_checks\
                    ON urls.id = last_url_checks.url_id\
                    ORDER BY urls.id DESC;")
        all_urls = curs.fetchall()
    conn.close()
    return all_urls


def get_url_db(id):
    conn = connect_db()
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute(
            "SELECT * FROM urls WHERE id=%s;", (id,))
        res = curs.fetchall()
    url = res[0] if res else None
    conn.close()
    return url


def get_url_checks_db(id):
    conn = connect_db()
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute("SELECT * FROM url_checks WHERE url_id=%s \
                    ORDER BY id DESC;", (id,))
        checks = curs.fetchall()
    conn.close()
    return checks


def get_id_url_db(url):
    conn = connect_db()
    with conn.cursor() as curs:
        curs.execute(
            "SELECT id FROM urls WHERE name=%s;", (url,))
        res = curs.fetchone()
    id_url = res[0] if res else None
    conn.close()
    return id_url


def add_new_url_db(url):
    conn = connect_db()
    with conn.cursor() as curs:
        curs.execute(
            "INSERT INTO urls (name, created_at) VALUES (%s, now()) \
                RETURNING id;", (url, ))
        id_url = curs.fetchone()[0]
    conn.commit()
    conn.close()
    return id_url


def get_name_url_db(id):
    conn = connect_db()
    with conn.cursor() as curs:
        curs.execute(
            "SELECT name FROM urls WHERE id=%s;", (id, ))
        url = curs.fetchone()[0]
    conn.close()
    return url


def add_new_check_db(id, status, parsed_url):
    conn = connect_db()
    with conn.cursor() as curs:
        curs.execute(
            "INSERT INTO url_checks\
            (url_id, created_at, status_code, h1, title, description)\
            VALUES (%s, now(), %s, %s, %s, %s) RETURNING created_at;",
            (id, status, parsed_url['h1'], parsed_url['title'], parsed_url['description'], ))
        created_at = curs.fetchone()[0]
    conn.commit()
    conn.close()
    return created_at


def get_last_check_db(id):
    conn = connect_db()
    with conn.cursor() as curs:
        curs.execute(
            "SELECT id FROM last_url_checks WHERE url_id=%s;", (id, ))
        res = curs.fetchone()
    check = res[0] if res else None
    conn.close()
    return check


def update_last_check_db(id, created_at, status):
    conn = connect_db()
    with conn.cursor() as curs:
        curs.execute(
            "UPDATE last_url_checks\
            SET created_at=%s, status_code=%s\
            WHERE url_id=%s;", (created_at, status, id, ))
    conn.commit()
    conn.close()


def add_last_check_db(id, created_at, status):
    conn = connect_db()
    with conn.cursor() as curs:
        curs.execute(
            "INSERT INTO last_url_checks\
            (url_id, created_at, status_code)\
            VALUES (%s, %s, %s);", (id, created_at, status))
    conn.commit()
    conn.close()


def last_check_db(id, created_at, status):
    check = get_last_check_db(id)
    if check is not None:
        update_last_check_db(id, created_at, status)
    else:
        add_last_check_db(id, created_at, status)
