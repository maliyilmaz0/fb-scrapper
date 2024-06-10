import sys
import psycopg2


def get_cursor(dictionary=False, autocommit=True):
    try:
        conn = psycopg2.connect(
            database="scrapper",
            user="postgres",
            password="1234rrrR",
            host="127.0.0.1",
            port="5432",
        )
        conn.autocommit = autocommit
        if dictionary:
            from psycopg2.extras import RealDictCursor

            return conn.cursor(cursor_factory=RealDictCursor)
        else:
            return conn.cursor()

    except Exception as err:
        exception_types, exception_objects, exception_tracebacks = sys.exc_info()
        exception_type = str(exception_types).split("'")[1]
        exception_file = exception_tracebacks.tb_frame.f_code.co_filename
        exception_line = exception_tracebacks.tb_lineno
        print("generals/db.py: PostgreSQL Exception: " + str(err))
        print(" Exception Type: ", exception_type)
        print(" Exception Line: ", exception_line)
        print(" Exception File: ", exception_file)
