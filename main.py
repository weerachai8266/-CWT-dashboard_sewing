import pymysql
import pygame
import sys
from datetime import datetime
from evdev import InputDevice, categorize, ecodes
import select

class SewingDashboard:
    def __init__(self):
        self.last_ok_barcode = ""
        self.last_ng_barcode = ""

        # Database connection
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

        # Initialize pygame
        pygame.init()
        self.UPDATE_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.UPDATE_EVENT, 1000)

        # Setup display
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Production Dashboard")
        self.width, self.height = self.screen.get_size()

        # Setup scanners
        try:
            self.scanner_ok = InputDevice('/dev/input/scan_ok')
            self.scanner_ng = InputDevice('/dev/input/scan_ng')
            self.scanner_ok.grab()
            self.scanner_ng.grab()
        except Exception as e:
            print(f"Scanner setup failed: {e}")
            sys.exit(1)

        # Scanner buffers
        self.barcode_buffers = {
            self.scanner_ok.fd: '',
            self.scanner_ng.fd: ''
        }

        # Initialize fonts and colors
        self.setup_fonts()
        self.setup_colors()
        
        # Initialize values
        self.target_value = self.get_target_from_cap()
        self.man_value = self.get_man_count()

    def setup_fonts(self):
        self.font_header = pygame.font.SysFont('Arial', 50, bold=True)
        self.font_label = pygame.font.SysFont('Arial', 40, bold=True)
        self.font_percent = pygame.font.SysFont('Arial', 80, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 30, bold=True)

    def setup_colors(self):
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 175, 0)

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

    def handle_scanner_input(self, scanner, callback):
        for event in scanner.read():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                if key_event.keystate == 1:  # Key down
                    if isinstance(key_event.keycode, list):
                        keycode = key_event.keycode[0]
                    else:
                        keycode = key_event.keycode
                    
                    if keycode == 'KEY_ENTER':
                        barcode = self.barcode_buffers[scanner.fd]
                        self.barcode_buffers[scanner.fd] = ''
                        callback(barcode)
                    else:
                        self.barcode_buffers[scanner.fd] += key_event.keycode

    def run(self):
        try:
            while True:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                    ):
                        return
                    elif event.type == self.UPDATE_EVENT:
                        self.target_value = self.get_target_from_cap()
                        self.man_value = self.get_man_count()

                # Handle scanner inputs
                r, _, _ = select.select([self.scanner_ok.fd, self.scanner_ng.fd], [], [], 0)
                for fd in r:
                    if fd == self.scanner_ok.fd:
                        self.handle_scanner_input(self.scanner_ok, self.process_ok_scan)
                    elif fd == self.scanner_ng.fd:
                        self.handle_scanner_input(self.scanner_ng, self.process_ng_scan)

                # Draw dashboard
                self.draw_dashboard()
                pygame.display.flip()

        finally:
            self.cleanup()

    def process_ok_scan(self, barcode):
        self.last_ok_barcode = barcode
        pass

    def process_ng_scan(self, barcode):
        self.last_ng_barcode = barcode
        pass

    def draw_dashboard(self):
        self.screen.fill(self.BLACK)

        # Top Bar
        self.draw_box((30, 20, 1300, 100))
        self.draw_text("Line 3RD", self.font_header, (50, 45))

        # DateTime
        self.draw_box((1350, 20, 538, 100))
        now = datetime.now()
        self.draw_text(f"DATE : {now:%d/%m/%Y}", self.font_small, (1380, 35))
        self.draw_text(f"Time : {now:%H:%M:%S}", self.font_small, (1380, 75))

        # Main boxes
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

        # Message box
        self.draw_box((30, 350, self.width - 60, 80))
        self.draw_text(self.last_ok_barcode, self.font_label, (50, 375))

    def cleanup(self):
        self.scanner_ok.ungrab()
        self.scanner_ng.ungrab()
        self.cursor.close()
        self.db.close()
        pygame.quit()

if __name__ == '__main__':
    dashboard = SewingDashboard()
    dashboard.run()