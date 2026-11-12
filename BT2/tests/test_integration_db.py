"""Integration test chạy trên cơ sở dữ liệu thật (MySQL hoặc SQLite test DB).

Dữ liệu thử được reset sạch trước mỗi test bằng reset_db() và khôi phục
lại dữ liệu mẫu sau khi chạy xong module test.
"""
from datetime import datetime

import pytest
from tests.db_test_helper import reset_db
from main import app
from repositories import MySQLTicketRepository, db_connection
from services.ticket_service import (
    ValidationError,
    assign_technician,
    close_ticket,
    create_ticket,
    update_tech_status,
)


@pytest.fixture(autouse=True)
def clean_database():
    reset_db()
    yield
    reset_db()


def test_real_db_full_ticket_lifecycle_persistence():
    """IT-01: Tạo phiếu -> phân công -> KTV hoàn tất -> đóng phiếu trên DB thật."""
    with app.app_context():
        repo = MySQLTicketRepository()
        now = datetime(2026, 11, 2, 9, 0, 0)

        created = create_ticket(
            repo,
            {
                "phone": "+84 909 111 222",
                "full_name": "Le Van Cuong",
                "serial_no": "IMEI359999999999001",
                "model_name": "Mekong Phone Pro",
                "purchase_date": "2026-01-15",
                "warranty_months": "12",
                "issue_category": "SAC",
                "priority": "CAO",
                "issue_desc": "Khong nhan sac nhanh va cong sac bi long",
            },
            employee_id=1,
            now=now,
        )
        tid = created["ticket_id"]
        assert created["ticket_code"] == f"BH-{tid:04d}"

        assign_technician(repo, tid, tech_id=1, employee_id=2)
        update_tech_status(repo, tid, tech_id=1, new_status="DANG_XU_LY", employee_id=3)
        update_tech_status(repo, tid, tech_id=1, new_status="CHO_LINH_KIEN", employee_id=3)
        update_tech_status(repo, tid, tech_id=1, new_status="HOAN_TAT", employee_id=3)
        close_ticket(repo, tid, employee_id=1)

        row = db_connection.query(
            "SELECT ticket_status, technician_id, closed_at FROM ticket WHERE ticket_id = %s",
            (tid,),
            one=True,
        )
        logs = db_connection.query(
            "SELECT from_status, to_status FROM ticket_status_log WHERE ticket_id = %s ORDER BY log_id",
            (tid,),
        )
        assert row["ticket_status"] == "DA_DONG"
        assert row["technician_id"] == 1
        assert row["closed_at"] is not None
        assert [(l["from_status"], l["to_status"]) for l in logs] == [
            (None, "MOI"),
            ("MOI", "DA_PHAN_CONG"),
            ("DA_PHAN_CONG", "DANG_XU_LY"),
            ("DANG_XU_LY", "CHO_LINH_KIEN"),
            ("CHO_LINH_KIEN", "HOAN_TAT"),
            ("HOAN_TAT", "DA_DONG"),
        ]


def test_real_db_rejects_nonexistent_technician_without_corrupting_ticket():
    """IT-02: Gán KTV không tồn tại trên DB thật phải báo ValidationError và giữ nguyên phiếu."""
    with app.app_context():
        repo = MySQLTicketRepository()
        with pytest.raises(ValidationError):
            assign_technician(repo, ticket_id=2, tech_id=999, employee_id=2)

        row = db_connection.query(
            "SELECT ticket_status, technician_id FROM ticket WHERE ticket_id = 2",
            one=True,
        )
        assert row["ticket_status"] == "MOI"
        assert row["technician_id"] is None


def test_real_db_serial_conflict_rolls_back_new_customer():
    """IT-03: Serial đã thuộc khách khác -> transaction rollback sạch khách vừa tạo trên DB thật."""
    with app.app_context():
        repo = MySQLTicketRepository()
        before_count = db_connection.query("SELECT COUNT(*) AS n FROM customer", one=True)["n"]

        with pytest.raises(ValidationError, match="thuộc về khách hàng khác"):
            create_ticket(
                repo,
                {
                    "phone": "0933444555",
                    "full_name": "Khach Bi Rollback",
                    "serial_no": "IMEI350000000000001",  # đã thuộc khách 1 trong seed
                    "model_name": "Mekong Phone X1",
                    "issue_category": "PIN",
                    "priority": "THAP",
                    "issue_desc": "Pin bi phong nhe can kiem tra",
                },
                employee_id=1,
            )

        after_count = db_connection.query("SELECT COUNT(*) AS n FROM customer", one=True)["n"]
        assert after_count == before_count
