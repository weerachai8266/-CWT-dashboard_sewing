import pymysql
from pymysql import cursors
import logging
from utils.logger import setup_logger
import datetime

logger = setup_logger('database')

class DatabaseManager:
    def __init__(self, current_user):
        self.db_config = {
            'host': '192.168.0.14',
            'user': 'sew_py',
            'password': 'cwt258963',
            'db': 'automotive',
            'charset': 'utf8mb4',
            'cursorclass': cursors.DictCursor
        }
        self._setup_connection()
        self.current_user = current_user

    def _setup_connection(self):
        try:
            self.connection = pymysql.connect(**self.db_config)
            logger.info("Database connection created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            raise

    def get_connection(self):
        if not self.connection.open:
            self._setup_connection()
        return self.connection

    def insert_ok(self, barcode):
        query = "INSERT INTO sewing_3rd (barcode, datetime, user) VALUES (%s, NOW(), %s)"
        self._execute_query(query, (barcode, self.current_user))

    def insert_qc(self, barcode):
        query = "INSERT INTO qc_3rd (barcode, datetime, user) VALUES (%s, NOW(), %s)"
        self._execute_query(query, (barcode, self.current_user))

    def _execute_query(self, query, params=None):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
            conn.commit()
            logger.info(f"Query executed successfully by user {self.current_user}")
        except Exception as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
            raise