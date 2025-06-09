import pymysql
from evdev import InputDevice, categorize, ecodes, list_devices
import select
from datetime import datetime
import pygame
import sys
import os

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
            sys.exit(1)

        try:
            # ตั้งค่า device
            self.device.read()  # ล้าง events เก่า
            self.device.grab()  # จอง device ไว้ใช้งาน
            
            # เพิ่มการตั้งค่า evdev
            import fcntl
            # ตั้งค่า non-blocking mode
            flag = fcntl.fcntl(self.device.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.device.fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
            
            self.buffer = ''
            self.shift = False
            print(f"✅ เริ่มใช้งานอุปกรณ์สำเร็จ")
        except Exception as e:
            print(f"❌ ไม่สามารถใช้งานอุปกรณ์ได้: {e}")
            print("ลองรันโปรแกรมด้วย sudo")
            sys.exit(1)

        self.buffer = ''
        self.shift = False

    def find_scanner(self):
        devices = [InputDevice(path) for path in list_devices()]
    
        print("\nรายการอุปกรณ์ที่พบทั้งหมด:")
        print("-" * 50)
        for i, dev in enumerate(devices):
            print(f"{i+1}. {dev.path}: {dev.name}")
        print("-" * 50)

        # คำที่ไม่ต้องการ (ข้าม)
        skip_keywords = [
            'consumer control', 
            'system control', 
            'mouse', 
            'dell',
            'vc4-hdmi',
            'keyboard system',
            'keyboard consumer',
            'touchpad'
        ]
        
        # คำที่เกี่ยวข้องกับ scanner
        scanner_keywords = [
            'scanner',
            'barcode',
            'newtologic',
            'datalogic',
            'honeywell',
            'zebra',
            'symbol'
        ]

        available_devices = []
        
        # ค้นหา Scanner ที่เป็นไปได้
        for dev in devices:
            name = dev.name.lower()
            
            # ข้ามอุปกรณ์ที่ไม่ต้องการ
            if any(keyword in name for keyword in skip_keywords):
                continue
                
            # ถ้าเจอ scanner keyword ให้เพิ่มเข้า list
            if any(keyword in name for keyword in scanner_keywords):
                available_devices.append(dev)
                continue
                
            # ถ้าเป็น keyboard ทั่วไป (ไม่ใช่ consumer/system) ให้เพิ่มเข้า list
            if 'keyboard' in name and not any(skip in name for skip in skip_keywords):
                available_devices.append(dev)

        if not available_devices:
            print("❌ ไม่พบ Scanner หรือ อุปกรณ์ที่ใช้งานได้")
            return None

        if len(available_devices) == 1:
            selected_device = available_devices[0]
            print(f"✅ พบอุปกรณ์ที่ใช้งานได้: {selected_device.path} ({selected_device.name})")
            return selected_device

        # ถ้าพบหลายอุปกรณ์ ให้ผู้ใช้เลือก
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

    def read_barcode(self):
        try:
            # อ่านข้อมูลจาก scanner
            r, _, _ = select.select([self.device.fd], [], [], 0.01)  # 10ms timeout
            
            if not r:  # ถ้าไม่มีข้อมูลเข้ามา
                return None
                
            # อ่านข้อมูลทั้งหมดที่มี
            for event in self.device.read():
                if event.type == ecodes.EV_KEY and event.value == 1:  # Key pressed
                    if event.code == ecodes.KEY_ENTER:
                        if len(self.buffer) > 0:
                            barcode_data = self.buffer
                            # print(f"Scanned: {barcode_data}")  # DEBUG
                            self.buffer = ''  # ล้าง buffer
                            return barcode_data
                    else:
                        # เพิ่มตัวอักษรเข้า buffer
                        try:
                            # แปลง keycode เป็นตัวอักษรตาม translate_key
                            key = ecodes.KEY[event.code].replace('KEY_', '')
                            # print(f"Key pressed: {key}")  # DEBUG
                            char = self.translate_key(key)
                            if char:
                                self.buffer += char
                                print(f"Buffer: {self.buffer}")  # DEBUG
                        except:
                            # print(f"Key error: {e}")  # DEBUG
                            pass
                # elif event.type == ecodes.EV_KEY and event.code in [ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT]:
                #     self.shift = event.value == 1
                
            return None
            
        except Exception as e:
            print(f"Read error: {e}")  # DEBUG
            self.buffer = ''
            return None

    def translate_key(self, key):
        try:
            # จัดการตัวเลข
            if key.isdigit():
                return key

            # จัดการตัวอักษร - เป็นตัวพิมพ์ใหญ่เสมอ
            elif len(key) == 1 and key.isalpha():
                return key.upper()  # ส่งคืนตัวพิมพ์ใหญ่เสมอ ไม่สนใจ shift

            # จัดการเครื่องหมายพิเศษ
            special_chars = {
                'MINUS': '-',
                'EQUAL': '=', 
                'LEFTBRACE': '[',
                'RIGHTBRACE': ']',
                'SEMICOLON': ';',
                'APOSTROPHE': "'",
                'GRAVE': '`',
                'BACKSLASH': '\\',
                'COMMA': ',',
                'DOT': '.',
                'SLASH': '/'
            }
            
            if key in special_chars:
                return special_chars[key]

            # DEBUG: แสดงค่า key ที่ไม่รู้จัก
            print(f"Unknown key: {key}")
            
            return None
        except Exception as e:
            print(f"❌ แปลงคีย์ผิดพลาด: {e}")
            return None
            
    def cleanup(self):
        try:
            # ล้าง buffer ทันทีที่เลิกใช้
            if hasattr(self, 'buffer'):
                self.buffer = ''
            if hasattr(self, 'device') and self.device:
                self.device.ungrab()
        except:
            pass

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
        self.font_TH = pygame.font.SysFont('FreeSerif', 80, bold=True)

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

    def draw_text(self, text, font, pos, color=None, center=False):
        if color is None: color = self.WHITE
        surface = font.render(str(text), True, color)
        rect = surface.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
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
        self.draw_text("PART", self.font_label, (50, 160))
        if self.show_error:
            self.draw_text(self.error_message, self.font_TH, (170, 210), self.RED)
        else:
            self.draw_text(self.last_ok_barcode, self.font_big, (170, 210))

        # Left Panel
        self.draw_box((30, 350, 915, 700))
        self.draw_text("Efficiency", self.font_header, (50, 370))
        pygame.draw.line(self.screen, self.GREY, (50, 430), (910, 430), 1)
        self.draw_text("00.00 %", self.font_percent, (630, 360), self.GREEN, False)

        self.draw_text("Output", self.font_header, (50, 450))
        pygame.draw.line(self.screen, self.GREY, (50, 510), (910, 510), 1)
        self.draw_text(self.output_value, self.font_percent, (630, 440), self.GREEN, False)

        self.draw_text("Target / hr", self.font_header, (50, 530))
        pygame.draw.line(self.screen, self.GREY, (50, 590), (910, 590), 1)
        self.draw_text(self.target_value, self.font_percent, (630, 520), self.GREEN, False)

        self.draw_text("Man", self.font_header, (50, 610))
        pygame.draw.line(self.screen, self.GREY, (50, 670), (910, 670), 1)
        self.draw_text(f"{self.man_act} / {self.man_plan}", self.font_percent, (630, 600), self.GREEN, False)

        # Right Panel
        self.draw_box((975, 350, 915, 700))

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

                barcode = self.scanner.read_barcode()
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