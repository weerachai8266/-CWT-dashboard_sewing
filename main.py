import pymysql
from evdev import InputDevice, categorize, ecodes, list_devices
import select
from datetime import datetime
import pygame
import sys
import os
import threading
import queue

class Scanner:
    def __init__(self):
        print("\nกำลังค้นหาอุปกรณ์...")
        self.device = self.find_scanner()
        if not self.device:
            print("\n❌ ไม่พบอุปกรณ์ที่ใช้งานได้")
            print("โปรดตรวจสอบ:")
            print("1. เสียบ Scanner เรียบร้อยแล้ว")
            print("2. Scanner เปิดทำงานอยู่")
            print("3. ถ้าจำเป็นให้รันด้วย sudo")
            os._exit(1)

        try:
            self.device.read()  # ล้าง events เก่า
            self.device.grab()  # จอง device ไว้ใช้งาน

            import fcntl
            flag = fcntl.fcntl(self.device.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.device.fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)

            print(f"✅ เริ่มใช้งานอุปกรณ์สำเร็จ")
        except Exception as e:
            print(f"❌ ไม่สามารถใช้งานอุปกรณ์ได้: {e}")
            print("ลองรันโปรแกรมด้วย sudo")
            os._exit(1)

        self.buffer = ''
        self.barcode_queue = queue.Queue()
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._barcode_loop, daemon=True)
        self.thread.start()

    def find_scanner(self):
        devices = [InputDevice(path) for path in list_devices()]
        print("\nรายการอุปกรณ์ที่พบทั้งหมด:")
        print("-" * 50)
        for i, dev in enumerate(devices):
            print(f"{i+1}. {dev.path}: {dev.name}")
        print("-" * 50)

        skip_keywords = [
            'consumer control', 'system control', 'mouse', 'dell',
            'vc4-hdmi', 'keyboard system', 'keyboard consumer', 'touchpad'
        ]
        scanner_keywords = [
            'scanner', 'barcode', 'newtologic', 'datalogic',
            'honeywell', 'zebra', 'symbol'
        ]

        available_devices = []
        for dev in devices:
            name = dev.name.lower()
            if any(keyword in name for keyword in skip_keywords):
                continue
            if any(keyword in name for keyword in scanner_keywords):
                available_devices.append(dev)
                continue
            if 'keyboard' in name and not any(skip in name for skip in skip_keywords):
                available_devices.append(dev)

        if not available_devices:
            print("❌ ไม่พบ Scanner หรือ อุปกรณ์ที่ใช้งานได้")
            return None

        if len(available_devices) == 1:
            selected_device = available_devices[0]
            print(f"✅ พบอุปกรณ์ที่ใช้งานได้: {selected_device.path} ({selected_device.name})")
            return selected_device

        print("\nพบหลายอุปกรณ์ที่ใช้งานได้:")
        for i, dev in enumerate(available_devices):
            print(f"{i+1}. {dev.path}: {dev.name}")
        while True:
            try:
                choice = input("\nเลือกอุปกรณ์ (1-" + str(len(available_devices)) + "): ")
                idx = int(choice) - 1
                if 0 <= idx < len(available_devices):
                    selected_device = available_devices[idx]
                    print(f"✅ เลือกใช้: {selected_device.path} ({selected_device.name})")
                    return selected_device
                else:
                    print("❌ กรุณาเลือกหมายเลขที่ถูกต้อง")
            except ValueError:
                print("❌ กรุณาป้อนตัวเลขเท่านั้น")

    def _barcode_loop(self):
        while not self._stop_event.is_set():
            try:
                r, _, _ = select.select([self.device.fd], [], [], 0.01)
                if not r:
                    continue
                for event in self.device.read():
                    if event.type == ecodes.EV_KEY and event.value == 1:
                        if event.code == ecodes.KEY_ENTER:
                            if len(self.buffer) > 0:
                                self.barcode_queue.put(self.buffer)
                                self.buffer = ''
                        else:
                            try:
                                key = ecodes.KEY[event.code].replace('KEY_', '')
                                char = self.translate_key(key)
                                if char:
                                    self.buffer += char
                            except Exception:
                                pass
            except Exception:
                self.buffer = ''
                continue

    def get_barcode(self):
        try:
            return self.barcode_queue.get_nowait()
        except queue.Empty:
            return None

    def translate_key(self, key):
        try:
            if key.isdigit():
                return key
            elif len(key) == 1 and key.isalpha():
                return key.upper()
            special_chars = {
                'MINUS': '-', 'EQUAL': '=', 'LEFTBRACE': '[', 'RIGHTBRACE': ']',
                'SEMICOLON': ';', 'APOSTROPHE': "'", 'GRAVE': '`', 'BACKSLASH': '\\',
                'COMMA': ',', 'DOT': '.', 'SLASH': '/'
            }
            if key in special_chars:
                return special_chars[key]
            print(f"Unknown key: {key}")
            return None
        except Exception as e:
            print(f"❌ แปลงคีย์ผิดพลาด: {e}")
            return None

    def cleanup(self):
        self._stop_event.set()
        if hasattr(self, 'device') and self.device:
            self.device.ungrab()

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

    def insert_ok(self, item_code):
        item_code = item_code.upper()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "INSERT INTO sewing_3rd (item, qty, status, created_at) VALUES (%s, 1, 10, %s)"
        try:
            self.cursor.execute(sql, (item_code, now))
            self.db.commit()
            print(f"✅ บันทึกข้อมูล: {item_code}")
        except pymysql.err.IntegrityError as e:
            print(f"❌ ไม่สามารถบันทึก: {item_code} (อาจซ้ำ)")

    def get_target_from_cap(self):
        try:
            sql = "SELECT `3rd` FROM sewing_cap ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result else "00"
        except Exception as e:
            print(f"Error fetching cap target: {e}")
            return "00"

    def get_man_plan(self):
        try:
            sql = "SELECT `3rd_plan` FROM sewing_man ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result else "00"
        except Exception as e:
            print(f"Error fetching man plan: {e}")
            return "00"

    def get_man_act(self):
        try:
            sql = "SELECT `3rd_act` FROM sewing_man ORDER BY created_at DESC LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result else "00"
        except Exception as e:
            print(f"Error fetching man act: {e}")
            return "00"

    def get_output_count(self):
        try:
            sql = "SELECT COUNT(`qty`) FROM `sewing_3rd` WHERE DATE(created_at) = CURDATE() LIMIT 1"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
            return str(result[0]) if result else "00"
        except Exception as e:
            print(f"Error fetching output count: {e}")
            return "00"

    def close(self):
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'db') and self.db:
                self.db.close()
            print("✅ ปิดการเชื่อมต่อฐานข้อมูล")
        except Exception as e:
            print(f"❌ ปิดการเชื่อมต่อฐานข้อมูลผิดพลาด: {e}")

class Dashboard:
    def __init__(self, db_manager, scanner):
        self.db_manager = db_manager
        self.scanner = scanner
        pygame.init()
        self.UPDATE_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.UPDATE_EVENT, 1000)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Production Dashboard")
        self.width, self.height = self.screen.get_size()
        self.setup_fonts()
        self.setup_colors()
        self.last_ok_barcode = ""
        self.error_message = ""
        self.show_error = False

        self.target_value = self.db_manager.get_target_from_cap()
        self.man_plan = self.db_manager.get_man_plan()
        self.man_act = self.db_manager.get_man_act()
        self.output_value = self.db_manager.get_output_count()

    def setup_fonts(self):
        self.font_header = pygame.font.SysFont('Arial', 50, bold=True)
        self.font_label = pygame.font.SysFont('Arial', 40, bold=True)
        self.font_percent = pygame.font.SysFont('Arial', 80, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 30, bold=True)
        self.font_big = pygame.font.SysFont('Consolas', 100, bold=True)
        self.font_TH = pygame.font.SysFont('FreeSerif', 80, bold=True) # TH

    def setup_colors(self):
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 175, 0)
        self.GREY = (128, 128, 128)
        self.RED = (175, 0, 0)

    def draw_box(self, rect, fill_color=None, border_color=None, border=3, radius=10):
        if fill_color is None: fill_color = self.BLACK
        if border_color is None: border_color = self.GREY
        pygame.draw.rect(self.screen, fill_color, rect, border_radius=radius)
        pygame.draw.rect(self.screen, border_color, rect, border, border_radius=radius)

    def draw_text(self, text, font, pos, color=None, align="left"):
        if color is None:
            color = self.WHITE
        surface = font.render(str(text), True, color)
        rect = surface.get_rect()
        x, y = pos

        if align == "center":
            rect.center = (x, y)
        elif align == "right":
            rect.topright = (x, y)
        else:  # "left"
            rect.topleft = (x, y)

        self.screen.blit(surface, rect)

    def process_ok_scan(self, barcode):
        if 12 < len(barcode) <= 17:
            self.last_ok_barcode = barcode
            self.db_manager.insert_ok(barcode)
            self.show_error = False
            self.error_message = ""
        else:
            if len(barcode) <= 15:
                self.error_message = "ไม่บันทึก กรุณาสแกนใหม่ (" + barcode +")"
                # self.error_message = barcode
            else:
                self.error_message = "ไม่บันทึก กรุณาสแกนใหม่ ("+ barcode +")"
                # self.error_message = barcode
            self.show_error = True

    def draw_dashboard(self):
        self.screen.fill(self.BLACK)

        # Header
        self.draw_box((30, 20, 1300, 100))
        self.draw_text("Line Name : 3RD", self.font_header, (50, 45))

        # DateTime
        self.draw_box((1350, 20, 538, 100))
        now = datetime.now()
        self.draw_text(" DATE : " + now.strftime("%d/%m/%Y"), self.font_small, (1380, 35))
        self.draw_text(" TIME  : " + now.strftime("%H:%M:%S"), self.font_small, (1380, 75))

        # Barcode Display
        self.draw_box((30, 150, self.width - 60, 170))
        self.draw_text("Part", self.font_label, (50, 160))
        if self.show_error:
            self.draw_text(self.error_message, self.font_TH, (170, 210), self.RED)
        else:
            self.draw_text(self.last_ok_barcode, self.font_big, (170, 210))

        # Left Panel
        gab_left_label  =   85
        gab_left_draw   =   85
        gab_left_value  =   85
        self.draw_box((30, 350, 915, 730))
        self.draw_text("Efficiency", self.font_header, (50, 370))
        pygame.draw.line(self.screen, self.GREY, (50, 430), (910, 430), 1)
        self.draw_text(f"{self.eff}%", self.font_percent, (910, 360), self.GREEN, align="right")

        self.draw_text("Output", self.font_header, (50, 370+(gab_left_label*1)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*1)), (910, 430+(gab_left_draw*1)), 1)
        self.draw_text(self.output_value, self.font_percent, (910, 360+(gab_left_value*1)), self.GREEN, align="right")

        self.draw_text("Target / hr", self.font_header, (50, 370+(gab_left_label*2)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*2)), (910, 430+(gab_left_draw*2)), 1)
        self.draw_text(self.target_value, self.font_percent, (910, 360+(gab_left_value*2)), self.GREEN, align="right")

        self.draw_text("Diff", self.font_header, (50, 370+(gab_left_label*3)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*3)), (910, 430+(gab_left_draw*3)), 1)
        self.draw_text("00", self.font_percent, (910, 360+(gab_left_value*3)), self.GREEN, align="right")

        self.draw_text("OK", self.font_header, (50, 370+(gab_left_label*4)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*4)), (910, 430+(gab_left_draw*4)), 1)
        self.draw_text("00", self.font_percent, (910, 360+(gab_left_value*4)), self.GREEN, align="right")

        self.draw_text("NG", self.font_header, (50, 370+(gab_left_label*5)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*5)), (910, 430+(gab_left_draw*5)), 1)
        self.draw_text("00", self.font_percent, (910, 360+(gab_left_value*5)), self.GREEN, align="right")

        self.draw_text("Man", self.font_header, (50, 370+(gab_left_label*6)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*6)), (910, 430+(gab_left_draw*6)), 1)
        self.draw_text(f"{self.man_act} / {self.man_plan}", self.font_percent, (910, 360+(gab_left_value*6)), self.GREEN, align="right")

        self.draw_text("spare", self.font_header, (50, 370+(gab_left_label*7)))
        pygame.draw.line(self.screen, self.GREY, (50, 430+(gab_left_draw*7)), (910, 430+(gab_left_draw*7)), 1)
        self.draw_text("00", self.font_percent, (910, 360+(gab_left_value*7)), self.GREEN, align="right")

        # Right Panel
        gap_right_label =   45
        gap_right_value =   80
        # gap_right_
        px_right_x  =   995
        px_right_y  =   380
        self.draw_box((975, 350, 915, 730))
        self.draw_text("08:00", self.font_label, (px_right_x, px_right_y))
        self.draw_text("09:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*1)))
        self.draw_text("10:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*2)))
        self.draw_text("11:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*3)))
        self.draw_text("12:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*4)))
        self.draw_text("13:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*5)))
        self.draw_text("14:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*6)))
        self.draw_text("15:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*7)))
        self.draw_text("16:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*8)))
        self.draw_text("17:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*9)))
        self.draw_text("18:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*10)))
        self.draw_text("19:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*11)))
        self.draw_text("20:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*12)))
        self.draw_text("21:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*13)))
        self.draw_text("22:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*14)))
        # self.draw_text("23:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*15)))
        # self.draw_text("23:00", self.font_label, (px_right_x, px_right_y+(gap_right_label*16)))

        self.draw_text("00" + " Pcs", self.font_label, (1300, px_right_y), self.GREEN, align="right")
        self.draw_text("00" + " Pcs", self.font_label, (1300, px_right_y+(gap_right_label*1)), self.GREEN, align="right")
        self.draw_text("00" + " Pcs", self.font_label, (1300, px_right_y+(gap_right_label*2)), self.GREEN, align="right")
        self.draw_text("00" + " Pcs", self.font_label, (1300, px_right_y+(gap_right_label*3)), self.GREEN, align="right")
        self.draw_text("00" + " Pcs", self.font_label, (1300, px_right_y+(gap_right_label*4)), self.GREEN, align="right")
        # self.draw_text("00.00%", self.font_percent, (1575, 360), self.GREEN, False)

        self.draw_text("00.00 %", self.font_label, (1550, px_right_y), self.GREEN, align="right")
        self.draw_text("00.00 %", self.font_label, (1550, px_right_y+(gap_right_label*1)), self.GREEN, align="right")
        self.draw_text("00.00 %", self.font_label, (1550, px_right_y+(gap_right_label*2)), self.GREEN, align="right")
        self.draw_text("00.00 %", self.font_label, (1550, px_right_y+(gap_right_label*3)), self.GREEN, align="right")
        self.draw_text("00.00 %", self.font_label, (1550, px_right_y+(gap_right_label*4)), self.GREEN, align="right")

    def run(self):
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        print("กำลังปิดโปรแกรม...")
                        self.cleanup()
                        pygame.quit()
                        os._exit(0)  # ใช้ os._exit เพื่อปิดโปรแกรมทันที
                    elif event.type == self.UPDATE_EVENT:
                        self.target_value = self.db_manager.get_target_from_cap()
                        self.man_plan = self.db_manager.get_man_plan()
                        self.man_act = self.db_manager.get_man_act()
                        self.output_value = self.db_manager.get_output_count()
                        self.eff = round(float(self.output_value) / float(self.target_value) * 100, 2) if float(self.target_value) != 0 else 0.00

                barcode = self.scanner.get_barcode()
                if barcode:
                    self.process_ok_scan(barcode)

                self.draw_dashboard()
                pygame.display.flip()
        except Exception as e:
            print(f"Dashboard error: {e}")
            os._exit(1)  # ปิดโปรแกรมเมื่อเกิดข้อผิดพลาด

    def cleanup(self):
        try:
            if hasattr(self, 'scanner'):
                self.scanner.cleanup()
        except Exception as e:
            print(f"Dashboard cleanup error: {e}")

if __name__ == '__main__':
    db_manager = None
    scanner = None
    dashboard = None
    
    try:
        print("กำลังเริ่มต้นโปรแกรม...")
        db_manager = DatabaseManager()
        scanner = Scanner()
        dashboard = Dashboard(db_manager, scanner)
        dashboard.run()
    except Exception as e:
        print(f"❌ โปรแกรมผิดพลาด: {e}")
    finally:
        try:
            if dashboard:
                dashboard.cleanup()
            if db_manager:
                db_manager.close()
            pygame.quit()
            print("กำลังปิดโปรแกรม...")
            os._exit(0)  # ใช้ os._exit แทน sys.exit
        except Exception as e:
            print(f"❌ ปิดโปรแกรมผิดพลาด: {e}")
            os._exit(1)