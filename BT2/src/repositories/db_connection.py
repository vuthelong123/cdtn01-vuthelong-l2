"""Quản lý kết nối cơ sở dữ liệu: Hỗ trợ linh hoạt cả MySQL và SQLite nhúng.

- Tự động ưu tiên kết nối MySQL nếu có sẵn (cấu hình qua .env).
- Nếu MySQL không chạy hoặc không cài đặt, tự động chuyển sang SQLite nhúng (warranty.db).
- Tự động tạo bảng và nạp dữ liệu mẫu cho SQLite ngay lần đầu khởi chạy,
  giúp giảng viên/người dùng tái tạo dự án chỉ với 1 lệnh mà không cần cài đặt MySQL.
"""
import os
import re
import sqlite3
from datetime import date, datetime

from dotenv import load_dotenv
from flask import g
from werkzeug.security import generate_password_hash

# Đọc cấu hình từ file .env ở thư mục gốc BT2
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

SQLITE_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "warranty.db")
)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS employee (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    phone TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE IF NOT EXISTS customer (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    email TEXT,
    segment TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS device (
    device_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    serial_no TEXT NOT NULL UNIQUE,
    model_name TEXT NOT NULL,
    purchase_date DATE,
    warranty_months INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
);

CREATE TABLE IF NOT EXISTS technician (
    technician_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL UNIQUE,
    center_id INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (employee_id) REFERENCES employee(employee_id)
);

CREATE TABLE IF NOT EXISTS ticket (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_code TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    device_id INTEGER NOT NULL,
    technician_id INTEGER NULL,
    received_by_employee_id INTEGER NOT NULL,
    issue_category TEXT NOT NULL,
    priority TEXT NOT NULL,
    ticket_status TEXT NOT NULL,
    issue_desc TEXT NOT NULL,
    received_at TIMESTAMP NOT NULL,
    due_date TIMESTAMP NOT NULL,
    closed_at TIMESTAMP NULL,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    FOREIGN KEY (device_id) REFERENCES device(device_id),
    FOREIGN KEY (technician_id) REFERENCES technician(technician_id),
    FOREIGN KEY (received_by_employee_id) REFERENCES employee(employee_id)
);

CREATE TABLE IF NOT EXISTS ticket_status_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by_employee_id INTEGER NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES ticket(ticket_id),
    FOREIGN KEY (changed_by_employee_id) REFERENCES employee(employee_id)
);
"""


def _init_sqlite(conn):
    """Tự động khởi tạo schema và nạp dữ liệu mẫu ban đầu nếu bảng chưa tồn tại."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employee'")
    if cur.fetchone():
        return

    cur.executescript(SCHEMA_SQL)
    pwd_hash = generate_password_hash("123456")

    cur.executemany(
        "INSERT INTO employee (employee_id, full_name, role, phone, is_active, username, password_hash) VALUES (?, ?, ?, ?, 1, ?, ?)",
        [
            (1, "Nguyen Thi Lan",  "TIEP_NHAN", "0901000001", "nhanvientiepnhan", pwd_hash),
            (2, "Tran Van Minh",   "QUAN_TRI",  "0901000002", "quantrivien",     pwd_hash),
            (3, "Le Hoang Nam",    "KY_THUAT",  "0901000003", "kythuatvien",     pwd_hash),
            (4, "Pham Quoc Bao",   "KY_THUAT",  "0901000004", "kythuatvien2",    pwd_hash),
        ],
    )
    cur.executemany(
        "INSERT INTO technician (technician_id, employee_id, center_id, is_active) VALUES (?, ?, 1, 1)",
        [(1, 3), (2, 4)],
    )
    cur.executemany(
        "INSERT INTO customer (customer_id, full_name, phone, email, segment) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "Vu The Long",    "0843310647", "long@example.com",  "VIP"),
            (2, "Nguyen Van An",  "0912345678", "an@example.com",    "THUONG"),
            (3, "Tran Thi Hoa",   "0987654321", None,                "THUONG"),
        ],
    )
    cur.executemany(
        "INSERT INTO device (device_id, customer_id, serial_no, model_name, purchase_date, warranty_months) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, 1, "IMEI350000000000001", "Mekong Phone X1", "2026-03-15", 12),
            (2, 2, "IMEI350000000000002", "Mekong Phone X2", "2025-01-10", 12),
            (3, 3, "IMEI350000000000003", "Mekong Tab T1",  "2026-08-01", 24),
        ],
    )
    cur.executemany(
        "INSERT INTO ticket (ticket_id, ticket_code, customer_id, device_id, technician_id, received_by_employee_id, issue_category, priority, ticket_status, issue_desc, received_at, due_date, closed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "BH-0001", 1, 1, 1,    1, "MAN_HINH", "CAO",        "DANG_XU_LY", "Man hinh bi soc doc, khong cam ung duoc",     "2026-10-24 09:00:00", "2026-10-25 09:00:00", None),
            (2, "BH-0002", 2, 2, None, 1, "PIN",      "TRUNG_BINH", "MOI",        "Pin tut nhanh, may nong khi sac",            "2026-10-25 10:30:00", "2026-10-28 10:30:00", None),
            (3, "BH-0003", 3, 3, 2,    1, "PHAN_MEM", "THAP",       "DA_DONG",    "May bi treo logo sau khi cap nhat he dieu hanh", "2026-10-20 08:00:00", "2026-10-25 08:00:00", "2026-10-23 16:00:00"),
        ],
    )
    cur.executemany(
        "INSERT INTO ticket_status_log (ticket_id, from_status, to_status, changed_by_employee_id) VALUES (?, ?, ?, ?)",
        [
            (1, None,          "MOI",          1),
            (1, "MOI",         "DA_PHAN_CONG", 2),
            (1, "DA_PHAN_CONG","DANG_XU_LY",   3),
            (2, None,          "MOI",          1),
            (3, None,          "MOI",          1),
            (3, "MOI",         "DA_PHAN_CONG", 2),
            (3, "DA_PHAN_CONG","DANG_XU_LY",   4),
            (3, "DANG_XU_LY",  "HOAN_TAT",     4),
            (3, "HOAN_TAT",    "DA_DONG",      2),
        ],
    )
    conn.commit()
    print(" [Database] Khoi tao schema va nap du lieu mau SQLite thanh cong (warranty.db).")


def connect():
    """Tạo kết nối mới: ưu tiên theo DB_TYPE (mysql / sqlite / auto fallback)."""
    db_type = os.getenv("DB_TYPE", "").strip().lower()

    if db_type != "sqlite":
        try:
            import mysql.connector

            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "127.0.0.1"),
                port=int(os.getenv("DB_PORT", "3306")),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "warranty_db"),
                charset="utf8mb4",
                autocommit=False,
                connection_timeout=3,
            )
            return conn
        except Exception:
            if db_type == "mysql":
                raise
            # Khi chưa chỉ định DB_TYPE=mysql -> fallback SQLite để chạy nhanh cục bộ

    # Kết nối SQLite nhúng
    sqlite_path = os.getenv("SQLITE_DB_PATH") or SQLITE_DB_PATH
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    _init_sqlite(conn)
    return conn


def check_db_health():
    """Kiểm tra nhanh tình trạng sẵn sàng của CSDL cho endpoint /health."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        return True
    finally:
        conn.close()


def get_db():
    """Lấy kết nối hiện tại trong request context của Flask hoặc tạo mới nếu ngoài context."""
    from flask import has_app_context

    if has_app_context():
        if "db" not in g:
            g.db = connect()
        return g.db
    return connect()


def close_db(_exc=None):
    """Đóng kết nối khi kết thúc request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _is_sqlite(conn):
    return isinstance(conn, sqlite3.Connection)


def _adapt_sql_for_sqlite(sql):
    """Chuyển đổi cú pháp SQL tương thích với SQLite."""
    sql = re.sub(r"\s+FOR\s+UPDATE\b", "", sql, flags=re.IGNORECASE)
    sql = sql.replace("%s", "?")
    return sql


def _parse_val(val):
    """Tự động chuyển chuỗi ngày giờ từ SQLite thành đối tượng datetime/date."""
    if not isinstance(val, str):
        return val
    if len(val) == 10 and val[4] == "-" and val[7] == "-":
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            return val
    if len(val) >= 19 and val[4] == "-" and val[7] == "-":
        try:
            clean = val.replace("T", " ")
            if "." in clean:
                return datetime.strptime(clean, "%Y-%m-%d %H:%M:%S.%f")
            return datetime.strptime(clean[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return val
    return val


def query(sql, args=(), one=False):
    """Thực thi câu truy vấn SELECT và trả về list of dict hoặc dict đơn lẻ."""
    conn = get_db()
    if _is_sqlite(conn):
        cur = conn.cursor()
        cur.execute(_adapt_sql_for_sqlite(sql), args)
        rows = [{k: _parse_val(r[k]) for k in r.keys()} for r in cur.fetchall()]
        cur.close()
        return rows[0] if one and rows else (None if one else rows)

    # MySQL logic
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, args=()):
    """Thực thi INSERT / UPDATE / DELETE và trả về lastrowid."""
    conn = get_db()
    if _is_sqlite(conn):
        cur = conn.cursor()
        cur.execute(_adapt_sql_for_sqlite(sql), args)
        last_id = cur.lastrowid
        cur.close()
        return last_id

    # MySQL logic
    cur = conn.cursor()
    cur.execute(sql, args)
    last_id = cur.lastrowid
    cur.close()
    return last_id
