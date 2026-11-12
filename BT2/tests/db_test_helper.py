"""Tiện ích dựng và dọn sạch cơ sở dữ liệu thật (reset_db) cho Integration & API test.

Hỗ trợ hai chế độ:
- Khi DB_TYPE=mysql (ví dụ chạy trong Docker Compose): reset các bảng trên MySQL và nạp lại dữ liệu mẫu.
- Khi chạy cục bộ không có MySQL: dùng file SQLite tạm riêng cho test (không đụng warranty.db thật).
"""
import os
import socket
import sqlite3
import tempfile
from werkzeug.security import generate_password_hash

from repositories import db_connection

_TEST_SQLITE_PATH = os.path.join(tempfile.gettempdir(), "cdtn01_test_warranty.db")
_PWD_HASH = generate_password_hash("123456")


def _can_resolve_mysql_host():
    host = os.getenv("DB_HOST", "127.0.0.1").strip()
    try:
        socket.gethostbyname(host)
        return True
    except OSError:
        return False


def configure_test_db_env():
    """Đảm bảo test chạy cục bộ (kể cả khi đã tạo .env cho Docker) không lỗi host 'db' hay ghi đè warranty.db."""
    db_type = os.getenv("DB_TYPE", "").strip().lower()
    if db_type != "mysql" or not _can_resolve_mysql_host():
        os.environ["DB_TYPE"] = "sqlite"
        db_connection.SQLITE_DB_PATH = _TEST_SQLITE_PATH


def reset_db():
    """Xóa sạch toàn bộ dữ liệu thử và nạp lại đúng tập fixture mẫu."""
    configure_test_db_env()
    conn = db_connection.connect()

    if isinstance(conn, sqlite3.Connection):
        conn.close()
        if os.path.exists(_TEST_SQLITE_PATH):
            os.remove(_TEST_SQLITE_PATH)
        conn = db_connection.connect()
        conn.close()
        return

    # Chế độ MySQL thật
    cur = conn.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for tbl in ("ticket_status_log", "ticket", "device", "customer", "technician", "employee"):
        cur.execute(f"TRUNCATE TABLE {tbl}")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")

    cur.executemany(
        "INSERT INTO employee (employee_id, full_name, role, phone, is_active, username, password_hash) "
        "VALUES (%s, %s, %s, %s, 1, %s, %s)",
        [
            (1, "Nguyen Thi Lan", "TIEP_NHAN", "0901000001", "nhanvientiepnhan", _PWD_HASH),
            (2, "Tran Van Minh", "QUAN_TRI", "0901000002", "quantrivien", _PWD_HASH),
            (3, "Le Hoang Nam", "KY_THUAT", "0901000003", "kythuatvien", _PWD_HASH),
            (4, "Pham Quoc Bao", "KY_THUAT", "0901000004", "kythuatvien2", _PWD_HASH),
        ],
    )
    cur.executemany(
        "INSERT INTO technician (technician_id, employee_id, center_id, is_active) VALUES (%s, %s, 1, 1)",
        [(1, 3), (2, 4)],
    )
    cur.executemany(
        "INSERT INTO customer (customer_id, full_name, phone, email, segment) VALUES (%s, %s, %s, %s, %s)",
        [
            (1, "Vu The Long", "0843310647", "long@example.com", "VIP"),
            (2, "Nguyen Van An", "0912345678", "an@example.com", "THUONG"),
            (3, "Tran Thi Hoa", "0987654321", None, "THUONG"),
        ],
    )
    cur.executemany(
        "INSERT INTO device (device_id, customer_id, serial_no, model_name, purchase_date, warranty_months) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        [
            (1, 1, "IMEI350000000000001", "Mekong Phone X1", "2026-03-15", 12),
            (2, 2, "IMEI350000000000002", "Mekong Phone X2", "2025-01-10", 12),
            (3, 3, "IMEI350000000000003", "Mekong Tab T1", "2026-08-01", 24),
        ],
    )
    cur.executemany(
        "INSERT INTO ticket (ticket_id, ticket_code, customer_id, device_id, technician_id, "
        "received_by_employee_id, issue_category, priority, ticket_status, issue_desc, "
        "received_at, due_date, closed_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        [
            (1, "BH-0001", 1, 1, 1, 1, "MAN_HINH", "CAO", "DANG_XU_LY",
             "Man hinh bi soc doc, khong cam ung duoc", "2026-10-24 09:00:00", "2026-10-25 09:00:00", None),
            (2, "BH-0002", 2, 2, None, 1, "PIN", "TRUNG_BINH", "MOI",
             "Pin tut nhanh, may nong khi sac", "2026-10-25 10:30:00", "2026-10-28 10:30:00", None),
            (3, "BH-0003", 3, 3, 2, 1, "PHAN_MEM", "THAP", "DA_DONG",
             "May bi treo logo sau khi cap nhat he dieu hanh", "2026-10-20 08:00:00", "2026-10-25 08:00:00",
             "2026-10-23 16:00:00"),
        ],
    )
    cur.executemany(
        "INSERT INTO ticket_status_log (ticket_id, from_status, to_status, changed_by_employee_id) "
        "VALUES (%s, %s, %s, %s)",
        [
            (1, None, "MOI", 1),
            (1, "MOI", "DA_PHAN_CONG", 2),
            (1, "DA_PHAN_CONG", "DANG_XU_LY", 3),
            (2, None, "MOI", 1),
            (3, None, "MOI", 1),
            (3, "MOI", "DA_PHAN_CONG", 2),
            (3, "DA_PHAN_CONG", "DANG_XU_LY", 4),
            (3, "DANG_XU_LY", "HOAN_TAT", 4),
            (3, "HOAN_TAT", "DA_DONG", 2),
        ],
    )
    conn.commit()
    cur.close()
    conn.close()

