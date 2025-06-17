import os
import threading
import queue
import select
from evdev import InputDevice, ecodes, list_devices

class Scanner:
    def __init__(self, device_path=None, device_index=None):
        print("\nกำลังค้นหาอุปกรณ์...")
        if device_path:
            print(f"[Scanner] Using fixed device path: {device_path}")
            self.device = InputDevice(device_path)
        else:
            self.device = self.find_scanner(device_index)
        if not self.device:
            print("\n❌ ไม่พบอุปกรณ์ที่ใช้งานได้")
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
            print("❌ ไม่พบ Scanner หรือ อุปกรณ์ที่ใช้งานได้")
            return None

        if device_index is not None:
            if 0 <= device_index < len(available_devices):
                selected_device = available_devices[device_index]
                print(f"✅ เลือกใช้: {selected_device.path} ({selected_device.name})")
                return selected_device
            else:
                print(f"❌ ไม่พบอุปกรณ์ index={device_index}")
                return None

        # ถ้าไม่ได้ระบุ index เลือกอันแรก
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
            print(f"Unknown key: {key}")
            return None
        except Exception as e:
            print(f"❌ แปลงคีย์ผิดพลาด: {e}")
            return None

    def cleanup(self):
        self._stop_event.set()
        if hasattr(self, 'device') and self.device:
            self.device.ungrab()