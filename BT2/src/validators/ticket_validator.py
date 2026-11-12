"""Module kiểm tra hợp lệ (Validator Layer) cho phiếu bảo hành.

Chịu trách nhiệm kiểm tra dữ liệu đầu vào và các ràng buộc nghiệp vụ:
- QT-02: Chuẩn hóa số điện thoại về 10 chữ số bắt đầu bằng 0.
- QT-15: Che số điện thoại cho các vai trò không phải Quản lý / Ban giám đốc.
- FR2: Mô tả lỗi bắt buộc có tối thiểu 10 ký tự.
- FR3: Nhóm sự cố và mức ưu tiên phải nằm trong danh mục cho phép.
- US1-AC3: Báo lỗi rõ ràng kèm tên các trường còn thiếu.
"""
import re
from datetime import date

# ----------------------------------------------------------------------------
# Hằng số nghiệp vụ
# ----------------------------------------------------------------------------
PRIORITY_LABELS = {"CAO": "Cao", "TRUNG_BINH": "Trung bình", "THAP": "Thấp"}
CATEGORY_LABELS = {
    "MAN_HINH": "Màn hình",
    "PIN": "Pin",
    "SAC": "Sạc",
    "PHAN_MEM": "Phần mềm",
    "NUOC_VAO": "Nước vào",
    "KHAC": "Khác",
}

STATUS_LABELS = {
    "MOI": "Mới",
    "DA_PHAN_CONG": "Đã phân công",
    "DANG_XU_LY": "Đang xử lý",
    "CHO_LINH_KIEN": "Chờ linh kiện",
    "HOAN_TAT": "Hoàn tất",
    "DA_DONG": "Đã đóng",
}

# Thứ tự vòng đời của phiếu bảo hành
STATUS_ORDER = list(STATUS_LABELS.keys())

# FR2: Mô tả lỗi tối thiểu 10 ký tự
MIN_DESC_LENGTH = 10

# Tên trường thân thiện khi báo lỗi (US1-AC3)
REQUIRED_FIELD_LABELS = {
    "phone": "Số điện thoại hợp lệ (10 số)",
    "serial_no": "Số serial/IMEI",
    "issue_desc": "Mô tả lỗi",
}


class ValidationError(Exception):
    """Ngoại lệ khi dữ liệu đầu vào vi phạm quy tắc nghiệp vụ."""

    def __init__(self, message, fields=None, status_code=400):
        super().__init__(message)
        self.message = message
        self.fields = fields or []
        self.status_code = status_code


class AuthorizationError(ValidationError):
    """Ngoại lệ khi người dùng vi phạm quyền sở hữu hoặc phân quyền (HTTP 403)."""

    def __init__(self, message, fields=None):
        super().__init__(message, fields=fields, status_code=403)


class NotFoundError(ValidationError):
    """Ngoại lệ khi không tìm thấy tài nguyên yêu cầu (HTTP 404)."""

    def __init__(self, message, fields=None):
        super().__init__(message, fields=fields, status_code=404)


def normalize_phone(raw):
    """QT-02: Chuẩn hóa SĐT về 10 chữ số bắt đầu bằng 0.

    Chấp nhận các định dạng +84..., 84..., có dấu cách hoặc dấu chấm.
    Trả về None nếu không thể chuẩn hóa thành 10 chữ số hợp lệ.
    """
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("84") and len(digits) == 11:
        digits = "0" + digits[2:]
    return digits if re.fullmatch(r"0\d{9}", digits) else None


def mask_phone(phone):
    """QT-15: Che số điện thoại khách hàng, ví dụ: 0901234567 -> 090****567."""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-3:]


def parse_optional_date(value):
    """Phân tích ngày tháng an toàn từ chuỗi ISO (YYYY-MM-DD) hoặc đối tượng date."""
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def validate_ticket_input(data):
    """Kiểm tra và chuẩn hóa dữ liệu tạo phiếu mới (UC01).

    Ném ValidationError nếu dữ liệu không hợp lệ. Trả về dict đã chuẩn hóa sạch.
    """
    phone = normalize_phone(data.get("phone"))
    serial = (data.get("serial_no") or "").strip()
    desc = (data.get("issue_desc") or "").strip()

    # US1-AC3: Nêu rõ từng trường bắt buộc còn thiếu
    invalid_fields = []
    if not phone:
        invalid_fields.append("phone")
    if not serial:
        invalid_fields.append("serial_no")
    if not desc:
        invalid_fields.append("issue_desc")
    if invalid_fields:
        labels = ", ".join(REQUIRED_FIELD_LABELS[f] for f in invalid_fields)
        raise ValidationError(f"Không thể lưu phiếu. Thiếu/không hợp lệ: {labels}.", invalid_fields)

    # FR2: Mô tả lỗi tối thiểu 10 ký tự (đúng 10 ký tự vẫn được chấp nhận)
    if len(desc) < MIN_DESC_LENGTH:
        raise ValidationError(f"Mô tả lỗi phải có ít nhất {MIN_DESC_LENGTH} ký tự.", ["issue_desc"])

    # FR3 / US2-AC2: Nhóm sự cố và mức ưu tiên hợp lệ
    category = data.get("issue_category")
    priority = data.get("priority")
    if category not in CATEGORY_LABELS or priority not in PRIORITY_LABELS:
        raise ValidationError("Nhóm sự cố hoặc mức ưu tiên không hợp lệ.", ["issue_category", "priority"])

    try:
        purchase_date = parse_optional_date(data.get("purchase_date"))
        months = data.get("warranty_months")
        warranty_months = None if months in (None, "") else int(months)
    except (ValueError, TypeError):
        raise ValidationError("Ngày mua hoặc số tháng bảo hành không hợp lệ.", ["purchase_date", "warranty_months"])

    return {
        "phone": phone,
        "full_name": (data.get("full_name") or "").strip(),
        "serial_no": serial,
        "model_name": (data.get("model_name") or "").strip(),
        "purchase_date": purchase_date,
        "warranty_months": warranty_months,
        "issue_category": category,
        "priority": priority,
        "issue_desc": desc,
    }
