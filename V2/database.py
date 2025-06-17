import pymysql
import sys
from datetime import datetime, timedelta, time

BREAK_PERIODS = [
    (time(10, 0), time(10, 10)),
    (time(12, 10), time(13, 10)),
    (time(15, 0), time(15, 10)),
    (time(17, 0), time(17, 30)),
]

def is_break(dt):
    t = dt.time() if hasattr(dt, "time") else dt
    for start, end in BREAK_PERIODS:
        if start <= t < end:
            return True
    return False

def working_minutes_in_hour(hour):
    count = 0
    current = datetime(2000,1,1, hour,0)
    end = datetime(2000,1,1, hour+1,0)
    while current < end:
        if not is_break(current):
            count += 1
        current += timedelta(minutes=1)
    return count

class DatabaseManager:
    def __init__(self):
        try:
            self.db = pymysql.connect(
                host="192.168.0.14",
                user="sew_py",
                password="cwt258963",
                database="automotive"
            )
            self.cursor = self.db.cursor()
            print("✅ เชื่อมต่อฐานข้อมูลสำเร็จ")
        except Exception as e:
            print(f"❌ เชื่อมต่อฐานข้อมูลล้มเหลว: {e}")
            sys.exit(1)

    def insert_pd(self, item_code):
        item_code = item_code.upper()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO sewing_3rd (item, qty, status, created_at) VALUES (%s, 1, 10, %s)"
        try:
            self.cursor.execute(sql, (item_code, now))
            self.db.commit()
            print(f"✅ บันทึกข้อมูล: {item_code}")
        except pymysql.err.IntegrityError as e:
            print(f"❌ ไม่สามารถบันทึก: {item_code} (อาจซ้ำ)")

    def insert_qc(self, item_code):
        item_code = item_code.upper()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO qc_3rd (item, qty, status, created_at) VALUES (%s, 1, 10, %s)"
        try:
            self.cursor.execute(sql, (item_code, now))
            self.db.commit()
            print(f"✅ QC บันทึกข้อมูล: {item_code}")
        except pymysql.err.IntegrityError as e:
            print(f"❌ QC ไม่สามารถบันทึก: {item_code} (อาจซ้ำ)")

    def get_target_from_cap(self):
        try:
            sql = "SELECT `3rd` FROM sewing_cap ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching cap target: {e}")
            return "0"

    def get_man_plan(self):
        try:
            sql = "SELECT `3rd_plan` FROM sewing_man ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching man plan: {e}")
            return "0"

    def get_man_act(self):
        try:
            sql = "SELECT `3rd_act` FROM sewing_man ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching man act: {e}")
            return "0"

    def get_output_count_pd(self):
        try:
            sql = "SELECT COUNT(`qty`) FROM `sewing_3rd` WHERE DATE(created_at) = CURDATE() LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching output count: {e}")
            return "0"

    def get_output_count_qc(self):
        try:
            sql = "SELECT COUNT(`qty`) FROM `qc_3rd` WHERE DATE(created_at) = CURDATE() LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result and result[0] is not None else "0"
        except Exception as e:
            print(f"Error fetching output count: {e}")
            return "0"

    def get_hourly_output(self):
        sql = """
            SELECT HOUR(created_at) AS hr, COUNT(*) AS pcs
            FROM sewing_3rd
            WHERE DATE(created_at) = CURDATE()
            GROUP BY hr
            ORDER BY hr
        """
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            output = {int(row[0]): int(row[1]) for row in results}
            return output
        except Exception as e:
            print(f"Error fetching hourly output: {e}")
            return {}
            
    def get_hourly_output_detailed(self, for_date=None):
        if not for_date:
            for_date = datetime.now().strftime("%Y-%m-%d")
        sql = """
            SELECT HOUR(created_at), MINUTE(created_at)
            FROM sewing_3rd
            WHERE DATE(created_at) = %s
        """
        self.cursor.execute(sql, (for_date,))
        results = self.cursor.fetchall()
        hourly_minutes = {}
        for hr, mn in results:
            dt = datetime(2000,1,1,hr,mn)
            if not is_break(dt):
                hourly_minutes.setdefault(hr, set()).add(mn)
        hourly_output = {hr: len(mns) for hr, mns in hourly_minutes.items()}
        return hourly_output

    def get_hourly_qc_output(self):
        sql = """
            SELECT HOUR(created_at) AS hr, COUNT(*) AS pcs
            FROM qc_3rd
            WHERE DATE(created_at) = CURDATE()
            GROUP BY hr
            ORDER BY hr
        """
        try:
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            output = {int(row[0]): int(row[1]) for row in results}
            return output
        except Exception as e:
            print(f"Error fetching hourly output: {e}")
            return {}

    def get_hourly_qc_output_detailed(self, for_date=None):
        if not for_date:
            for_date = datetime.now().strftime("%Y-%m-%d")
        sql = """
            SELECT HOUR(created_at), MINUTE(created_at)
            FROM qc_3rd
            WHERE DATE(created_at) = %s
        """
        self.cursor.execute(sql, (for_date,))
        results = self.cursor.fetchall()
        hourly_minutes = {}
        for hr, mn in results:
            dt = datetime(2000, 1, 1, hr, mn)
            if not is_break(dt):
                hourly_minutes.setdefault(hr, set()).add(mn)
        hourly_output = {hr: len(mns) for hr, mns in hourly_minutes.items()}
        return hourly_output

    def close(self):
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'db') and self.db:
                self.db.close()
            print("✅ ปิดการเชื่อมต่อฐานข้อมูล")
        except Exception as e:
            print(f"❌ ปิดการเชื่อมต่อฐานข้อมูลผิดพลาด: {e}")