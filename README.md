## ✅ ขั้นตอนการตั้งค่า systemd ให้รัน sewing.py อัตโนมัติ
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