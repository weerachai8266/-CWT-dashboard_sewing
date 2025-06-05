import pymysql
import pygame
import sys
from datetime import datetime

# Database connection setup
try:
    db = pymysql.connect(
        host="192.168.0.14",
        user="sew_py",
        password="cwt258963",
        database="automotive"
    )
    cursor = db.cursor()
except Exception as e:
    print(f"Database connection failed: {e}")
    sys.exit(1)

pygame.init()
UPDATE_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(UPDATE_EVENT, 1000)  # Update every second

# Setup fullscreen display
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Production Dashboard")
width, height = screen.get_size()

# Fonts
font_header = pygame.font.SysFont('Arial', 50, bold=True)
font_label = pygame.font.SysFont('Arial', 40, bold=True)
font_percent = pygame.font.SysFont('Arial', 80, bold=True)
font_small = pygame.font.SysFont('Arial', 30, bold=True)
# font_mid = pygame.font.SysFont('Arial', 30)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 175, 0)

def get_target_from_cap():
    try:
        sql = "SELECT `3rd` FROM sewing_cap ORDER BY created_at DESC LIMIT 1"
        cursor.execute(sql)
        result = cursor.fetchone()
        return str(result[0]) if result else "00"
    except Exception as e:
        print(f"Error fetching sewing_cap target: {e}")
        return "00"

def get_man_count():
    try:
        sql = "SELECT `3rd` FROM sewing_man ORDER BY created_at DESC LIMIT 1"
        cursor.execute(sql)
        result = cursor.fetchone()
        return str(result[0]) if result else "00"
    except Exception as e:
        print(f"Error fetching sewing_man count: {e}")
        return "00"

def draw_box(rect, fill_color=BLACK, border_color=WHITE, border=3, radius=20):
    pygame.draw.rect(screen, fill_color, rect, border_radius=radius)
    pygame.draw.rect(screen, border_color, rect, border, border_radius=radius)

def draw_text(text, font, pos, color=WHITE, center=False):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    screen.blit(surface, rect)

# Initialize values
target_value = get_target_from_cap()
man_value = get_man_count()

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                pygame.quit()
                cursor.close()
                db.close()
                sys.exit()

        target_value = get_target_from_cap()
        man_value = get_man_count()   

        screen.fill(BLACK)

        # Top Bar
        draw_box((30, 20, 1300, 100))
        draw_text("Line 3RD", font_header, (50, 45))

        draw_box((1350, 20, 538, 100))
        draw_text("DATE :", font_small, (1380, 35))
        draw_text(datetime.now().strftime("%d/%m/%Y"), font_small, (1500, 35), WHITE, center=False)
        draw_text("Time  :", font_small, (1380, 75))
        draw_text(datetime.now().strftime("%H:%M:%S"), font_small, (1500, 75), WHITE, center=False)

        # Efficiency
        draw_box((30, 140, 420, 180))
        draw_text("Efficiency", font_label, (50, 160))
        draw_text("00.00 %", font_percent, (240, 270), GREEN, center=True)

        # Output
        draw_box((470, 140, 420, 180))
        draw_text("Output", font_label, (490, 160))
        draw_text("00", font_percent, (680, 270), GREEN, center=True)

        # Target
        draw_box((910, 140, 420, 180))
        draw_text("Target / hr", font_label, (930, 160))
        draw_text(target_value, font_percent, (1120, 270), GREEN, center=True)

        # Man
        draw_box((1350, 140, 420, 180))
        draw_text("Man", font_label, (1370, 160))
        draw_text(man_value, font_percent, (1580, 270), GREEN, center=True)

        # OK Part Message Box
        draw_box((30, 350, width - 60, 80))
        draw_text("Part", font_label, (50, 375))

        pygame.display.flip()
finally:
    cursor.close()
    db.close()