# BUG LOG — BÀI TẬP 3

Ghi nhận các lỗi thật được phát hiện trong quá trình chạy kiểm thử (`pytest -v`) ở giai đoạn Bài tập 3, đã tìm đúng nguyên nhân gốc, sửa trong mã nguồn và xác minh lại bằng test tự động.

---

### BUG-01 — Tính sai ngày hết hạn bảo hành khiến thiết bị quá hạn vẫn được báo "Còn bảo hành"
- **Mã và mức độ:** `BUG-01` · **CRITICAL** *(sai lệch nghiệp vụ QT-05)*
- **Phát hiện bởi test case nào:** `TC-07` (`tests/test_business_rules_extended.py::TestWarrantyBoundaryAndMasking::test_warranty_one_day_after_expiration_is_expired`)
- **Triệu chứng:** Với thiết bị mua ngày `2025-03-15`, bảo hành `12` tháng, khi tiếp nhận vào ngày `2026-03-16` (đã quá hạn 1 ngày) hoặc thậm chí `2026-04-14`, hàm `warranty_state()` vẫn trả về `"ok"` (`Còn bảo hành`) thay vì `"expired"` (`Hết bảo hành`).
- **Cách tái lập:** Gọi `warranty_state({"purchase_date": date(2025, 3, 15), "warranty_months": 12, "received_at": datetime(2026, 3, 16, 8, 0, 0)})` hoặc chạy `pytest -v` trước khi sửa; test `test_warranty_one_day_after_expiration_is_expired` báo `AssertionError: assert 'ok' == 'expired'`.
- **Nguyên nhân:** Hàm [`warranty_state`](../src/services/ticket_service.py) tính số tháng chênh lệch nguyên `elapsed = (received.year - purchase.year) * 12 + (received.month - purchase.month)` (chỉ trừ 1 nếu `received.day < purchase.day`) rồi so sánh `elapsed <= months`. Vì phép chia nguyên làm tròn xuống cả tháng dở dang, mọi ngày từ `15/03/2026` đến `14/04/2026` đều có `elapsed == 12 <= 12`, nên bị tính nhầm là còn bảo hành dư gần 1 tháng.
- **Cách sửa:** Thêm hàm tiện ích `_add_months(start_date, months)` trong `BT2/src/services/ticket_service.py` (dùng `calendar.monthrange` để xử lý chính xác cả ngày cuối tháng), tính đúng ngày hết hạn `expiry_date = _add_months(purchase_date, months)`, và so sánh trực tiếp `received_date <= expiry_date`.
- **Link commit và xác nhận:** https://github.com/vuthelong123/CDTN01/commit/e4f6329bd60c4e989c3f8082fb6ec3182639becd · Đã xác nhận lại: `test_warranty_on_exact_expiration_day_is_ok` (`2026-03-15` → `"ok"`) và `test_warranty_one_day_after_expiration_is_expired` (`2026-03-16` → `"expired"`) đều **PASS** trong lần chạy `pytest -v` (`61 passed`).

---

### BUG-02 — Phân công kỹ thuật viên không kiểm tra KTV tồn tại/đang hoạt động và gây `KeyError` trên phiếu mới tạo
- **Mã và mức độ:** `BUG-02` · **MAJOR** *(vi phạm US4-AC3 / FR5 và gây lỗi hỏng dữ liệu trạng thái)*
- **Phát hiện bởi test case nào:** `TC-03`, `TC-09` (`tests/test_business_rules_extended.py::TestAssignTechnician::test_assign_technician_success`, `test_assign_technician_rejects_inactive_or_missing_technician`, `tests/test_integration_db.py::test_real_db_rejects_nonexistent_technician_without_corrupting_ticket`)
- **Triệu chứng:** (1) Khi phân công phiếu mới tạo qua `FakeTicketRepository`, `assign_technician()` bị văng `KeyError: 'technician_id'`; (2) Khi truyền `technician_id = 999` (không tồn tại) hoặc KTV đã ngừng hoạt động trên SQLite/DB, hàm không ném `ValidationError` mà vẫn cập nhật `ticket_status = 'DA_PHAN_CONG'` hoặc văng lỗi ràng buộc khóa ngoại ở DB.
- **Cách tái lập:** Gọi `assign_technician(repo, ticket_id=2, tech_id=999, employee_id=2)` hoặc gửi `POST /admin/assign/2` với `technician_id=999`. Trước khi sửa, `test_real_db_rejects_nonexistent_technician_without_corrupting_ticket` thất bại (`Failed: DID NOT RAISE ValidationError`) và `test_assign_technician_success` văng `KeyError: 'technician_id'`.
- **Nguyên nhân:** Hàm [`assign_technician`](../src/services/ticket_service.py) truy cập trực tiếp `t["technician_id"]` thay vì `t.get("technician_id")` (trong khi `FakeTicketRepository.add_ticket` không tự điền mặc định `technician_id=None`), đồng thời service không gọi repository kiểm tra `tech_id` có tồn tại và đang `is_active = 1` trước khi gọi `repo.assign_technician()`.
- **Cách sửa:** Bổ sung phương thức `find_active_technician(tech_id)` vào [`MySQLTicketRepository`](../src/repositories/ticket_repository.py) và [`FakeTicketRepository`](../tests/conftest.py); sửa `assign_technician()` dùng `t.get("technician_id")` và kiểm tra `isinstance(tech_id, int) and tech_id > 0` kết hợp `repo.find_active_technician(tech_id)`, ném `ValidationError` nếu KTV không tồn tại hoặc ngừng hoạt động; đồng thời bổ sung mặc định `technician_id=None, closed_at=None` trong `FakeTicketRepository.add_ticket`.
- **Link commit và xác nhận:** https://github.com/vuthelong123/CDTN01/commit/0005d08731e3ab0d03afbabc778d0dee1d2be832 · Đã xác nhận lại: toàn bộ test nhóm `TestAssignTechnician`, `IT-02` và `test_assign_nonexistent_technician_via_api_returns_400` đều **PASS** (`61 passed`).

---

### BUG-03 — Lỗ hổng kiểm soát truy cập & xử lý lỗi API (OWASP A01 trả `302` thay vì `401/403`, lộ SĐT trên JSON, bật `debug=True` & lộ raw `{exc}`)
- **Mã và mức độ:** `BUG-03` · **CRITICAL** *(lỗ hổng bảo mật A01 OWASP & lộ cấu trúc lỗi nội bộ)*
- **Phát hiện bởi test case nào:** `TC-01`, `TC-08`, `TC-09`, `TC-10`, `TC-11` (`tests/test_api_routes.py`: `test_unauthenticated_api_request_returns_401`, `test_wrong_role_accessing_admin_assign_returns_403`, `test_technician_cannot_update_another_technicians_ticket`, `test_invalid_phone_on_api_customer_returns_400_and_message`, `test_internal_error_does_not_leak_traceback_or_db_details`)
- **Triệu chứng:**
  1. Khi `kythuatvien2` gửi `POST /technician/update/1` (phiếu của `kythuatvien1`), server trả HTTP `302` redirect thay vì `403 Forbidden`; chưa đăng nhập gọi `/api/customer` trả `302` thay vì `401`.
  2. Gọi `GET /api/customer?phone=123` trả HTTP `200` thay vì `400`.
  3. Các route `reception_routes.py`, `admin_routes.py`, `tech_routes.py` flash nguyên chuỗi `{exc}` ra giao diện khi lỗi hệ thống và `main.py` bật cứng `debug=True`, `host=127.0.0.1` cùng chuỗi secret fallback cố định `"dev-only-change-me"`.
  4. Khi `DB_TYPE=mysql` không kết nối được, `db_connection.py` tự nuốt ngoại lệ và lặng lẽ chuyển sang file SQLite rỗng.
- **Cách tái lập:** Chạy `tests/test_api_routes.py` trước khi sửa; tất cả test kiểm tra HTTP `401`, `403`, `400`, `/health` (`404`) đều `FAILED`.
- **Nguyên nhân:** `login_required` trong `auth_routes.py` chỉ trả `redirect(...)` cho mọi request kể cả `/api/*`; `update_tech_status` gộp chung lỗi không phải chủ sở hữu vào `ValidationError` mặc định; các route bắt `Exception as exc` rồi nội suy thẳng `{exc}` vào `flash()`; `main.py` cấu hình cứng `debug=True` và secret mặc định thay vì đọc biến môi trường.
- **Cách sửa:** Thêm `AuthorizationError` (`status_code=403`) và `NotFoundError` (`status_code=404`) trong `ticket_validator.py`; tạo module `BT2/src/routes/helpers.py` (`wants_json()`, `validation_error_response()`, `internal_error_response()` ghi log server-side và trả thông báo chung an toàn); cập nhật `auth_routes.py`, `reception_routes.py`, `admin_routes.py`, `tech_routes.py` trả đúng mã `401/403/400/404/201/200` và che SĐT (`mask_phone`) trên cả JSON của tiếp nhận/KTV; tắt `debug=True` mặc định, thêm `/health`, bỏ fallback secret tĩnh trong `main.py`, và ngăn fallback ngầm sang SQLite khi `DB_TYPE=mysql` trong `db_connection.py`.
- **Link commit và xác nhận:** https://github.com/vuthelong123/CDTN01/commit/2cd059801ab5343bed2e16c777f8368119c9ecb0 · Đã xác nhận lại: `11/11` test trong `tests/test_api_routes.py` (bao gồm OWASP A01 `401/403`, lỗi `400`, chống lộ `500`, `/health`) đều **PASS** trong lần chạy `pytest -v` (`61 passed`).

