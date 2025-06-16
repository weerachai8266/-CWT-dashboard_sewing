from scanner import Scanner
from database import DatabaseManager
from dashboard import Dashboard
from utils.logger import setup_logger
import sys
import traceback
import pygame
from datetime import datetime

# Global configuration
CURRENT_USER = 'weerachai8266'
CURRENT_DATETIME = datetime(2025, 6, 16, 5, 29, 37)  # UTC time: 2025-06-16 05:29:37

logger = setup_logger('main')

def main():
    try:
        logger.info(f"Starting CWT Dashboard application - Version 2.1")
        logger.info(f"User: {CURRENT_USER}")
        logger.info(f"System time (UTC): {CURRENT_DATETIME}")
        
        # Initialize components with user info
        db_manager = DatabaseManager(current_user=CURRENT_USER)
        scanner1 = Scanner(device_path='/dev/input/scanner1')
        scanner2 = Scanner(device_path='/dev/input/scanner2')
        
        # Start dashboard with user and time info
        dashboard = Dashboard(
            db_manager=db_manager,
            scanner1=scanner1,
            scanner2=scanner2,
            current_user=CURRENT_USER,
            current_datetime=CURRENT_DATETIME
        )
        dashboard.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if 'scanner1' in locals():
            scanner1.cleanup()
        if 'scanner2' in locals():
            scanner2.cleanup()
        pygame.quit()

if __name__ == "__main__":
    main()