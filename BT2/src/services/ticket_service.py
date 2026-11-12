"""Lớp dịch vụ nghiệp vụ (Service Layer) cho quản lý phiếu bảo hành.

Không phụ thuộc vào Flask routes hay framework web.
Toàn bộ tương tác dữ liệu được thực hiện thông qua repo (Repository Pattern).
"""
import calendar
import uuid
from datetime import date, datetime, timedelta

from validators.ticket_validator import (CATEGORY_LABELS, MIN_DESC_LENGTH,
                                         PRIORITY_LABELS, STATUS_LABELS,
                                         STATUS_ORDER, AuthorizationError,
                                         NotFoundError, ValidationError,
                                         mask_phone, normalize_phone,
                                         validate_ticket_input)

# QT-04: Giờ cam kết hoàn tất theo mức ưu tiên
SLA_HOURS = {"CAO": 24, "TRUNG_BINH": 72, "THAP": 120}

# QT-06: Trạng thái khởi tạo của mọi phiếu mới
INITIAL_STATUS = "MOI"

# QT-06: Quy trình chuyển trạng thái tuyến tính bắt buộc của Kỹ thuật viên
TECH_TRANSITIONS = {
    "DA_PHAN_CONG": ["DANG_XU_LY"],
    "DANG_XU_LY": ["CHO_LINH_KIEN"],
    "CHO_LINH_KIEN": ["HOAN_TAT"],
}


def compute_due_date(received_at, priority):
    """QT-04: Sinh hạn cam kết từ thời điểm tiếp nhận theo mức ưu tiên.

    Chỉ tính ngày làm việc từ Thứ Hai đến Thứ Bảy (bỏ qua ngày Chủ Nhật).
    """
    days_left = SLA_HOURS[priority] // 24
    due = received_at
    while days_left > 0:
        due += timedelta(days=1)
        if due.weekday() != 6:  # 6 = Chủ Nhật
            days_left -= 1
    return due


def _add_months(start_date, months):
    """Cộng chính xác số tháng theo lịch, giữ ngày cuối tháng hợp lệ nếu vượt quá."""
    total_months = start_date.month - 1 + months
    year = start_date.year + total_months // 12
    month = total_months % 12 + 1
    day = min(start_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def warranty_state(ticket):
    """QT-05: Xác định tình trạng bảo hành của thiết bị tại thời điểm tiếp nhận."""
    purchase = ticket.get("purchase_date")
    months = ticket.get("warranty_months")
    if not purchase or months is None or months < 0:
        return "unverified"
    purchase_date = purchase.date() if isinstance(purchase, datetime) else purchase
    received = ticket["received_at"]
    received_date = received.date() if isinstance(received, datetime) else received
    expiry_date = _add_months(purchase_date, months)
    return "ok" if received_date <= expiry_date else "expired"


def create_ticket(repo, data, employee_id, now=None):
    """UC01: Tạo phiếu bảo hành mới (khách hàng + thiết bị + mô tả sự cố)."""
    clean = validate_ticket_input(data)
    received_at = (now or datetime.now()).replace(microsecond=0)

    try:
        # QT-01: SĐT là duy nhất; nếu đã tồn tại thì dùng lại thông tin khách
        customer = repo.find_customer_by_phone(clean["phone"])
        if customer:
            customer_id = customer["customer_id"]
        else:
            if not clean["full_name"]:
                raise ValidationError("Khách hàng mới: vui lòng nhập họ tên.", ["full_name"])
            customer_id = repo.add_customer(clean["full_name"], clean["phone"])

        # QT-03: Serial/IMEI duy nhất; mỗi máy chỉ thuộc một khách hàng
        device = repo.find_device_by_serial(clean["serial_no"])
        if device:
            if device["customer_id"] != customer_id:
                raise ValidationError("Serial/IMEI này đang thuộc về khách hàng khác.", ["serial_no"])
            device_id = device["device_id"]
        else:
            if not clean["model_name"]:
                raise ValidationError("Thiết bị mới: vui lòng nhập tên model.", ["model_name"])
            device_id = repo.add_device(
                customer_id,
                clean["serial_no"],
                clean["model_name"],
                clean["purchase_date"],
                clean["warranty_months"],
            )

        # QT-04: Tự động sinh hạn cam kết
        due_date = compute_due_date(received_at, clean["priority"])

        # Sinh mã phiếu duy nhất dựa trên ticket_id tuần tự
        ticket_id = repo.add_ticket(
            ticket_code="TMP-" + uuid.uuid4().hex[:12],
            customer_id=customer_id,
            device_id=device_id,
            received_by_employee_id=employee_id,
            issue_category=clean["issue_category"],
            priority=clean["priority"],
            ticket_status=INITIAL_STATUS,
            issue_desc=clean["issue_desc"],
            received_at=received_at,
            due_date=due_date,
        )
        ticket_code = f"BH-{ticket_id:04d}"
        repo.set_ticket_code(ticket_id, ticket_code)

        # QT-06: Ghi log trạng thái khởi tạo
        repo.add_status_log(ticket_id, None, INITIAL_STATUS, employee_id)
        repo.commit()
    except Exception:
        repo.rollback()
        raise

    return {
        "ticket_id": ticket_id,
        "ticket_code": ticket_code,
        "customer_id": customer_id,
        "device_id": device_id,
        "ticket_status": INITIAL_STATUS,
        "received_at": received_at,
        "due_date": due_date,
    }


def classify_ticket(repo, ticket_id, category, priority):
    """UC02: Phân loại phiếu bảo hành (nhóm sự cố và mức ưu tiên)."""
    if category not in CATEGORY_LABELS or priority not in PRIORITY_LABELS:
        raise ValidationError("Nhóm sự cố hoặc mức ưu tiên không hợp lệ.")

    t = repo.get_ticket_for_update(ticket_id)
    if not t:
        raise NotFoundError("Không tìm thấy phiếu.")
    if t["ticket_status"] in ("HOAN_TAT", "DA_DONG"):
        raise ValidationError("Phiếu đã hoàn tất hoặc đã đóng, không thể phân loại lại.")

    due = compute_due_date(t["received_at"], priority)
    repo.update_ticket_classification(ticket_id, category, priority, due)
    repo.commit()
    return t["ticket_code"]


def assign_technician(repo, ticket_id, tech_id, employee_id):
    """UC04: Gán đúng 1 kỹ thuật viên đang hoạt động cho phiếu bảo hành."""
    t = repo.get_ticket_for_update(ticket_id)
    if not t:
        raise NotFoundError("Không tìm thấy phiếu.")
    if t.get("technician_id") is not None:
        raise ValidationError("Phiếu đã có kỹ thuật viên, không thể gán thêm người thứ hai.")
    if t["ticket_status"] != "MOI":
        raise ValidationError("Chỉ phiếu ở trạng thái Mới mới được phân công.")
    if not isinstance(tech_id, int) or tech_id <= 0 or not repo.find_active_technician(tech_id):
        raise ValidationError("Kỹ thuật viên không tồn tại hoặc đã ngừng hoạt động.", ["technician_id"])

    repo.assign_technician(ticket_id, tech_id)
    repo.add_status_log(ticket_id, "MOI", "DA_PHAN_CONG", employee_id)
    repo.commit()
    return t["ticket_code"]


def close_ticket(repo, ticket_id, employee_id):
    """UC07: Đóng phiếu bảo hành khi đã ở trạng thái Hoàn tất."""
    t = repo.get_ticket_for_update(ticket_id)
    if not t:
        raise NotFoundError("Không tìm thấy phiếu.")
    if t["ticket_status"] != "HOAN_TAT":
        raise ValidationError("Chỉ đóng được phiếu ở trạng thái Hoàn tất.")

    now = datetime.now().replace(microsecond=0)
    repo.close_ticket(ticket_id, now)
    repo.add_status_log(ticket_id, "HOAN_TAT", "DA_DONG", employee_id)
    repo.commit()
    return t["ticket_code"]


def update_tech_status(repo, ticket_id, tech_id, new_status, employee_id):
    """UC06: Kỹ thuật viên cập nhật trạng thái theo đúng tiến trình tuyến tính."""
    t = repo.get_ticket_for_update(ticket_id)
    if not t:
        raise NotFoundError("Không tìm thấy phiếu.")
    if t.get("technician_id") != tech_id:
        raise AuthorizationError("Phiếu này không được phân công cho bạn.")

    allowed = TECH_TRANSITIONS.get(t["ticket_status"], [])
    if new_status not in allowed:
        raise ValidationError("Chuyển trạng thái không hợp lệ (không được quay lại hoặc bỏ bước).")

    repo.update_ticket_status(ticket_id, new_status)
    repo.add_status_log(ticket_id, t["ticket_status"], new_status, employee_id)
    repo.commit()
    return t["ticket_code"], t["ticket_status"], new_status


def update_ticket_description(repo, ticket_id, new_desc, employee_id):
    """Nhân viên tiếp nhận chỉnh sửa mô tả sự cố cho phiếu đã tạo."""
    desc = (new_desc or "").strip()
    if len(desc) < MIN_DESC_LENGTH:
        raise ValidationError(f"Mô tả lỗi phải có ít nhất {MIN_DESC_LENGTH} ký tự.", ["issue_desc"])

    t = repo.get_ticket_for_update(ticket_id)
    if not t:
        raise NotFoundError("Không tìm thấy phiếu.")
    if t["ticket_status"] == "DA_DONG":
        raise ValidationError("Phiếu đã đóng, không thể sửa mô tả.")

    repo.update_ticket_desc(ticket_id, desc)
    repo.commit()
    return t["ticket_code"]


def admin_update_ticket(repo, ticket_id, data, employee_id):
    """Quản trị viên cập nhật toàn diện thông tin phiếu bảo hành."""
    t = repo.get_ticket_for_update(ticket_id)
    if not t:
        raise NotFoundError("Không tìm thấy phiếu.")

    category = data.get("issue_category", t["issue_category"])
    priority = data.get("priority", t["priority"])
    new_status = data.get("ticket_status", t["ticket_status"])
    desc = (data.get("issue_desc") or t["issue_desc"]).strip()
    raw_tech = data.get("technician_id")
    tech_id = int(raw_tech) if raw_tech not in (None, "", "None") else None

    if category not in CATEGORY_LABELS:
        raise ValidationError("Nhóm sự cố không hợp lệ.")
    if priority not in PRIORITY_LABELS:
        raise ValidationError("Mức ưu tiên không hợp lệ.")
    if new_status not in STATUS_LABELS:
        raise ValidationError("Trạng thái phiếu không hợp lệ.")
    if len(desc) < MIN_DESC_LENGTH:
        raise ValidationError(f"Mô tả lỗi phải có ít nhất {MIN_DESC_LENGTH} ký tự.")

    # Tính lại hạn cam kết nếu mức ưu tiên thay đổi
    due_date = t["due_date"]
    if priority != t["priority"]:
        due_date = compute_due_date(t["received_at"], priority)

    # Ghi log chuyển trạng thái nếu có thay đổi
    old_status = t["ticket_status"]
    if new_status != old_status:
        repo.add_status_log(ticket_id, old_status, new_status, employee_id)

    # Nếu trạng thái chuyển thành DA_DONG mà chưa có closed_at thì ghi nhận thời điểm đóng
    closed_at = t.get("closed_at")
    if new_status == "DA_DONG" and not closed_at:
        closed_at = datetime.now().replace(microsecond=0)
    elif new_status != "DA_DONG":
        closed_at = None

    repo.admin_update_ticket(
        ticket_id=ticket_id,
        issue_category=category,
        priority=priority,
        due_date=due_date,
        issue_desc=desc,
        ticket_status=new_status,
        technician_id=tech_id,
        closed_at=closed_at,
    )
    repo.commit()
    return t["ticket_code"]
