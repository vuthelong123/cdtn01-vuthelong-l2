USE warranty_db;

-- Nhân viên: 1 tiếp nhận, 1 quản trị, 2 kỹ thuật viên (mật khẩu mẫu: 123456)
INSERT INTO employee (employee_id, full_name, role, phone, is_active, username, password_hash) VALUES
(1, 'Nguyen Thi Lan',  'TIEP_NHAN', '0901000001', TRUE, 'nhanvientiepnhan', 'scrypt:32768:8:1$uXQJcwyPoumxXWOW$a621d8d2f113b84996d6e2c69892bb58d07ba43901a63889f7b5eea6a23a4bfcb3b7ed1bbb58eb10dbd81f67a8904294d764d84571fa5d3a551eaf9f1e6253c1'),
(2, 'Tran Van Minh',   'QUAN_TRI',  '0901000002', TRUE, 'quantrivien',      'scrypt:32768:8:1$uXQJcwyPoumxXWOW$a621d8d2f113b84996d6e2c69892bb58d07ba43901a63889f7b5eea6a23a4bfcb3b7ed1bbb58eb10dbd81f67a8904294d764d84571fa5d3a551eaf9f1e6253c1'),
(3, 'Le Hoang Nam',    'KY_THUAT',  '0901000003', TRUE, 'kythuatvien',      'scrypt:32768:8:1$uXQJcwyPoumxXWOW$a621d8d2f113b84996d6e2c69892bb58d07ba43901a63889f7b5eea6a23a4bfcb3b7ed1bbb58eb10dbd81f67a8904294d764d84571fa5d3a551eaf9f1e6253c1'),
(4, 'Pham Quoc Bao',   'KY_THUAT',  '0901000004', TRUE, 'kythuatvien2',     'scrypt:32768:8:1$uXQJcwyPoumxXWOW$a621d8d2f113b84996d6e2c69892bb58d07ba43901a63889f7b5eea6a23a4bfcb3b7ed1bbb58eb10dbd81f67a8904294d764d84571fa5d3a551eaf9f1e6253c1');

INSERT INTO technician (technician_id, employee_id, center_id, is_active) VALUES
(1, 3, 1, TRUE),
(2, 4, 1, TRUE);

INSERT INTO customer (customer_id, full_name, phone, email, segment) VALUES
(1, 'Vu The Long',    '0843310647', 'long@example.com',  'VIP'),
(2, 'Nguyen Van An',  '0912345678', 'an@example.com',    'THUONG'),
(3, 'Tran Thi Hoa',   '0987654321', NULL,                'THUONG');

INSERT INTO device (device_id, customer_id, serial_no, model_name, purchase_date, warranty_months) VALUES
(1, 1, 'IMEI350000000000001', 'Mekong Phone X1', '2026-03-15', 12),
(2, 2, 'IMEI350000000000002', 'Mekong Phone X2', '2025-01-10', 12),
(3, 3, 'IMEI350000000000003', 'Mekong Tab T1',  '2026-08-01', 24);

INSERT INTO ticket
(ticket_id, ticket_code, customer_id, device_id, technician_id, received_by_employee_id,
 issue_category, priority, ticket_status, issue_desc, received_at, due_date, closed_at) VALUES
(1, 'BH-0001', 1, 1, 1,    1, 'MAN_HINH', 'CAO',        'DANG_XU_LY', 'Man hinh bi soc doc, khong cam ung duoc',     '2026-10-24 09:00:00', '2026-10-25 09:00:00', NULL),
(2, 'BH-0002', 2, 2, NULL, 1, 'PIN',      'TRUNG_BINH', 'MOI',        'Pin tut nhanh, may nong khi sac',            '2026-10-25 10:30:00', '2026-10-28 10:30:00', NULL),
(3, 'BH-0003', 3, 3, 2,    1, 'PHAN_MEM', 'THAP',       'DA_DONG',    'May bi treo logo sau khi cap nhat he dieu hanh', '2026-10-20 08:00:00', '2026-10-25 08:00:00', '2026-10-23 16:00:00');

INSERT INTO ticket_status_log (ticket_id, from_status, to_status, changed_by_employee_id) VALUES
(1, NULL,          'MOI',          1),
(1, 'MOI',         'DA_PHAN_CONG', 2),
(1, 'DA_PHAN_CONG','DANG_XU_LY',   3),
(2, NULL,          'MOI',          1),
(3, NULL,          'MOI',          1),
(3, 'MOI',         'DA_PHAN_CONG', 2),
(3, 'DA_PHAN_CONG','DANG_XU_LY',   4),
(3, 'DANG_XU_LY',  'HOAN_TAT',     4),
(3, 'HOAN_TAT',    'DA_DONG',      2);
