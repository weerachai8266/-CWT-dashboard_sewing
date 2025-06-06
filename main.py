import pymysql
from evdev import InputDevice, categorize, ecodes
import select
from datetime import datetime
import pygame
import sys

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
        except Exception as e:
            print(f"Database connection failed: {e}")
            sys.exit(1)

    def insert_ok(self, item_code):
        item_code = item_code.upper()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO sewing_3rd (item, qty, status, created_at) VALUES (%s, 1, 10, %s)"
        try:
            self.cursor.execute(sql, (item_code, now))
            self.db.commit()
            print(f"[OK] รับงานเข้าระบบ: {item_code}")
        except pymysql.err.IntegrityError as e:
            print(f"[ERROR] ไม่สามารถเพิ่ม: {item_code} (อาจซ้ำ)")

    def update_ng(self, item_code):
        item_code = item_code.upper()
        today = datetime.now().strftime('%Y-%m-%d')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql_select = """
            SELECT id FROM sewing_3rd
            WHERE item = %s AND status = 10 AND DATE(created_at) = %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        self.cursor.execute(sql_select, (item_code, today))
        result = self.cursor.fetchone()
        if result:
            sql_update = "UPDATE sewing_3rd SET status = 20, updated_at = %s WHERE id = %s"
            self.cursor.execute(sql_update, (now, result[0]))
            self.db.commit()
            print(f"[NG] ตรวจชิ้นงานเสีย: {item_code}")
        else:
            sql_insert = "INSERT INTO sewing_3rd (item, qty, status, created_at) VALUES (%s, 1, 20, %s)"
            self.cursor.execute(sql_insert, (item_code, now))
            self.db.commit()
            print(f"[NG] เพิ่มใหม่ (ไม่มีรายการที่อัปเดตได้): {item_code}")

    def get_target_from_cap(self):
        try:
            sql = "SELECT `3rd` FROM sewing_cap ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result else "00"
        except Exception as e:
            print(f"Error fetching cap target: {e}")
            return "00"

    def get_man_count(self):
        try:
            sql = "SELECT `3rd` FROM sewing_man ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result else "00"
        except Exception as e:
            print(f"Error fetching man count: {e}")
            return "00"

    def close(self):
        self.cursor.close()
        self.db.close()

class BarcodeReader:
    def __init__(self, ok_path='/dev/input/scan_ok', ng_path='/dev/input/scan_ng'):
        self.scanner_ok = InputDevice(ok_path)
        self.scanner_ng = InputDevice(ng_path)
        self.scanner_ok.grab()
        self.scanner_ng.grab()
        self.barcode_buffers = {
            self.scanner_ok.fd: '',
            self.scanner_ng.fd: ''
        }
        self.shift_states = {
            self.scanner_ok.fd: False,
            self.scanner_ng.fd: False
        }
    def cleanup(self):
        self.scanner_ok.ungrab()
        self.scanner_ng.ungrab()

class Dashboard:
    def __init__(self, db_manager, barcode_reader):
        self.db_manager = db_manager
        self.barcode_reader = barcode_reader
        pygame.init()
        self.UPDATE_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.UPDATE_EVENT, 1000)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Production Dashboard")
        self.width, self.height = self.screen.get_size()
        self.setup_fonts()
        self.setup_colors()
        self.last_ok_barcode = ""
        self.last_ng_barcode = ""
        self.target_value = self.db_manager.get_target_from_cap()
        self.man_value = self.db_manager.get_man_count()

    def setup_fonts(self):
        self.font_header = pygame.font.SysFont('Arial', 50, bold=True)
        self.font_label = pygame.font.SysFont('Arial', 40, bold=True)
        self.font_percent = pygame.font.SysFont('Arial', 80, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 30, bold=True)

    def setup_colors(self):
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 175, 0)

    def draw_box(self, rect, fill_color=None, border_color=None, border=3, radius=10):
        if fill_color is None: fill_color = self.BLACK
        if border_color is None: border_color = self.WHITE
        pygame.draw.rect(self.screen, fill_color, rect, border_radius=radius)
        pygame.draw.rect(self.screen, border_color, rect, border, border_radius=radius)

    def draw_text(self, text, font, pos, color=None, center=False):
        if color is None: color = self.WHITE
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        self.screen.blit(surface, rect)

    def process_ok_scan(self, barcode):
        self.last_ok_barcode = barcode
        self.db_manager.insert_ok(barcode)

    def process_ng_scan(self, barcode):
        self.last_ng_barcode = barcode
        self.db_manager.update_ng(barcode)

    def run(self):
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                    ):
                        return
                    elif event.type == self.UPDATE_EVENT:
                        self.target_value = self.db_manager.get_target_from_cap()
                        self.man_value = self.db_manager.get_man_count()

                r, _, _ = select.select([self.barcode_reader.scanner_ok.fd, self.barcode_reader.scanner_ng.fd], [], [], 0)
                for fd in r:
                    device = self.barcode_reader.scanner_ok if fd == self.barcode_reader.scanner_ok.fd else self.barcode_reader.scanner_ng
                    for event in device.read():
                        if event.type == ecodes.EV_KEY:
                            key_event = categorize(event)
                            if key_event.keystate == 1:  # Key down
                                keycode = key_event.keycode
                                if isinstance(keycode, list):
                                    keycode = keycode[0]

                                if keycode in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                                    self.barcode_reader.shift_states[fd] = True
                                    continue

                                if keycode == 'KEY_ENTER':
                                    barcode = self.barcode_reader.barcode_buffers[fd].upper()
                                    if fd == self.barcode_reader.scanner_ok.fd:
                                        self.process_ok_scan(barcode)
                                    else:
                                        self.process_ng_scan(barcode)
                                    self.barcode_reader.barcode_buffers[fd] = ''
                                    continue

                                key = keycode.replace('KEY_', '')
                                char = ''
                                if key.isdigit():
                                    char = key
                                elif key == 'MINUS':
                                    char = '_' if self.barcode_reader.shift_states[fd] else '-'
                                elif len(key) == 1 and key.isalpha():
                                    char = key.upper() if self.barcode_reader.shift_states[fd] else key.lower()

                                if char:
                                    self.barcode_reader.barcode_buffers[fd] += char

                                self.barcode_reader.shift_states[fd] = False

                self.draw_dashboard()
                pygame.display.flip()
        finally:
            self.barcode_reader.cleanup()
            self.db_manager.close()
            pygame.quit()

    def draw_dashboard(self):
        self.screen.fill(self.BLACK)
        self.draw_box((30, 20, 1300, 100))
        self.draw_text("Line 3RD", self.font_header, (50, 45))
        self.draw_box((1350, 20, 538, 100))
        now = datetime.now()
        self.draw_text(f"DATE : {now:%d/%m/%Y}", self.font_small, (1380, 35))
        self.draw_text(f"Time : {now:%H:%M:%S}", self.font_small, (1380, 75))
        self.draw_box((30, 140, 420, 180))
        self.draw_text("Efficiency", self.font_label, (50, 160))
        self.draw_text("00.00 %", self.font_percent, (240, 270), self.GREEN, True)
        self.draw_box((470, 140, 420, 180))
        self.draw_text("Output", self.font_label, (490, 160))
        self.draw_text("00", self.font_percent, (680, 270), self.GREEN, True)
        self.draw_box((910, 140, 420, 180))
        self.draw_text("Target / hr", self.font_label, (930, 160))
        self.draw_text(self.target_value, self.font_percent, (1120, 270), self.GREEN, True)
        self.draw_box((1350, 140, 420, 180))
        self.draw_text("Man", self.font_label, (1370, 160))
        self.draw_text(self.man_value, self.font_percent, (1580, 270), self.GREEN, True)
        self.draw_box((30, 350, self.width - 60, 80))
        self.draw_text(self.last_ok_barcode, self.font_label, (50, 375))

if __name__ == '__main__':
    db_manager = DatabaseManager()
    barcode_reader = BarcodeReader()
    dashboard = Dashboard(db_manager, barcode_reader)
    dashboard.run()