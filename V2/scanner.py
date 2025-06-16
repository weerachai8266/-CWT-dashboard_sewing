from evdev import InputDevice, list_devices, ecodes
import os
import threading
import select
import queue
import logging
from utils.logger import setup_logger

logger = setup_logger('scanner')

class Scanner:
    def __init__(self, device_path=None, device_index=None):
        logger.info(f"Initializing Scanner with path: {device_path}, index: {device_index}")
        if device_path:
            try:
                self.device = InputDevice(device_path)
                logger.info(f"Using fixed device path: {device_path}")
            except Exception as e:
                logger.error(f"Error opening device {device_path}: {e}")
                raise
        else:
            self.device = self.find_scanner(device_index)
        
        if not self.device:
            logger.error("No scanner device found")
            raise RuntimeError("Scanner device not found")

        self._setup_device()
        self._initialize_buffer()
        self._start_reading_thread()

    def _setup_device(self):
        try:
            self.device.grab()
            import fcntl
            flag = fcntl.fcntl(self.device.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.device.fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
            logger.info(f"Device setup complete: {self.device.path} ({self.device.name})")
        except Exception as e:
            logger.error(f"Device setup failed: {e}")
            raise

    def _initialize_buffer(self):
        self.buffer = ''
        self.barcode_queue = queue.Queue()
        self._stop_event = threading.Event()

    def _start_reading_thread(self):
        self.thread = threading.Thread(target=self._barcode_loop, daemon=True)
        self.thread.start()

    def find_scanner(self, device_index=None):
        devices = [InputDevice(path) for path in list_devices()]
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
            logger.error("No scanner or usable device found")
            return None
        if device_index is not None:
            if 0 <= device_index < len(available_devices):
                return available_devices[device_index]
            else:
                logger.error(f"Invalid device index: {device_index}")
                return None
        return available_devices[0]

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
            return None
        except Exception:
            return None

    def cleanup(self):
        logger.info("Cleaning up scanner resources")
        self._stop_event.set()
        if hasattr(self, 'device') and self.device:
            try:
                self.device.ungrab()
                logger.info("Device ungrabbed successfully")
            except Exception as e:
                logger.error(f"Error during device cleanup: {e}")