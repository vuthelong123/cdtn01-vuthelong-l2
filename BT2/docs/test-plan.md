# TEST PLAN RÚT GỌN — BÀI TẬP 3 (TRACK SE)

- **Hệ thống:** Quản lý Yêu cầu Bảo hành — Mekong Mobile (Luồng L2 - Service Desk)
- **Sinh viên thực hiện:** Vũ Thế Long — MSSV: `2374802010286`
- **Phạm vi tài liệu:** Kế hoạch kiểm thử cho toàn bộ prototype đóng gói ở Bài tập 3.

---

## 1. Phạm vi kiểm thử và phần chủ ý KHÔNG kiểm

### Phần ĐƯỢC kiểm thử
Kiểm thử đầy đủ các luồng nghiệp vụ cốt lõi và quy tắc đã hiện thực trong `BT2/src/`:
1. **Xác thực & phân quyền (Authentication / OWASP A01):** Đăng nhập, phân quyền theo vai trò (`TIEP_NHAN`, `QUAN_TRI`, `KY_THUAT`), kiểm tra quyền sở hữu khi kỹ thuật viên cập nhật phiếu (`update_tech_status`), che số điện thoại cho vai trò không phải quản trị (`QT-15`).
2. **Tiếp nhận & tạo phiếu (`UC01` / `FR1`, `FR2`, `QT-01`–`QT-05`):** Chuẩn hóa SĐT 10 số, tái sử dụng khách hàng/thiết bị, kiểm tra trùng serial giữa hai khách khác nhau + rollback giao dịch, độ dài tối thiểu mô tả lỗi (`10` ký tự), tự tính hạn cam kết SLA bỏ qua Chủ Nhật, xác định tình trạng bảo hành (`ok` / `expired` / `unverified`).
3. **Phân loại, chỉnh sửa & tra cứu phiếu (`UC02`, `UC03` / `FR3`, `FR4`):** Phân loại nhóm sự cố & mức ưu tiên, cập nhật mô tả khi phiếu chưa đóng, tra cứu theo mã phiếu & trạng thái.
4. **Phân công, xử lý tuyến tính & đóng phiếu (`UC04`–`UC07` / `FR5`–`FR8`, `QT-06`):** Gán tối đa 1 KTV đang hoạt động, chuyển trạng thái tuyến tính của KTV kèm ghi `ticket_status_log`, đóng phiếu khi đã `HOAN_TAT`, kiểm tra endpoint `/health`.

### Phần chủ ý KHÔNG kiểm thử (kèm lý do)
1. **Giao diện CSS / bố cục trình duyệt (Glassmorphism Dark Mode, responsive breakpoint, font chữ):** Không dùng kiểm thử tự động giao diện (Selenium/Playwright) vì CSS thuần trình bày trực quan, không chứa quy tắc nghiệp vụ hay ràng buộc dữ liệu.
2. **Các luồng ngoài phạm vi Luồng L2 đã nêu trong SRS (`srs.md` mục 1.1):** Lịch hẹn kỹ thuật viên, quản lý kho linh kiện, thanh toán, bán hàng/cơ hội bán hàng — các chức năng này chưa hiện thực trong prototype.
3. **Kiểm thử tải / hiệu năng quy mô lớn (stress test):** Chỉ kiểm tra chức năng với bộ dữ liệu mẫu và độ ổn định CRUD; kiểm thử tải nhiều nghìn request đồng thời nằm ngoài phạm vi đơn vị bài tập prototype.

---

## 2. Loại test và số lượng mỗi tầng

Tổng bộ kiểm thử tự động gồm **61 test case** chạy qua một lệnh `pytest -v`, chia thành 3 tầng:

| Tầng kiểm thử | Tệp kiểm thử | Số lượng | Mục tiêu kiểm chứng |
| :--- | :--- | :---: | :--- |
| **Unit Test** (Service & Validator, `FakeTicketRepository` in-memory) | `BT2/tests/test_ticket_service.py`<br>`BT2/tests/test_business_rules_extended.py` | **47** | Kiểm tra độc lập toàn bộ hàm nghiệp vụ (`create_ticket`, `classify_ticket`, `assign_technician`, `update_tech_status`, `update_ticket_description`, `admin_update_ticket`, `close_ticket`, `warranty_state`, `normalize_phone`, `mask_phone`). |
| **Integration Test** (Repository + DB thật) | `BT2/tests/test_integration_db.py` | **3** | Kiểm tra `MySQLTicketRepository` lưu/truy vấn/rollback transaction và ghi lịch sử `ticket_status_log` trên cơ sở dữ liệu thật (MySQL 8.0 trong Docker hoặc SQLite test DB). |
| **API / Route & Security Test** (Flask `test_client()` + DB thật) | `BT2/tests/test_api_routes.py` | **11** | Kiểm tra `/health`, luồng E2E qua HTTP route, dữ liệu sai (HTTP status code + message), phân quyền OWASP A01 (`401`/`403`), chống lộ lỗi nội bộ (`500` an toàn), và tính tái lập. |
| **Tổng cộng** | | **61** | **Chọn lọc 12 test case tiêu biểu chạy thật đưa vào bảng `test-report.md`.** |

---

## 3. Tiêu chí thành công ĐO ĐƯỢC

Kiểm thử được coi là **ĐẠT** khi thỏa mãn đồng thời 5 chỉ số định lượng sau:
1. **100% (61/61)** test case trong bộ kiểm thử tự động (`pytest -v`) đạt trạng thái `PASS`, và **12/12** test case trong `test-report.md` đạt `PASS` sau khi sửa bug.
2. **100% quy tắc nghiệp vụ đã hiện thực** (`FR1`–`FR8`, `QT-01`–`QT-06`, `QT-15`) có ít nhất **1 test case** luồng đúng và bao phủ các điểm biên trọng yếu (`FR2` độ dài `9/10` ký tự; `QT-05` ngày hết hạn bảo hành `ok/expired`).
3. **100% nhóm kiểm thử bắt buộc có test thực thi:** tối thiểu 2 test biên 2 phía, 2 test dữ liệu sai kiểm tra cả HTTP status code và thông báo lỗi, 1 test bảo mật chủ sở hữu (OWASP A01), và 1 test tính tái lập.
4. **0 bug mức `CRITICAL`** và **0 bug mức `MAJOR`** còn mở (`BUG-01`, `BUG-02`, `BUG-03` đều đã sửa và xác nhận lại).
5. **0 mất mát dữ liệu / sập server (`500` không kiểm soát)** khi thử dữ liệu sai hoặc khi giao dịch bị lỗi giữa chừng.

---

## 4. Môi trường và dữ liệu thử

- **Môi trường chạy kiểm thử:**
  - **Trong Docker Compose (chuẩn BT3):** Container `web` (`python:3.11-slim` + Flask `3.0.3` + `gunicorn 23.0.0`) kết nối trực tiếp tới container `db` (`mysql:8.0`) qua biến môi trường `DB_TYPE=mysql`, `DB_HOST=db`. Lệnh chạy: `docker compose exec web pytest -v`.
  - **Cục bộ Windows (khi phát triển/Unit + SQLite test DB):** Python `3.11.5`, `pytest 9.1.1`; Integration/API test tự động dùng tệp SQLite tạm (`cdtn01_test_warranty.db` trong thư mục tạm hệ thống) để không làm hỏng dữ liệu làm việc. Lệnh chạy tại `BT2/`: `pytest -v`.
- **Nguồn dữ liệu thử và cơ chế dựng / dọn sạch (`reset_db()`):**
  - Dữ liệu nền gốc được định nghĩa trong `BT2/sql/schema.sql` và `BT2/sql/seed.sql` (gồm 4 nhân viên với 3 vai trò, 2 kỹ thuật viên đang hoạt động, 3 khách hàng, 3 thiết bị, 3 phiếu mẫu `BH-0001`..`BH-0003`, 9 bản ghi `ticket_status_log`).
  - Trước và sau mỗi Integration / API test, fixture `clean_database` gọi hàm `reset_db()` trong `BT2/tests/db_test_helper.py` để xóa sạch toàn bộ bảng (`TRUNCATE TABLE` với `FOREIGN_KEY_CHECKS = 0` trên MySQL hoặc tạo mới SQLite test DB) và nạp lại đúng tập fixture mẫu ban đầu, đảm bảo mọi test độc lập, lặp lại được và giữ nguyên dữ liệu mẫu sau khi chạy xong bộ test.

