# install packages 
### รายชื่อไลบรารีที่ต้องใช้
    pymysql (pip)
    evdev (apt และ pip)
    pygame (apt)
    python3, python3-pip, python3-dev (apt)
    select, datetime, sys, os, threading, queue (built-in Python)

### ติดตั้ง Python และ pip
### วิธีใช้

บันทึกไฟล์นี้เป็น ~ check_and_install_libs.sh ~
ให้สิทธิ์รัน:
~~~chmod +x check_and_install_libs.sh~
รัน:
~./check_and_install_libs.sh~

### ติดตั้ง required packages
~~~ echo "🔧 กำลังติดตั้ง packages ที่จำเป็น..."
sudo apt-get install -y \
    python3-evdev \
    python3-dev \
    default-libmysqlclient-dev
~~~

### ติดตั้ง Python packages
~~~ echo "📚 กำลังติดตั้ง Python libraries..."
pip3 install evdev pymysql
~~~

### เพิ่มผู้ใช้เข้ากลุ่ม input
~~~ echo "👥 กำลังเพิ่มสิทธิ์ผู้ใช้..."
sudo usermod -a -G input weerachai8266
~~~

### สร้างโฟลเดอร์สำหรับโปรแกรมและ logs
~~~ echo "📁 กำลังสร้างโครงสร้างโฟลเดอร์..."
mkdir -p ~/sewing/logs
~~~

# 🔧 วิธีตั้งค่าแบบ Fix ตามพอร์ต USB เท่านั้น
เปิดไฟล์ rule:

~~~bash
sudo nano /etc/udev/rules.d/99-barcode.rules
~~~

วางโค้ด
~~~udev
# สแกนเนอร์ OK → เสียบพอร์ต 1-1.2
KERNEL=="event*", SUBSYSTEM=="input", KERNELS=="1-1.2", SYMLINK+="input/scan_ok"
# สแกนเนอร์ NG → เสียบพอร์ต 1-1.3
KERNEL=="event*", SUBSYSTEM=="input", KERNELS=="1-1.3", SYMLINK+="input/scan_ng"
~~~

บันทึกและออก (Ctrl+O, Enter, แล้ว Ctrl+X)

โหลด rule ใหม่:
~~~bash
sudo udevadm control --reload-rules
sudo udevadm trigger
~~~

ตรวจสอบว่า symlink ถูกสร้าง:
~~~bash
ls -l /dev/input/scan_*
~~~


# ✅ ขั้นตอนการตั้งค่า systemd ให้รัน sewing.py อัตโนมัติ
### 1. สร้างไฟล์ systemd service
~~~bash
sudo nano /etc/systemd/system/sewing.service
~~~
🔧 ใส่เนื้อหาดังนี้:
~~~ini
[Unit]
Description=Sewing Barcode Scanner
After=network.target

[Service]
Type=simple
User=3rd
WorkingDirectory=/home/3rd/sewing
ExecStart=/home/3rd/sewing/venv/bin/python /home/3rd/sewing/sewing.py
Restart=always

[Install]
WantedBy=multi-user.target
~~~
- เปลี่ยนชื่อ User= ให้ตรงกับชื่อผู้ใช้ (ของคุณคือ 3rd)
- เปลี่ยน path ให้ตรงกับตำแหน่งไฟล์ของคุณ

### 2. โหลด service และเปิดใช้งาน
~~~bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable sewing.service
sudo systemctl start sewing.service
~~~
### 3. ตรวจสอบสถานะการทำงาน
~~~bash
sudo systemctl status sewing.service
~~~
คุณควรเห็นสถานะเป็น active (running)
หากสแกนบาร์โค้ด → จะทำงานและบันทึกทันทีแม้ไม่เปิด terminal


