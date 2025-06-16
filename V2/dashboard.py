import pygame
import logging
from utils.logger import setup_logger
from datetime import datetime, time
import os

logger = setup_logger('dashboard')

class Dashboard:
    # Display constants
    DISPLAY_WIDTH = 1920
    DISPLAY_HEIGHT = 1080
    STATION_NAME = "3RD-A"
    
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    
    # Break periods
    BREAK_PERIODS = [
        {
            'start': time(10, 0),  # 10:00
            'end': time(10, 15),   # 10:15
            'name': 'Morning Break'
        },
        {
            'start': time(12, 0),  # 12:00
            'end': time(13, 0),    # 13:00
            'name': 'Lunch Break'
        },
        {
            'start': time(15, 0),  # 15:00
            'end': time(15, 15),   # 15:15
            'name': 'Afternoon Break'
        }
    ]

    def __init__(self, db_manager, scanner1, scanner2, current_user, current_datetime):
        self._init_pygame()
        self._load_fonts()
        self._init_variables(db_manager, scanner1, scanner2)
        self.current_user = current_user
        self.current_datetime = current_datetime

    def _init_pygame(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), 
            pygame.FULLSCREEN
        )
        pygame.display.set_caption("CWT Dashboard")

    def _load_fonts(self):
        try:
            # ใช้วิธีโหลดฟอนต์แบบเดิมจาก v2
            self.font_TH = pygame.font.Font("./fonts/THSarabunNew Bold.ttf", 50)
            self.font_mini = pygame.font.Font("./fonts/THSarabunNew Bold.ttf", 40)
            self.font_percent = pygame.font.Font("./fonts/THSarabunNew Bold.ttf", 60)
        except Exception as e:
            logger.error(f"Font loading error: {e}")
            raise

    def _init_variables(self, db_manager, scanner1, scanner2):
        self.db_manager = db_manager
        self.scanner1 = scanner1
        self.scanner2 = scanner2
        
        # Production variables
        self.last_pd_barcode = ""
        self.show_error = False
        self.error_message = ""
        
        # QC variables
        self.last_qc_barcode = ""
        self.qc_show_error = False
        self.qc_error_message = ""

    def is_break_time(self):
        """ตรวจสอบว่าเป็นเวลาพักหรือไม่"""
        current_time = self.current_datetime.time()
        for period in self.BREAK_PERIODS:
            if period['start'] <= current_time <= period['end']:
                return True, period['name']
        return False, None

    def draw_text(self, text, font, position, color=WHITE):
        """วาดข้อความบนหน้าจอ"""
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def draw_box(self, rect):
        """วาดกรอบสี่เหลี่ยม"""
        pygame.draw.rect(self.screen, self.WHITE, rect, 2)

    def draw_header(self):
        """วาดส่วน header พร้อมแสดงสถานะเวลาพัก"""
        current_time = self.current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        is_break, break_name = self.is_break_time()
        
        # Draw basic info
        self.draw_text(f"Station: {self.STATION_NAME}", self.font_mini, (50, 10))
        self.draw_text(f"User: {self.current_user}", self.font_mini, (50, 50))
        self.draw_text(f"Time (UTC): {current_time}", self.font_mini, (50, 90))

        # Draw break status
        if is_break:
            self.draw_text(f"Break Time: {break_name}", self.font_mini, (50, 130), self.RED)

    def draw_break_schedule(self, x, y):
        """วาดตารางเวลาพัก"""
        self.draw_text("Break Schedule:", self.font_mini, (x, y))
        y_offset = 40
        for period in self.BREAK_PERIODS:
            break_text = f"{period['name']}: {period['start'].strftime('%H:%M')} - {period['end'].strftime('%H:%M')}"
            self.draw_text(break_text, self.font_mini, (x, y + y_offset))
            y_offset += 40

    def process_pd_scan(self, barcode):
        if 12 < len(barcode) <= 17:
            self.last_pd_barcode = barcode
            self.db_manager.insert_ok(barcode)
            self.show_error = False
            self.error_message = ""
        else:
            self.error_message = f"ไม่บันทึก กรุณาสแกนใหม่ ({barcode})"
            self.show_error = True

    def process_qc_scan(self, barcode):
        if barcode.startswith("NI") and len(barcode) > 2:
            self.last_qc_barcode = barcode
            self.db_manager.insert_qc(barcode)
            self.qc_show_error = False
            self.qc_error_message = ""
        else:
            self.qc_error_message = f"ไม่บันทึก กรุณาสแกนใหม่ ({barcode})"
            self.qc_show_error = True

    def update_display(self):
        """อัพเดทหน้าจอ"""
        self.screen.fill(self.BLACK)
        
        # Draw header with break status
        self.draw_header()
        
        # Draw break schedule
        self.draw_break_schedule(1500, 10)
        
        # Draw scanner data boxes
        # Production box
        self.draw_box((30, 140, 915, 100))
        self.draw_text("Production", self.font_mini, (50, 150))
        if self.show_error:
            self.draw_text("Error: " + self.error_message, self.font_TH, (50, 155), self.RED)
        else:
            self.draw_text("Model: " + self.last_pd_barcode, self.font_percent, (50, 165))

        # QC box
        self.draw_box((975, 140, 915, 100))
        self.draw_text("QC", self.font_mini, (995, 150))

        if self.qc_show_error:
            self.draw_text("Error: " + self.qc_error_message, self.font_TH, (995, 155), self.RED)
        else:
            self.draw_text("Part: " + self.last_qc_barcode, self.font_percent, (995, 165))

        pygame.display.flip()

    def run(self):
        """Main loop with break time handling"""
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return

            # Check for break time
            is_break, break_name = self.is_break_time()
            
            # Only process barcodes if not in break time
            if not is_break:
                barcode1 = self.scanner1.get_barcode() if self.scanner1 else None
                barcode2 = self.scanner2.get_barcode() if self.scanner2 else None

                if barcode1:
                    self.process_pd_scan(barcode1)
                if barcode2:
                    self.process_qc_scan(barcode2)
            
            # Update display
            self.update_display()
            clock.tick(60)