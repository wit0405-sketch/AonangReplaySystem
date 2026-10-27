AONANG LANDMARK REPLAY SYSTEM — ต้นแบบสำหรับ Windows 10
===========================================================

สถานะ: ชุดโปรแกรมต้นแบบ (Source + ตัวติดตั้งสำหรับสร้างภายหลัง) ไม่ใช่ Setup.exe ที่คอมไพล์แล้ว

ฟังก์ชันในต้นแบบ:
- รับภาพจาก Capture Card ผ่าน OpenCV (เลือกกล้องจากรายการ)
- แสดงภาพสด
- เก็บภาพย้อนหลังในหน่วยความจำ 30 วินาที
- กด SAVE REPLAY เพื่อบันทึกคลิปย้อนหลัง 30 วินาทีเป็น MP4
- เปิดคลิป Replay ในหน้าต่างเล่นวิดีโอ
- มีปุ่มส่งออกไฟล์คลิปไปใช้เป็น Media Source ใน OBS

ข้อจำกัดสำคัญ:
- UGREEN 35287 จำนวน 1 ตัว รับภาพ HDMI ได้ครั้งละ 1 แหล่ง ไม่ใช่กล้อง 4 ตัวแยกกัน
- การสร้างไฟล์ MP4 ใช้ FFmpeg ที่ติดตั้งในเครื่อง (แนะนำ) หรือ OpenCV VideoWriter
- ต้นแบบนี้ยังไม่ได้สั่ง OBS WebSocket โดยตรง และยังไม่ใช่ระบบ replay broadcast แบบมืออาชีพ
- ภาพย้อนหลังจะเก็บใน RAM; แนะนำให้ทดสอบที่ 1280x720 ก่อน หากเครื่องมี RAM/CPU จำกัด

วิธีเริ่มต้น:
1. ติดตั้ง Python 3.11 64-bit จาก python.org และติ๊ก Add Python to PATH
2. ดับเบิลคลิก INSTALL_DEPENDENCIES.bat
3. ดับเบิลคลิก RUN_AONANG_REPLAY.bat
4. เลือกอุปกรณ์กล้องในรายการ แล้วกด Connect Camera
5. กด SAVE REPLAY เพื่อบันทึกย้อนหลัง 30 วินาที
6. ใน OBS: Sources > + > Media Source > เลือกไฟล์ MP4 ที่บันทึกไว้

วิธีสร้าง EXE:
- ติดตั้ง dependencies ด้วย INSTALL_DEPENDENCIES.bat
- ดับเบิลคลิก BUILD_EXE.bat
- ไฟล์ EXE จะอยู่ใน dist\AonangReplaySystem\AonangReplaySystem.exe
- การสร้าง EXE ต้องทำบน Windows และอาจต้องติดตั้ง runtime เพิ่มตามเครื่อง

หมายเหตุ OBS:
หากต้องการให้โปรแกรมควบคุมแหล่งภาพ/สลับ LIVE กับ REPLAY ใน OBS โดยตรง ต้องเพิ่มการเชื่อมต่อ OBS WebSocket และกำหนดชื่อ Scene/Source ใน OBS ในรุ่นถัดไป


วิธีสร้าง Setup.exe (ตัวติดตั้ง):
1. ทำบน Windows 10/11 เท่านั้น
2. ติดตั้ง Python 3.11 64-bit
3. ติดตั้ง Inno Setup 6 จากเว็บไซต์ทางการ: https://jrsoftware.org/isinfo.php
4. ดับเบิลคลิก BUILD_SETUP_EXE.bat
5. หากสำเร็จ จะได้ installer_output\Setup_AonangReplaySystem.exe

ข้อจำกัด:
- เครื่องมือสร้าง Windows EXE/Setup.exe ไม่สามารถคอมไพล์ได้จากสภาพแวดล้อม Linux ที่ใช้สร้าง ZIP นี้
- BUILD_SETUP_EXE.bat จะสร้างโปรแกรม EXE ก่อน แล้วจึงใช้ Inno Setup สร้าง Setup.exe บนเครื่อง Windows
- โปรแกรมรุ่นนี้ยังเป็นต้นแบบ และยังไม่มีการควบคุม OBS WebSocket โดยตรง
