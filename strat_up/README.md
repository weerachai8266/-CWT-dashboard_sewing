# ✅ วิธีตั้งค่า Static IP แบบถาวร บน Raspberry Pi OS รุ่นใหม่ (Bookworm) ที่ ไม่มี NetworkManager
ใช้ระบบ systemd-networkd ซึ่งแทนที่ dhcpcd และ NetworkManager

### 🧭 1. ตรวจสอบว่าใช้ systemd-networkd
~~~bash
networkctl
~~~
ถ้าคุณเห็น interface เช่น eth0, wlan0 อยู่ในสถานะ configured แสดงว่าใช้ systemd-networkd ✅

### 🛠 2. สร้าง config สำหรับ Static IP
ตัวอย่าง: ตั้ง IP ให้ eth0 = 192.168.0.200
สร้างไฟล์:

~~~bash
sudo nano /etc/systemd/network/10-eth0.network
~~~
วางเนื้อหา:
~~~ini
[Match]
Name=eth0

[Network]
Address=192.168.0.200/24
Gateway=192.168.0.1
DNS=8.8.8.8 1.1.1.1
~~~
### ⚠️ ปรับ IP, gateway, DNS ให้ตรงกับ network ของคุณ

### 🚀 3. เปิดใช้ systemd-networkd (ถ้ายังไม่เปิด)
~~~bash
sudo systemctl enable systemd-networkd --now
~~~
ปิด dhcpcd ถ้าเคยใช้:

~~~bash
sudo systemctl disable dhcpcd --now
~~~
### 🔄 4. รีบูตเพื่อให้ค่ามีผล:
~~~bash
sudo reboot
~~~
### 🧪 5. ตรวจสอบ IP หลังบูต
~~~bash
ip a
~~~
ควรเห็นว่า eth0 มี IP ที่คุณตั้งไว้ เช่น 192.168.0.200

### สร้าง Systemd Service File
~~~bash
sudo nano /etc/systemd/system/monitor.service
~~~

 - เนื้อหาไฟล์ monitor.service

~~~bash
[Unit]
Description=Sewing Machine Monitor
After=network.target home.mount

[Service]
ExecStart=/usr/bin/python3 /home/cwt/sew/V2/main-v2.1.py
WorkingDirectory=/home/cwt/sew/V2
Restart=always
User=cwt
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
~~~

 - รีโหลดและเปิดใช้งาน service
~~~bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable monitor.service
sudo systemctl disable monitor.service ปิด
sudo systemctl start monitor.service
~~~
 - ตรวจสอบว่า service ทำงานหรือไม่
~~~bash
sudo systemctl status monitor.service
~~~

## ปิดโปรแกรมที่เปิดอยู่
 1. หาค่า PID ของโปรแกรม:
~~~bash
ps aux | grep main-v2.1.py
~~~

 2. Kill process ด้วย PID:
 ~~~bash
 kill 1234
 ~~~

### 📝 หมายเหตุ:
  ถ้าคุณต้องการตั้งค่า wlan0 แบบ static → ก็สร้างไฟล์ /etc/systemd/network/20-wlan0.network แยกต่างหาก โดยเปลี่ยน Name=wlan0
  อย่าตั้ง static IP ซ้ำกับ DHCP เดิมใน network มิฉะนั้นจะชน
   หากคุณระบุว่าอยากให้ eth0 หรือ wlan0 ใช้ IP อะไร ผมสามารถเขียนไฟล์ .network ให้แบบพร้อมใช้งานได้เลยครับ

---
# git 

~~~
sudo apt update
sudo apt install git -y
git --version
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
~~~
