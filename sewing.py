from evdev import InputDevice, categorize, ecodes
import pymysql
import select
from datetime import datetime

# Connect to database
db = pymysql.connect(
    host="192.168.0.14",
    user="sew_py",
    password="cwt258963",
    database="sewing"
)
cursor = db.cursor()

# Open barcode scanners
scanner_ok = InputDevice('/dev/input/scan_ok')
scanner_ng = InputDevice('/dev/input/scan_ng')

scanner_ok.grab()
scanner_ng.grab()

# เก็บสถานะของการสแกนแยกกัน
barcode_buffers = {
    scanner_ok.fd: '',
    scanner_ng.fd: ''
}
shift_states = {
    scanner_ok.fd: False,
    scanner_ng.fd: False
}

def insert_ok(item_code):
    item_code = item_code.upper()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql = "INSERT INTO 3rd (item, qty, status, created_at) VALUES (%s, 1, 10, %s)"
    try:
        cursor.execute(sql, (item_code, now))
        db.commit()
        print(f"[OK] ✅ รับงานเข้าระบบ: {item_code}")
    except pymysql.err.IntegrityError as e:
        print(f"[ERROR] ไม่สามารถเพิ่ม: {item_code} (อาจซ้ำ)")

def update_ng(item_code):
    item_code = item_code.upper()
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # หารายการ status = 10 ของวันนี้
    sql_select = """
        SELECT id FROM 3rd
        WHERE item = %s AND status = 10 AND DATE(created_at) = %s
        ORDER BY created_at DESC
        LIMIT 1
    """
    cursor.execute(sql_select, (item_code, today))
    result = cursor.fetchone()

    if result:
        # อัปเดต status = 20
        sql_update = "UPDATE 3rd SET status = 20, updated_at = %s WHERE id = %s"
        cursor.execute(sql_update, (now, result[0]))
        db.commit()
        print(f"[NG] ❗ตรวจชิ้นงานเสีย: {item_code}")

    else:
        # ไม่มีรายการที่ status = 10 → ให้เพิ่มใหม่ด้วย status = 20
        sql_insert = "INSERT INTO 3rd (item, qty, status, created_at) VALUES (%s, 1, 20, %s)"
        cursor.execute(sql_insert, (item_code, now))
        db.commit()
        print(f"[NG] ➕ เพิ่มใหม่ (ไม่มีรายการที่อัปเดตได้): {item_code}")

        
print("🔍 กำลังรอฟังการสแกนจากทั้ง OK และ NG...")

devices = {
    scanner_ok.fd: (scanner_ok, insert_ok),
    scanner_ng.fd: (scanner_ng, update_ng)
}

try:
    while True:
        r, _, _ = select.select(devices.keys(), [], [])
        for fd in r:
            device, callback = devices[fd]
            for event in device.read():
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)

                    if key_event.keystate == 1:  # Key down
                        keycode = key_event.keycode
                        if isinstance(keycode, list):
                            keycode = keycode[0]

                        if keycode in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                            shift_states[fd] = True
                            continue

                        if keycode == 'KEY_ENTER':
                            barcode = barcode_buffers[fd].upper()
                            callback(barcode)
                            barcode_buffers[fd] = ''
                            continue

                        key = keycode.replace('KEY_', '')
                        char = ''

                        if key.isdigit():
                            char = key
                        elif key == 'MINUS':
                            char = '_' if shift_states[fd] else '-'
                        elif len(key) == 1 and key.isalpha():
                            char = key.upper() if shift_states[fd] else key.lower()

                        if char:
                            barcode_buffers[fd] += char

                        shift_states[fd] = False

except KeyboardInterrupt:
    print("\n⛔ หยุดแล้ว")

finally:
    scanner_ok.ungrab()
    scanner_ng.ungrab()
    db.close()