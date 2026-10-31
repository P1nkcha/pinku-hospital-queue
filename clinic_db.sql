-- =====================================================================
-- clinic_db.sql : สร้างฐานข้อมูลระบบจองคิวคลินิก (CPE361)
-- ใช้คู่กับ create_db.py  (ไฟล์นี้ต้องเซฟเป็น UTF-8)
--
-- วันที่ในข้อมูลตัวอย่างคิดจากวันที่รัน เช่น date('now','localtime','+1 day')
-- ทุกครั้งที่รัน create_db.py จึงมีคิวของ "วันนี้" ให้ Demo เสมอ
--   วันที่ -2 = เมื่อวานซืน, -1 = เมื่อวาน, 0 = วันนี้, +1 = พรุ่งนี้, +2 = มะรืนนี้
--   ประวัติการรักษาย้อนหลังใช้วันที่ -30 ถึง -200 วัน
-- =====================================================================

-- เปิดการตรวจ foreign key (SQLite ปิดไว้เป็นค่าเริ่มต้น ต้องเปิดทุกครั้งที่เชื่อมต่อ)
PRAGMA foreign_keys = ON;

-- ลบตารางเก่าก่อน (ลบตารางลูกก่อนตารางแม่ ไม่งั้นติด foreign key)
DROP TABLE IF EXISTS treatments;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS schedules;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS departments;


-- =====================================================================
-- ส่วนที่ 1 : สร้างตาราง 6 ตาราง
-- =====================================================================

-- 1) แผนก : ชื่อแผนกห้ามซ้ำ
CREATE TABLE departments (
    dept_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_name   TEXT NOT NULL UNIQUE
);

-- 2) แพทย์ : แพทย์ 1 คนสังกัด 1 แผนก (dept_id ห้ามว่าง)
CREATE TABLE doctors (
    doctor_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_name TEXT NOT NULL,
    dept_id     INTEGER NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- 3) ผู้ป่วย
--    phone      : ห้ามซ้ำ ต้องเป็น 0 ตามด้วยตัวเลขอีก 9 หลัก (เก็บเป็น TEXT เพื่อไม่ให้ 0 หาย)
--    birth_date : ต้องเป็นวันที่จริงแบบ YYYY-MM-DD
--                 date(x) คืนค่าเดิมถ้าวันที่ถูกต้อง ถ้าผิดจะได้ค่าอื่นหรือ NULL
--                 ใช้ IS แทน = เพราะถ้าได้ NULL การเทียบด้วย = จะได้ NULL ซึ่ง CHECK ถือว่าผ่าน
--                 (เรื่องห้ามเป็นวันในอนาคต โปรแกรมเป็นคนเช็ก เพราะ CHECK ใช้ date('now') ไม่ได้)
CREATE TABLE patients (
    patient_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    phone        TEXT NOT NULL UNIQUE
                 CHECK (phone GLOB '0[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
    birth_date   TEXT NOT NULL
                 CHECK (date(birth_date) IS birth_date)
);

-- 4) ช่องเวลาออกตรวจ : ช่องละ 30 นาที
--    slot_time ต้องเป็น HH:MM ชั่วโมง 00-23 และนาทีเป็น 00 หรือ 30
--    แพทย์คนเดียวกันห้ามมีวันและเวลาซ้ำ -> UNIQUE (doctor_id, work_date, slot_time)
CREATE TABLE schedules (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id   INTEGER NOT NULL,
    work_date   TEXT NOT NULL
                CHECK (date(work_date) IS work_date),
    slot_time   TEXT NOT NULL
                CHECK (slot_time GLOB '[01][0-9]:[03]0' OR slot_time GLOB '2[0-3]:[03]0'),
    UNIQUE (doctor_id, work_date, slot_time),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

-- 5) การจองคิว
--    symptom   : ไม่บังคับกรอก (ว่างได้ เก็บเป็น NULL)
--    status    : มีได้ 3 ค่า ค่าเริ่มต้นคือ 'จองแล้ว'
--    booked_at : ถ้าไม่ใส่ ระบบใส่วันเวลาปัจจุบันของเครื่องให้เอง
CREATE TABLE appointments (
    appt_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id  INTEGER NOT NULL,
    schedule_id INTEGER NOT NULL,
    symptom     TEXT,
    status      TEXT NOT NULL DEFAULT 'จองแล้ว'
                CHECK (status IN ('จองแล้ว', 'ตรวจแล้ว', 'ยกเลิก')),
    booked_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (patient_id)  REFERENCES patients(patient_id),
    FOREIGN KEY (schedule_id) REFERENCES schedules(schedule_id)
);

-- กฎ "ช่องเวลาหนึ่งมีคิวที่ยังไม่ยกเลิกได้แค่ 1 คิว"
-- UNIQUE แบบมีเงื่อนไข (partial index) : schedule_id ห้ามซ้ำ เฉพาะแถวที่ยังไม่ยกเลิก
-- คิวที่ยกเลิกแล้วไม่นับ ช่องนั้นจึงจองใหม่ได้ และยังเก็บประวัติคิวที่ยกเลิกไว้ได้หลายแถว
CREATE UNIQUE INDEX one_active_appt_per_slot
    ON appointments (schedule_id)
    WHERE status <> 'ยกเลิก';

-- 6) ผลการรักษา (ประวัติการรักษา) : บันทึกตอนกด "บันทึกว่าตรวจแล้ว"
--    appt_id     : UNIQUE ทำให้ 1 คิวมีผลการรักษาได้ไม่เกิน 1 แถว (appointments 1 ต่อ 0..1 treatments)
--                  ไม่เก็บ patient_id ซ้ำ เพราะหาได้จาก appt_id -> appointments.patient_id (ตาม 3NF)
--    diagnosis   : ผลวินิจฉัย บังคับกรอก
--    treatment   : การรักษา ไม่บังคับ (ว่างได้ เก็บเป็น NULL)
--    recorded_at : ถ้าไม่ใส่ ระบบใส่วันเวลาปัจจุบันของเครื่องให้เอง
CREATE TABLE treatments (
    treatment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    appt_id      INTEGER NOT NULL UNIQUE,
    diagnosis    TEXT NOT NULL,
    treatment    TEXT,
    recorded_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (appt_id) REFERENCES appointments(appt_id)
);


-- =====================================================================
-- ส่วนที่ 2 : ข้อมูลตัวอย่าง (แผนก 5, แพทย์ 10, ผู้ป่วย 15, ช่องเวลา 50, คิว 30, ผลการรักษา 15)
--   หลังรันไฟล์นี้ create_db.py จะเติมตารางออกตรวจล่วงหน้า 30 วันให้เอง (แพทย์ทุกคน ทุกวัน วันละ 12 ช่อง)
--   ช่องที่ซ้ำกับช่องตัวอย่างด้านล่างจะถูกข้าม (INSERT OR IGNORE) ช่องตัวอย่างจึงคง schedule_id 1-50 เหมือนเดิม
-- =====================================================================

-- แผนก 5 แผนก -> dept_id 1-5
INSERT INTO departments (dept_name) VALUES
    ('อายุรกรรม'),          -- 1
    ('กุมารเวชกรรม'),       -- 2
    ('ทันตกรรม'),           -- 3
    ('ศัลยกรรม'),           -- 4
    ('สูติ-นรีเวชกรรม');    -- 5

-- แพทย์ 10 คน แผนกละ 2 คน -> doctor_id 1-10
INSERT INTO doctors (doctor_name, dept_id) VALUES
    ('นพ.ประวิทย์ ศรีสุข', 1),        -- 1 อายุรกรรม
    ('พญ.กมลวรรณ ทองดี', 1),         -- 2 อายุรกรรม
    ('พญ.สุภาวดี ใจงาม', 2),          -- 3 กุมารเวชกรรม
    ('นพ.ธนากร วงศ์ใหญ่', 2),         -- 4 กุมารเวชกรรม
    ('ทพ.วีระพงษ์ แก้วมณี', 3),       -- 5 ทันตกรรม
    ('ทพญ.วรรณา แก้วงาม', 3),        -- 6 ทันตกรรม
    ('นพ.อนุชา พรหมมา', 4),          -- 7 ศัลยกรรม
    ('นพ.เกียรติศักดิ์ บุญมา', 4),      -- 8 ศัลยกรรม
    ('พญ.ปิยะนุช สายสุวรรณ', 5),      -- 9 สูติ-นรีเวชกรรม
    ('พญ.รัตนา ศรีวงศ์', 5);          -- 10 สูติ-นรีเวชกรรม

-- ผู้ป่วย 15 คน -> patient_id 1-15 (เด็กใช้เบอร์ของผู้ปกครอง)
INSERT INTO patients (patient_name, phone, birth_date) VALUES
    ('สมหญิง ใจดี',        '0812345678', '1990-05-01'),   -- 1
    ('มานะ รักเรียน',       '0898765432', '1985-11-20'),   -- 2
    ('สมศักดิ์ มีสุข',       '0861112233', '1978-03-15'),   -- 3
    ('วิภาวรรณ ศรีทอง',     '0872223344', '1995-07-09'),   -- 4
    ('ด.ช.ภูมิ สุขสันต์',     '0883334455', '2018-02-14'),   -- 5
    ('นภา พึ่งบุญ',          '0814445566', '1988-12-01'),   -- 6
    ('ชัยวัฒน์ ทองคำ',       '0825556677', '1970-09-30'),   -- 7
    ('ปวีณา ศรีสวัสดิ์',      '0836667788', '2000-01-25'),   -- 8
    ('ธีรเดช อินทร์แก้ว',     '0847778899', '1992-06-18'),   -- 9
    ('กัญญา วงศ์สวัสดิ์',     '0858889900', '1983-04-04'),   -- 10
    ('ด.ญ.ใบเฟิร์น ใจดี',    '0869990011', '2019-10-10'),   -- 11
    ('อำนาจ จันทร์เพ็ญ',     '0910001122', '1965-08-08'),   -- 12
    ('สุดารัตน์ บุญเรือง',     '0921112233', '1998-11-11'),   -- 13
    ('พงศกร แสงทอง',       '0932223344', '1975-02-28'),   -- 14
    ('ลลิตา มณีรัตน์',       '0943334455', '2002-07-07');   -- 15

-- ช่องเวลาออกตรวจ 40 ช่อง -> schedule_id 1-40 (เรียงจากวันเก่าไปวันใหม่)
INSERT INTO schedules (doctor_id, work_date, slot_time) VALUES
    -- เมื่อวานซืน (-2 วัน) : schedule_id 1-4
    (2,  date('now', 'localtime', '-2 day'), '09:00'),   -- 1
    (2,  date('now', 'localtime', '-2 day'), '09:30'),   -- 2
    (7,  date('now', 'localtime', '-2 day'), '10:00'),   -- 3
    (7,  date('now', 'localtime', '-2 day'), '10:30'),   -- 4
    -- เมื่อวาน (-1 วัน) : schedule_id 5-9
    (1,  date('now', 'localtime', '-1 day'), '09:00'),   -- 5
    (1,  date('now', 'localtime', '-1 day'), '09:30'),   -- 6
    (3,  date('now', 'localtime', '-1 day'), '09:00'),   -- 7
    (3,  date('now', 'localtime', '-1 day'), '09:30'),   -- 8
    (5,  date('now', 'localtime', '-1 day'), '13:00'),   -- 9
    -- วันนี้ : schedule_id 10-21
    (1,  date('now', 'localtime'), '09:00'),             -- 10
    (1,  date('now', 'localtime'), '09:30'),             -- 11
    (1,  date('now', 'localtime'), '10:00'),             -- 12
    (1,  date('now', 'localtime'), '10:30'),             -- 13
    (3,  date('now', 'localtime'), '09:00'),             -- 14
    (3,  date('now', 'localtime'), '09:30'),             -- 15
    (3,  date('now', 'localtime'), '10:00'),             -- 16
    (5,  date('now', 'localtime'), '13:00'),             -- 17
    (5,  date('now', 'localtime'), '13:30'),             -- 18
    (5,  date('now', 'localtime'), '14:00'),             -- 19
    (7,  date('now', 'localtime'), '10:00'),             -- 20
    (7,  date('now', 'localtime'), '10:30'),             -- 21
    -- พรุ่งนี้ (+1 วัน) : schedule_id 22-30
    (2,  date('now', 'localtime', '+1 day'), '09:00'),   -- 22
    (2,  date('now', 'localtime', '+1 day'), '09:30'),   -- 23
    (2,  date('now', 'localtime', '+1 day'), '10:00'),   -- 24
    (2,  date('now', 'localtime', '+1 day'), '10:30'),   -- 25
    (4,  date('now', 'localtime', '+1 day'), '13:00'),   -- 26
    (4,  date('now', 'localtime', '+1 day'), '13:30'),   -- 27
    (9,  date('now', 'localtime', '+1 day'), '09:00'),   -- 28
    (9,  date('now', 'localtime', '+1 day'), '09:30'),   -- 29
    (9,  date('now', 'localtime', '+1 day'), '10:00'),   -- 30
    -- มะรืนนี้ (+2 วัน) : schedule_id 31-40
    (1,  date('now', 'localtime', '+2 day'), '09:00'),   -- 31
    (1,  date('now', 'localtime', '+2 day'), '09:30'),   -- 32
    (1,  date('now', 'localtime', '+2 day'), '10:00'),   -- 33
    (6,  date('now', 'localtime', '+2 day'), '13:00'),   -- 34
    (6,  date('now', 'localtime', '+2 day'), '13:30'),   -- 35
    (6,  date('now', 'localtime', '+2 day'), '14:00'),   -- 36
    (8,  date('now', 'localtime', '+2 day'), '09:00'),   -- 37
    (8,  date('now', 'localtime', '+2 day'), '09:30'),   -- 38
    (10, date('now', 'localtime', '+2 day'), '10:00'),   -- 39
    (10, date('now', 'localtime', '+2 day'), '10:30');   -- 40

-- ช่องเวลาย้อนหลัง 10 ช่อง -> schedule_id 41-50 (ใช้กับประวัติการรักษา เรียงจากวันเก่าไปวันใหม่)
--   ต่อท้ายช่องเดิม เลขช่อง 1-40 จึงไม่เปลี่ยน ตัวอย่าง SQL และสคริปต์ Demo อ้างเลขเดิมได้
INSERT INTO schedules (doctor_id, work_date, slot_time) VALUES
    (5,  date('now', 'localtime', '-200 day'), '14:00'),  -- 41 ทพ.วีระพงษ์
    (1,  date('now', 'localtime', '-180 day'), '10:00'),  -- 42 นพ.ประวิทย์
    (2,  date('now', 'localtime', '-150 day'), '09:00'),  -- 43 พญ.กมลวรรณ
    (3,  date('now', 'localtime', '-120 day'), '09:00'),  -- 44 พญ.สุภาวดี
    (8,  date('now', 'localtime', '-90 day'),  '09:00'),  -- 45 นพ.เกียรติศักดิ์
    (6,  date('now', 'localtime', '-75 day'),  '13:30'),  -- 46 ทพญ.วรรณา
    (1,  date('now', 'localtime', '-60 day'),  '09:30'),  -- 47 นพ.ประวิทย์
    (4,  date('now', 'localtime', '-45 day'),  '13:00'),  -- 48 นพ.ธนากร
    (9,  date('now', 'localtime', '-40 day'),  '10:30'),  -- 49 พญ.ปิยะนุช
    (2,  date('now', 'localtime', '-30 day'),  '10:00');  -- 50 พญ.กมลวรรณ

-- การจองคิว 20 คิว -> appt_id 1-20
--   ตรวจแล้ว 5 คิว (วันก่อนหน้า), ยกเลิก 3 คิว, จองแล้ว 12 คิว
--   booked_at ใส่เองให้เป็นวันก่อนวันนัด จะได้ดูสมจริง
INSERT INTO appointments (patient_id, schedule_id, symptom, status, booked_at) VALUES
    -- คิวที่ผ่านมาแล้ว
    (1,  1,  'ไข้ ไอ เจ็บคอ',        'ตรวจแล้ว', datetime('now', 'localtime', '-5 day')),  -- 1  สมหญิง  พญ.กมลวรรณ  -2 09:00
    (3,  3,  'แผลที่ขา',             'ตรวจแล้ว', datetime('now', 'localtime', '-4 day')),  -- 2  สมศักดิ์ นพ.อนุชา     -2 10:00
    (7,  4,  'ปวดเข่า',              'ยกเลิก',   datetime('now', 'localtime', '-4 day')),  -- 3  ชัยวัฒน์ นพ.อนุชา     -2 10:30
    (2,  5,  'ปวดหัว เวียนหัว',       'ตรวจแล้ว', datetime('now', 'localtime', '-3 day')),  -- 4  มานะ    นพ.ประวิทย์  -1 09:00
    (5,  7,  'ไข้สูง',               'ตรวจแล้ว', datetime('now', 'localtime', '-2 day')),  -- 5  ภูมิ     พญ.สุภาวดี   -1 09:00
    (6,  9,  'ปวดฟันกรามล่าง',        'ตรวจแล้ว', datetime('now', 'localtime', '-3 day')),  -- 6  นภา     ทพ.วีระพงษ์  -1 13:00
    -- คิววันนี้ (ช่อง 12 ถูกยกเลิก จึงว่างให้จองใหม่ได้)
    (4,  10, 'เจ็บคอ',               'จองแล้ว',  datetime('now', 'localtime', '-2 day')),  -- 7  วิภาวรรณ นพ.ประวิทย์  0 09:00
    (8,  11, 'ไอเรื้อรัง',            'จองแล้ว',  datetime('now', 'localtime', '-2 day')),  -- 8  ปวีณา   นพ.ประวิทย์  0 09:30
    (9,  12, 'ตรวจติดตามความดัน',     'ยกเลิก',   datetime('now', 'localtime', '-3 day')),  -- 9  ธีรเดช  นพ.ประวิทย์  0 10:00
    (11, 14, 'ผื่นคัน',              'จองแล้ว',  datetime('now', 'localtime', '-1 day')),  -- 10 ใบเฟิร์น พญ.สุภาวดี   0 09:00
    (10, 17, 'ขูดหินปูน',            'จองแล้ว',  datetime('now', 'localtime', '-6 day')),  -- 11 กัญญา   ทพ.วีระพงษ์  0 13:00
    (12, 20, 'มีก้อนที่หลัง',          'จองแล้ว',  datetime('now', 'localtime', '-1 day')),  -- 12 อำนาจ   นพ.อนุชา     0 10:00
    (13, 18, NULL,                  'จองแล้ว',  datetime('now', 'localtime', '-1 day')),  -- 13 สุดารัตน์ ทพ.วีระพงษ์  0 13:30 (ไม่กรอกอาการ)
    -- คิวพรุ่งนี้
    (1,  22, 'ติดตามอาการไข้',        'จองแล้ว',  datetime('now', 'localtime', '-2 day')),  -- 14 สมหญิง  พญ.กมลวรรณ  +1 09:00
    (5,  26, 'ติดตามอาการหลังหายไข้',  'จองแล้ว',  datetime('now', 'localtime', '-1 day')),  -- 15 ภูมิ     นพ.ธนากร    +1 13:00
    (15, 28, 'ฝากครรภ์',             'จองแล้ว',  datetime('now', 'localtime', '-4 day')),  -- 16 ลลิตา   พญ.ปิยะนุช   +1 09:00
    (14, 23, 'ปวดท้อง',              'ยกเลิก',   datetime('now', 'localtime', '-2 day')),  -- 17 พงศกร   พญ.กมลวรรณ  +1 09:30
    -- คิวมะรืนนี้
    (2,  31, 'ตรวจติดตามอาการปวดหัว', 'จองแล้ว',  datetime('now', 'localtime', '-1 day')),  -- 18 มานะ    นพ.ประวิทย์  +2 09:00
    (6,  34, 'อุดฟัน',               'จองแล้ว',  datetime('now', 'localtime', '-3 day')),  -- 19 นภา     ทพญ.วรรณา   +2 13:00
    (3,  37, 'ล้างแผล ตัดไหม',        'จองแล้ว',  datetime('now', 'localtime', '-2 day'));  -- 20 สมศักดิ์ นพ.เกียรติศักดิ์ +2 09:00

-- คิวย้อนหลังที่ตรวจแล้ว 10 คิว -> appt_id 21-30 (ใช้ช่องเวลา 41-50)
--   ทำให้ผู้ป่วยบางคนมีประวัติการรักษาหลายครั้ง และอาการตรงกับแผนกของแพทย์
--   อำนาจ: เบาหวาน (อายุรกรรม) และต้อกระจก (ศัลยกรรม), ภูมิ: หอบหืด (กุมารเวชกรรม), ชัยวัฒน์: ความดันสูง (อายุรกรรม)
INSERT INTO appointments (patient_id, schedule_id, symptom, status, booked_at) VALUES
    (6,  41, 'ขูดหินปูน',              'ตรวจแล้ว', datetime('now', 'localtime', '-207 day')),  -- 21 นภา     ทพ.วีระพงษ์      -200 14:00
    (12, 42, 'ปัสสาวะบ่อย กระหายน้ำ',   'ตรวจแล้ว', datetime('now', 'localtime', '-185 day')),  -- 22 อำนาจ   นพ.ประวิทย์      -180 10:00
    (7,  43, 'ปวดท้ายทอย',            'ตรวจแล้ว', datetime('now', 'localtime', '-153 day')),  -- 23 ชัยวัฒน์ พญ.กมลวรรณ      -150 09:00
    (5,  44, 'ไอ หายใจมีเสียงวี้ด',      'ตรวจแล้ว', datetime('now', 'localtime', '-122 day')),  -- 24 ภูมิ     พญ.สุภาวดี       -120 09:00
    (12, 45, 'ตามัว มองไม่ชัด',         'ตรวจแล้ว', datetime('now', 'localtime', '-97 day')),   -- 25 อำนาจ   นพ.เกียรติศักดิ์  -90  09:00
    (10, 46, 'เสียวฟัน',               'ตรวจแล้ว', datetime('now', 'localtime', '-80 day')),   -- 26 กัญญา   ทพญ.วรรณา       -75  13:30
    (12, 47, 'ตรวจติดตามเบาหวาน',      'ตรวจแล้ว', datetime('now', 'localtime', '-67 day')),   -- 27 อำนาจ   นพ.ประวิทย์      -60  09:30
    (5,  48, 'หอบเหนื่อยตอนกลางคืน',    'ตรวจแล้ว', datetime('now', 'localtime', '-46 day')),   -- 28 ภูมิ     นพ.ธนากร        -45  13:00
    (13, 49, 'ตรวจภายในประจำปี',        'ตรวจแล้ว', datetime('now', 'localtime', '-50 day')),   -- 29 สุดารัตน์ พญ.ปิยะนุช       -40  10:30
    (7,  50, 'ตรวจติดตามความดัน',       'ตรวจแล้ว', datetime('now', 'localtime', '-37 day'));   -- 30 ชัยวัฒน์ พญ.กมลวรรณ      -30  10:00

-- ผลการรักษา 15 แถว = ทุกคิวที่สถานะ "ตรวจแล้ว" (คิว 1, 2, 4, 5, 6 และ 21-30)
--   recorded_at ใส่เองให้เป็นวันนัดของคิวนั้น หลังเวลานัดประมาณ 20-30 นาที
--   คิว 29 ไม่มีการรักษา (treatment เป็น NULL) เพราะตรวจแล้วผลปกติ
INSERT INTO treatments (appt_id, diagnosis, treatment, recorded_at) VALUES
    -- คิวเดิมที่ตรวจแล้ว 5 คิว
    (1,  'คออักเสบจากไวรัส',            'ยาลดไข้ ยาแก้ไอ ดื่มน้ำมากๆ และพักผ่อน',               date('now', 'localtime', '-2 day') || ' 09:20:00'),    -- สมหญิง
    (2,  'แผลฉีกขาดที่ขาซ้าย',           'ล้างแผล เย็บ 4 เข็ม ฉีดยาป้องกันบาดทะยัก นัดตัดไหม',     date('now', 'localtime', '-2 day') || ' 10:25:00'),    -- สมศักดิ์
    (4,  'ไมเกรน',                      'ยาแก้ปวด แนะนำนอนหลับให้เพียงพอ นัดติดตามอาการ',        date('now', 'localtime', '-1 day') || ' 09:20:00'),    -- มานะ
    (5,  'ไข้หวัดใหญ่',                  'ยาลดไข้ เช็ดตัวลดไข้ นัดติดตามอาการ',                   date('now', 'localtime', '-1 day') || ' 09:25:00'),    -- ภูมิ
    (6,  'ฟันกรามล่างซี่ 46 ผุลึก',         'อุดฟันชั่วคราว นัดอุดฟันถาวร',                         date('now', 'localtime', '-1 day') || ' 13:30:00'),    -- นภา
    -- ประวัติย้อนหลัง 10 คิว
    (21, 'หินปูนและเหงือกอักเสบ',          'ขูดหินปูนทั้งปาก แนะนำการแปรงฟันและใช้ไหมขัดฟัน',      date('now', 'localtime', '-200 day') || ' 14:30:00'),  -- นภา
    (22, 'เบาหวานชนิดที่ 2',               'ยา Metformin 500 mg วันละ 2 ครั้ง และควบคุมอาหาร',     date('now', 'localtime', '-180 day') || ' 10:20:00'),  -- อำนาจ
    (23, 'ความดันโลหิตสูง',                'ยา Amlodipine 5 mg วันละ 1 ครั้ง ลดอาหารเค็ม',        date('now', 'localtime', '-150 day') || ' 09:20:00'),  -- ชัยวัฒน์
    (24, 'โรคหอบหืด',                    'ยาพ่นขยายหลอดลมเมื่อมีอาการ สอนวิธีใช้ยาพ่น',          date('now', 'localtime', '-120 day') || ' 09:25:00'),  -- ภูมิ
    (25, 'ต้อกระจกตาขวา',                 'ผ่าตัดสลายต้อกระจกตาขวาและใส่เลนส์แก้วตาเทียม',        date('now', 'localtime', '-90 day') || ' 09:30:00'),   -- อำนาจ
    (26, 'ฟันผุซี่ 36',                     'อุดฟันด้วยวัสดุสีเหมือนฟัน',                            date('now', 'localtime', '-75 day') || ' 14:00:00'),   -- กัญญา
    (27, 'เบาหวานชนิดที่ 2 ควบคุมได้ดี',      'ให้ยาเดิมต่อ นัดเจาะเลือดซ้ำใน 3 เดือน',                date('now', 'localtime', '-60 day') || ' 09:50:00'),   -- อำนาจ
    (28, 'โรคหอบหืดกำเริบ',               'พ่นยาขยายหลอดลมที่คลินิก ให้ยาพ่นสเตียรอยด์ใช้ต่อเนื่อง', date('now', 'localtime', '-45 day') || ' 13:25:00'),   -- ภูมิ
    (29, 'ตรวจภายในประจำปี ผลปกติ',        NULL,                                                 date('now', 'localtime', '-40 day') || ' 10:50:00'),   -- สุดารัตน์
    (30, 'ความดันโลหิตสูง ควบคุมได้',        'ให้ยาเดิมต่อ วัดความดันที่บ้านทุกเช้า',                  date('now', 'localtime', '-30 day') || ' 10:20:00');   -- ชัยวัฒน์
