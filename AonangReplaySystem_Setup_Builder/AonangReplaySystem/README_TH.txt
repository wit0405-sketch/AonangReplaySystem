AONANG LANDMARK REPLAY SYSTEM v0.2.0 — Windows 10/11
=====================================================

สถานะ
- Source code พร้อมสคริปต์สร้าง EXE และ Setup.exe
- ยังต้อง build บน Windows ผ่าน GitHub Actions หรือเครื่อง Windows
- ไฟล์ติดตั้งที่ build แล้วจะถูกเก็บเป็น GitHub Actions artifact ไม่ได้ commit เข้า repository โดยตรง

ฟังก์ชัน
- รับภาพจาก Capture Card ผ่าน OpenCV และแสดงภาพสด
- เก็บ rolling buffer ย้อนหลังตามเวลาที่เลือก 5–30 วินาที
- SAVE REPLAY เพื่อสร้างคลิป MP4; ใช้ FFmpeg จาก imageio-ffmpeg หรือ FFmpeg ใน PATH ก่อน และ fallback ไป OpenCV
- เปิดไฟล์ MP4/MOV/AVI/MKV ที่มีอยู่
- เชื่อมต่อ OBS Studio ผ่าน OBS WebSocket
- PLAY REPLAY: ตั้งค่า Media Source "Aonang Replay" ในฉาก REPLAY และสั่งเริ่มเล่น
- STOP REPLAY: หยุด Media Source
- BACK TO LIVE: สลับ Program Scene กลับไป LIVE
- แสดงสถานะการเชื่อมต่อ OBS

การตั้งค่า OBS
1. เปิด OBS Studio 28 หรือใหม่กว่า
2. ไปที่ Tools > WebSocket Server Settings
3. เปิด WebSocket Server และใช้พอร์ต 4455 (หรือกรอกพอร์ตจริงในโปรแกรม)
4. ตั้งรหัสผ่านตามต้องการ แล้วกรอกให้ตรงกันในโปรแกรม
5. สร้าง Scene ชื่อ LIVE และ REPLAY ให้ตรงตัวพิมพ์
6. กด Connect OBS ในโปรแกรม
7. เลือก/บันทึกคลิป แล้วกด PLAY REPLAY
หมายเหตุ: OBS ต้องเปิดอยู่ตลอดเวลาที่ควบคุม และไฟล์วิดีโอต้องเข้าถึงได้จากเครื่องที่รัน OBS

การใช้ Capture Card
- เสียบ capture card และเลือก Camera device ที่ถูกต้อง
- หากอุปกรณ์ไม่เปิด ให้ลองหมายเลขอุปกรณ์อื่น และปิดโปรแกรมอื่นที่กำลังใช้ capture card
- อุปกรณ์ UGREEN 35287 หนึ่งตัวรับ HDMI ได้ครั้งละหนึ่งแหล่ง ไม่ได้แยกกล้องหลายตัว

Build บน Windows ด้วยตนเอง
1. ติดตั้ง Python 3.11 64-bit
2. ติดตั้ง Inno Setup 6 จาก https://jrsoftware.org/isinfo.php
3. เปิด BUILD_SETUP_EXE.bat
4. ผลลัพธ์: installer_output\Setup_AonangReplaySystem.exe

Build ผ่าน GitHub Actions
1. เปิดแท็บ Actions ใน repository
2. เลือก workflow "Build Windows Setup"
3. กด Run workflow หรือ push commit ไปยัง main
4. เมื่อ workflow สำเร็จ เปิด workflow run แล้วดาวน์โหลด artifact ชื่อ AonangReplaySystem-Setup-Windows
5. แตก ZIP จะพบ Setup_AonangReplaySystem.exe

ข้อจำกัดและการทดสอบ
- ต้องทดสอบกับ Windows จริง, capture card จริง และ OBS ที่ตั้งค่า WebSocket แล้ว
- การ build สำเร็จไม่ได้ยืนยันว่ากล้องทุกอุปกรณ์หรือ OBS ทุก configuration จะทำงานเหมือนกัน
- โปรแกรมนี้ยังไม่ใช่ระบบ replay แบบหลายกล้อง/instant replay hardware broadcast
