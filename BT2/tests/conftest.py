"""Fixture dùng chung cho unit test.

Không dùng MySQL: FakeTicketRepository lưu dữ liệu trong bộ nhớ và mô phỏng commit/rollback.
Fake chỉ thay phần *lưu trữ*; mọi quy tắc nghiệp vụ vẫn chạy thật trong ticket_service.
"""
import copy
from datetime import datetime

import pytest


class FakeTicketRepository:
    """Kho dữ liệu giả trong bộ nhớ, cùng giao diện với MySQLTicketRepository.

    commit() chốt dữ liệu; rollback() khôi phục về lần commit gần nhất,
    nên test có thể kiểm chứng "không để lại phiếu/khách dở dang khi lỗi".
    """

    def __init__(self):
        self.customers, self.devices, self.tickets = {}, {}, {}
        self.status_logs = []  # mỗi phần tử: (ticket_id, from_status, to_status, employee_id)
        self.active_technicians = {1, 2}  # KTV mặc định đang hoạt động
        self._seq = {"customer": 0, "device": 0, "ticket": 0}
        self.commits = 0
        self.rollbacks = 0
        self._saved = self._snapshot()

    # --- tiện ích cho test: dựng sẵn dữ liệu đã commit ---
    def seed_customer(self, full_name, phone):
        cid = self.add_customer(full_name, phone)
        self.commit()
        self.commits = 0  # không tính lần commit dựng dữ liệu
        return cid

    def seed_device(self, customer_id, serial_no, model_name="Seed Model"):
        did = self.add_device(customer_id, serial_no, model_name, None, None)
        self.commit()
        self.commits = 0
        return did

    # --- giao diện repository mà ticket_service gọi ---
    def find_customer_by_phone(self, phone):
        for cid, c in self.customers.items():
            if c["phone"] == phone:
                return {"customer_id": cid}
        return None

    def add_customer(self, full_name, phone):
        self._seq["customer"] += 1
        cid = self._seq["customer"]
        self.customers[cid] = {"full_name": full_name, "phone": phone}
        return cid

    def find_device_by_serial(self, serial_no):
        for did, d in self.devices.items():
            if d["serial_no"] == serial_no:
                return {"device_id": did, "customer_id": d["customer_id"]}
        return None

    def add_device(self, customer_id, serial_no, model_name, purchase_date, warranty_months):
        self._seq["device"] += 1
        did = self._seq["device"]
        self.devices[did] = {
            "customer_id": customer_id,
            "serial_no": serial_no,
            "model_name": model_name,
            "purchase_date": purchase_date,
            "warranty_months": warranty_months,
        }
        return did

    def add_ticket(self, **fields):
        self._seq["ticket"] += 1
        tid = self._seq["ticket"]
        record = {"technician_id": None, "closed_at": None}
        record.update(fields)
        self.tickets[tid] = record
        return tid

    def set_ticket_code(self, ticket_id, ticket_code):
        self.tickets[ticket_id]["ticket_code"] = ticket_code

    def add_status_log(self, ticket_id, from_status, to_status, employee_id):
        self.status_logs.append((ticket_id, from_status, to_status, employee_id))

    def get_ticket_for_update(self, ticket_id):
        if ticket_id in self.tickets:
            t = copy.deepcopy(self.tickets[ticket_id])
            t["ticket_id"] = ticket_id
            return t
        return None

    def update_ticket_classification(self, ticket_id, category, priority, due_date):
        if ticket_id in self.tickets:
            self.tickets[ticket_id]["issue_category"] = category
            self.tickets[ticket_id]["priority"] = priority
            self.tickets[ticket_id]["due_date"] = due_date

    def assign_technician(self, ticket_id, tech_id):
        if ticket_id in self.tickets:
            self.tickets[ticket_id]["technician_id"] = tech_id
            self.tickets[ticket_id]["ticket_status"] = "DA_PHAN_CONG"

    def find_active_technician(self, tech_id):
        if tech_id in self.active_technicians:
            return {"technician_id": tech_id}
        return None

    def update_ticket_status(self, ticket_id, new_status):
        if ticket_id in self.tickets:
            self.tickets[ticket_id]["ticket_status"] = new_status

    def close_ticket(self, ticket_id, closed_at):
        if ticket_id in self.tickets:
            self.tickets[ticket_id]["ticket_status"] = "DA_DONG"
            self.tickets[ticket_id]["closed_at"] = closed_at

    def update_ticket_desc(self, ticket_id, issue_desc):
        if ticket_id in self.tickets:
            self.tickets[ticket_id]["issue_desc"] = issue_desc

    def admin_update_ticket(
        self, ticket_id, issue_category, priority, due_date, issue_desc, ticket_status, technician_id, closed_at=None
    ):
        if ticket_id in self.tickets:
            t = self.tickets[ticket_id]
            t["issue_category"] = issue_category
            t["priority"] = priority
            t["due_date"] = due_date
            t["issue_desc"] = issue_desc
            t["ticket_status"] = ticket_status
            t["technician_id"] = technician_id
            t["closed_at"] = closed_at

    def commit(self):
        self.commits += 1
        self._saved = self._snapshot()

    def rollback(self):
        self.rollbacks += 1
        (self.customers, self.devices, self.tickets, self.status_logs, self._seq) = copy.deepcopy(self._saved)

    def _snapshot(self):
        return copy.deepcopy((self.customers, self.devices, self.tickets, self.status_logs, self._seq))


@pytest.fixture
def repo():
    """Kho dữ liệu giả sạch cho mỗi test (tự tạo, không phụ thuộc dữ liệu trên máy)."""
    return FakeTicketRepository()


@pytest.fixture
def now():
    """Thời điểm tiếp nhận cố định: Thứ Hai 26/10/2026 09:00 (để kiểm tra hạn cam kết xác định được)."""
    return datetime(2026, 10, 26, 9, 0, 0)


@pytest.fixture
def make_data():
    """Tạo dữ liệu form hợp lệ; truyền tham số để ghi đè từng trường cần thử."""
    def _make(**overrides):
        data = {
            "phone": "0843310647",
            "full_name": "Vu The Long",
            "serial_no": "IMEI350000000000001",
            "model_name": "Mekong Phone X1",
            "purchase_date": "2026-03-15",
            "warranty_months": "12",
            "issue_category": "MAN_HINH",
            "priority": "CAO",
            "issue_desc": "Man hinh bi soc doc, khong cam ung duoc",
        }
        data.update(overrides)
        return data
    return _make


@pytest.fixture
def assert_nothing_created():
    """Trả về hàm khẳng định kho dữ liệu không có khách/thiết bị/phiếu/log nào được lưu."""
    def _check(repo):
        assert repo.tickets == {}, "không được tạo phiếu"
        assert repo.status_logs == [], "không được ghi log trạng thái"
        assert repo.devices == {}, "không được tạo thiết bị"
        assert repo.customers == {}, "không được tạo khách hàng"
        assert repo.commits == 0, "không được commit"
    return _check
