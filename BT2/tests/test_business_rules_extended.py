"""Unit test bổ sung cho các quy tắc nghiệp vụ chưa có test ở BT2:
- UC02 / FR3: classify_ticket
- UC04 / FR5 / US4-AC3: assign_technician
- UC06 / FR7 / QT-06: update_tech_status
- QT-05: warranty_state (biên ngày bảo hành)
- QT-15: mask_phone
"""
from datetime import date, datetime

import pytest
from services.ticket_service import (
    ValidationError,
    assign_technician,
    classify_ticket,
    create_ticket,
    mask_phone,
    update_tech_status,
    warranty_state,
)

RECEPTION_ID = 1
ADMIN_ID = 2
TECH1_EMP_ID = 3
TECH1_ID = 1
TECH2_ID = 2


class TestClassifyTicket:
    def test_classify_ticket_updates_category_priority_and_due_date(self, repo, make_data, now):
        info = create_ticket(repo, make_data(issue_category="KHAC", priority="THAP"), RECEPTION_ID, now=now)
        tid = info["ticket_id"]

        code = classify_ticket(repo, tid, "PIN", "CAO")

        assert code == info["ticket_code"]
        assert repo.tickets[tid]["issue_category"] == "PIN"
        assert repo.tickets[tid]["priority"] == "CAO"
        assert repo.tickets[tid]["due_date"] == datetime(2026, 10, 27, 9, 0, 0)

    def test_classify_ticket_rejects_invalid_category_or_priority(self, repo, make_data, now):
        info = create_ticket(repo, make_data(), RECEPTION_ID, now=now)
        with pytest.raises(ValidationError, match="không hợp lệ"):
            classify_ticket(repo, info["ticket_id"], "KHONG_TON_TAI", "CAO")

    def test_classify_ticket_rejects_closed_ticket(self, repo, make_data, now):
        info = create_ticket(repo, make_data(), RECEPTION_ID, now=now)
        repo.tickets[info["ticket_id"]]["ticket_status"] = "DA_DONG"

        with pytest.raises(ValidationError, match="hoàn tất hoặc đã đóng"):
            classify_ticket(repo, info["ticket_id"], "PIN", "CAO")


class TestAssignTechnician:
    def test_assign_technician_success(self, repo, make_data, now):
        info = create_ticket(repo, make_data(), RECEPTION_ID, now=now)
        tid = info["ticket_id"]

        code = assign_technician(repo, tid, TECH1_ID, ADMIN_ID)

        assert code == info["ticket_code"]
        assert repo.tickets[tid]["technician_id"] == TECH1_ID
        assert repo.tickets[tid]["ticket_status"] == "DA_PHAN_CONG"
        assert (tid, "MOI", "DA_PHAN_CONG", ADMIN_ID) in repo.status_logs

    def test_assign_technician_rejects_second_assignment(self, repo, make_data, now):
        info = create_ticket(repo, make_data(), RECEPTION_ID, now=now)
        tid = info["ticket_id"]
        assign_technician(repo, tid, TECH1_ID, ADMIN_ID)

        with pytest.raises(ValidationError, match="đã có kỹ thuật viên"):
            assign_technician(repo, tid, TECH2_ID, ADMIN_ID)
        assert repo.tickets[tid]["technician_id"] == TECH1_ID

    def test_assign_technician_rejects_inactive_or_missing_technician(self, repo, make_data, now):
        """US4-AC3: KTV không tồn tại hoặc ngừng hoạt động -> phải từ chối, giữ nguyên phiếu."""
        info = create_ticket(repo, make_data(), RECEPTION_ID, now=now)
        tid = info["ticket_id"]

        with pytest.raises(ValidationError):
            assign_technician(repo, tid, 999, ADMIN_ID)

        assert repo.tickets[tid]["technician_id"] is None
        assert repo.tickets[tid]["ticket_status"] == "MOI"


class TestTechStatusTransitions:
    def test_linear_tech_workflow_succeeds_and_logs_history(self, repo, make_data, now):
        info = create_ticket(repo, make_data(), RECEPTION_ID, now=now)
        tid = info["ticket_id"]
        assign_technician(repo, tid, TECH1_ID, ADMIN_ID)

        for next_st in ("DANG_XU_LY", "CHO_LINH_KIEN", "HOAN_TAT"):
            code, old_st, new_st = update_tech_status(repo, tid, TECH1_ID, next_st, TECH1_EMP_ID)
            assert code == info["ticket_code"]
            assert new_st == next_st
            assert repo.tickets[tid]["ticket_status"] == next_st

        assert (tid, "DA_PHAN_CONG", "DANG_XU_LY", TECH1_EMP_ID) in repo.status_logs
        assert (tid, "DANG_XU_LY", "CHO_LINH_KIEN", TECH1_EMP_ID) in repo.status_logs
        assert (tid, "CHO_LINH_KIEN", "HOAN_TAT", TECH1_EMP_ID) in repo.status_logs

    def test_update_tech_status_rejects_skip_or_backward_transition(self, repo, make_data, now):
        info = create_ticket(repo, make_data(), RECEPTION_ID, now=now)
        tid = info["ticket_id"]
        assign_technician(repo, tid, TECH1_ID, ADMIN_ID)

        with pytest.raises(ValidationError, match="không hợp lệ"):
            update_tech_status(repo, tid, TECH1_ID, "HOAN_TAT", TECH1_EMP_ID)
        assert repo.tickets[tid]["ticket_status"] == "DA_PHAN_CONG"

    def test_update_tech_status_rejects_non_owner_technician(self, repo, make_data, now):
        info = create_ticket(repo, make_data(), RECEPTION_ID, now=now)
        tid = info["ticket_id"]
        assign_technician(repo, tid, TECH1_ID, ADMIN_ID)

        with pytest.raises(ValidationError, match="không được phân công cho bạn"):
            update_tech_status(repo, tid, TECH2_ID, "DANG_XU_LY", 4)
        assert repo.tickets[tid]["ticket_status"] == "DA_PHAN_CONG"


class TestWarrantyBoundaryAndMasking:
    def test_warranty_on_exact_expiration_day_is_ok(self):
        """Biên dưới/đúng hạn: mua 15/03/2025, BH 12 tháng -> ngày 15/03/2026 vẫn còn BH."""
        ticket = {
            "purchase_date": date(2025, 3, 15),
            "warranty_months": 12,
            "received_at": datetime(2026, 3, 15, 17, 0, 0),
        }
        assert warranty_state(ticket) == "ok"

    def test_warranty_one_day_after_expiration_is_expired(self):
        """Biên trên/quá hạn: ngày 16/03/2026 (quá hạn 1 ngày) phải trả 'expired'."""
        ticket = {
            "purchase_date": date(2025, 3, 15),
            "warranty_months": 12,
            "received_at": datetime(2026, 3, 16, 8, 0, 0),
        }
        assert warranty_state(ticket) == "expired"

    def test_warranty_without_purchase_date_is_unverified(self):
        ticket = {
            "purchase_date": None,
            "warranty_months": 12,
            "received_at": datetime(2026, 10, 26, 9, 0, 0),
        }
        assert warranty_state(ticket) == "unverified"

    def test_mask_phone_hides_middle_digits(self):
        assert mask_phone("0843310647") == "084****647"

