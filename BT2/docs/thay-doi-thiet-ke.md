# BẢN GHI NHẬN THAY ĐỔI THIẾT KẾ (BT1 → BT2)

- **Học phần:** Chuyên đề tốt nghiệp 01 (CDTN01) - Track SE (Software Engineering)
- **Đề tài:** Hệ thống quản lý yêu cầu bảo hành (Luồng L2 - Service Desk)
- **Sinh viên thực hiện:** Vũ Thế Long - MSSV: 2374802010286

## 1. Lý do và Mục tiêu thay đổi
Trong Bài tập 1 (BT1), hệ thống đã xây dựng tài liệu đặc tả yêu cầu (SRS), mô hình cơ sở dữ liệu (ERD) và các bản vẽ thiết kế Use Case. Tuy nhiên, khi chuyển sang giai đoạn hiện thực mã nguồn và phát triển kiểm thử tự động ở Bài tập 2 (BT2), một số thiết kế ban đầu bộc lộ hạn chế cần được tái cấu trúc:
1. **Thiếu khả năng kiểm thử độc lập:** Logic nghiệp vụ ban đầu bị gắn chặt vào Framework giao diện (Flask routes) và truy vấn trực tiếp cơ sở dữ liệu MySQL, khiến việc viết Unit Test bắt buộc phải kết nối CSDL thật, dễ gây sai lệch dữ liệu và chạy chậm.
2. **Cơ chế xác thực chưa được mô hình hóa trong CSDL:** Bảng `employee` ở BT1 chỉ có thông tin định danh và vai trò, chưa có tài khoản và mật khẩu bảo mật.
3. **Quy tắc chuyển trạng thái cần làm chặt chẽ hơn:** Đảm bảo kỹ thuật viên tuân thủ nghiêm ngặt tiến trình xử lý sự cố từng bước một.

## 2. Bảng tổng hợp các thay đổi chính

| Thành phần | Thiết kế ở BT1 | Hiện thực thực tế ở BT2 | Lý do thay đổi & Lợi ích |
| :--- | :--- | :--- | :--- |
| **Kiến trúc mã nguồn** | Các route Flask vừa nhận request, vừa kiểm tra validation, vừa gọi SQL trực tiếp. | **Tách lớp 4 tầng chuẩn SE:**<br>- `routes/` (Presentation)<br>- `services/` (Business Logic)<br>- `validators/` (Validation)<br>- `repositories/` (Data Access) | Tách biệt trách nhiệm (SoC), mã nguồn module hóa, cho phép kiểm thử nghiệp vụ độc lập mà không cần khởi động server web. |
| **Kiểm thử tự động** | Chưa có kiểm thử tự động. | **Bộ Unit Test với Pytest:**<br>- Sử dụng `FakeTicketRepository` (in-memory)<br>- Bao phủ 3 nhóm: Happy path, Boundary (FR2), Invalid input. | Đảm bảo chất lượng mã nguồn, chạy 29/29 test pass chỉ trong ~0.05s mà không cần đụng đến database MySQL production. |
| **Bảng dữ liệu `employee`** | Chỉ gồm `employee_id`, `full_name`, `role`, `phone`, `is_active`. | **Bổ sung:**<br>- `username VARCHAR(50) UNIQUE`<br>- `password_hash VARCHAR(255)` | Hiện thực chức năng đăng nhập, phân quyền 3 vai trò theo SRS và bảo mật mật khẩu bằng thuật toán băm (Werkzeug hash). |
| **Luồng trạng thái KTV (QT-06)** | Cho phép chọn giữa các trạng thái kế tiếp trong danh sách. | **Khóa chặt tiến trình tuyến tính:**<br>`Đã phân công` → `Đang xử lý` → `Chờ linh kiện` → `Hoàn tất`. | Ngăn chặn kỹ thuật viên nhảy cóc trạng thái hoặc thao tác sai quy trình xử lý kỹ thuật. |
| **Giao diện hiển thị trạng thái** | Sử dụng badge trạng thái đơn lẻ. | **Thanh tiến trình (Stepper) 6 bước trực quan:**<br>`Mới` → `Đã phân công` → `Đang xử lý` → `Chờ linh kiện` → `Hoàn tất` → `Đã đóng`. | Giúp cả 3 vai trò (Tiếp nhận, Quản trị, Kỹ thuật) quan sát trực quan vị trí hiện tại của phiếu trong vòng đời SLA. |

## 3. Tác động tới tài liệu và mã nguồn
Bản vẽ kiến trúc thực tế được ghi nhận tại [architecture-thuc-te.drawio](file:///c:/CDTN01/BT2/docs/architecture-thuc-te.drawio).
Toàn bộ các yêu cầu chức năng (FR1 – FR8) và quy tắc nghiệp vụ (QT-01 – QT-06, QT-15) trong [srs.md](file:///c:/CDTN01/BT2/docs/srs.md) đều được đảm bảo vẹn toàn và phản ánh chính xác trong mã nguồn mới.

---

# BẢN GHI NHẬN THAY ĐỔI THIẾT KẾ (BT2 → BT3)

## 1. Mục tiêu thay đổi ở giai đoạn Bài tập 3
Chuyển hệ thống từ mức chạy cục bộ thủ công (`run.bat` + SQLite fallback) sang **prototype đóng gói chuẩn Docker Compose 2 container** (Flask + MySQL 8.0), bổ sung kiểm thử đa tầng (Unit + Integration với DB thật + API/Security), khắc phục các lỗi logic và lỗ hổng bảo mật phát hiện trong quá trình kiểm thử.

## 2. Bảng tổng hợp các thay đổi chính (BT2 → BT3)

| Thành phần | Hiện thực ở BT2 | Hiện thực cập nhật ở BT3 | Lý do thay đổi & Lợi ích |
| :--- | :--- | :--- | :--- |
| **Đóng gói & Khởi chạy** | Chạy trực tiếp bằng `run.bat` / `python src/main.py` trên máy host (bind `127.0.0.1:5000`, `debug=True`). | **Docker Compose 2 dịch vụ** ở gốc repo (`docker-compose.yml` + `BT2/Dockerfile` + Gunicorn cổng `8000`) kèm MySQL `8.0` tự nạp `schema.sql` + `seed.sql` và healthcheck `/health`. | Đáp ứng phép thử máy trắng `<= 2 lệnh` trên môi trường sạch; tách riêng tầng ứng dụng và CSDL, tắt `debug=True` mặc định. |
| **Lược đồ SQL (`sql/schema.sql`, `seed.sql`)** | `schema.sql` chưa có cột `username`, `password_hash`; phải chạy rời `init_auth.py`. | Đồng bộ `username`, `password_hash` vào `schema.sql` và hash mật khẩu mẫu (`scrypt`) vào `seed.sql`. | Container MySQL 8.0 tự động sẵn sàng đầy đủ tài khoản đăng nhập ngay khi khởi động lần đầu. |
| **Tính bảo hành (`warranty_state`)** | Tính theo chênh lệch tháng nguyên `elapsed <= months`, làm thiết bị quá hạn vài ngày đến gần 1 tháng vẫn báo `ok`. | Tính ngày hết hạn theo lịch chính xác (`_add_months(purchase_date, months)`) và so sánh `received_date <= expiry_date`. | Sửa lỗi `BUG-01` (QT-05), đảm bảo đúng ranh giới ngày cuối bảo hành (`ok`) và ngày đầu tiên hết hạn (`expired`). |
| **Phân công KTV (`assign_technician`)** | Không kiểm tra `technician_id` tồn tại / đang hoạt động (`is_active`) và truy cập `t["technician_id"]` dễ gây `KeyError`. | Bổ sung `find_active_technician(tech_id)` trong Repository và kiểm tra bắt buộc trước khi gán. | Đáp ứng `US4-AC3`, sửa lỗi `BUG-02`, ngăn gán KTV không tồn tại/đã nghỉ. |
| **Chuẩn hóa phản hồi API & Bảo mật** | Mọi route ngoài `/api/customer` đều trả `302` redirect HTML, lộ `{exc}` ra flash, JSON tiếp nhận/KTV chưa che SĐT, fallback ngầm sang SQLite kể cả khi đặt `DB_TYPE=mysql`. | Tách `AuthorizationError` (`403`) và `NotFoundError` (`404`), thêm `routes/helpers.py` hỗ trợ JSON + mã HTTP `200/201/400/401/403/404/500` an toàn, che SĐT trên JSON tiếp nhận/KTV, bỏ fallback secret tĩnh và fail-fast khi `DB_TYPE=mysql` lỗi. | Sửa `BUG-03`, đảm bảo kiểm soát truy cập theo chủ sở hữu (OWASP A01), không lộ lỗi nội bộ và kiểm thử API tự động chính xác. |
| **Bộ kiểm thử (`tests/`)** | 34 Unit test trên `FakeTicketRepository` (trong tài liệu cũ vẫn ghi 29). | **61 test case** (47 Unit + 3 Integration DB thật + 11 API/Security/Reproducibility) có hàm `reset_db()`. | Bao phủ 100% quy tắc nghiệp vụ đã hiện thực trên cả logic, DB thật và giao diện HTTP/API. |
