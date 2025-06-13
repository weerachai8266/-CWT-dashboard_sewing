#!/bin/bash

# อัปเดตฐานข้อมูลแพ็คเกจ
sudo apt update

# รายชื่อไลบรารีที่ติดตั้งผ่าน apt
APT_PACKAGES=(
    python3
    python3-pip
    python3-dev
    python3-pygame
    python3-evdev
)

echo "ตรวจสอบและติดตั้งไลบรารีระบบ (apt)..."
for pkg in "${APT_PACKAGES[@]}"; do
    if dpkg -s "$pkg" >/dev/null 2>&1; then
        echo "พบ $pkg แล้ว"
    else
        echo "กำลังติดตั้ง $pkg ..."
        sudo apt install -y "$pkg"
    fi
done

echo ""
echo "ติดตั้งไลบรารี Python ที่จำเป็น (pip3)..."
pip3 install --upgrade pip
pip3 install pymysql evdev

echo ""
echo "ตรวจสอบและติดตั้งไลบรารีเสร็จสิ้น!"