# BẢNG KHAI BÁO SỬ DỤNG CÔNG CỤ TRÍ TUỆ NHÂN TẠO (AI DISCLOSURE)

- **Học phần:** Chuyên đề tốt nghiệp 01 (CDTN01) - Track SE (Software Engineering)
- **Sinh viên thực hiện:** Vũ Thế Long — MSSV: `2374802010286`
- **Phạm vi cập nhật:** Tổng hợp cả Giai đoạn 2 (BT2) và Giai đoạn 3 (BT3 — Kiểm thử & Đóng gói prototype).

---

## Bảng kê khai chi tiết (Giai đoạn BT2 & BT3)

| Công cụ AI | Dùng vào việc gì | Áp dụng ở tệp hoặc hàm nào | Sinh viên đã kiểm chứng thế nào |
| :--- | :--- | :--- | :--- |
| **Antigravity / ChatGPT** *(BT2)* | Gợi ý cấu trúc tách lớp 4 tầng (`routes`, `services`, `validators`, `repositories`), khung `FakeTicketRepository` in-memory và 29–34 unit test ban đầu. | `BT2/src/` (cấu trúc lớp), `BT2/tests/conftest.py`, `BT2/tests/test_ticket_service.py` | Đọc kiểm từng module đảm bảo tách biệt tầng, đối chiếu từng test case với `srs.md`, tự chạy `pytest -v` trên terminal kiểm chứng tất cả test đều pass. |
| **Antigravity / ChatGPT** *(BT3)* | Gợi ý bổ sung Integration test (`reset_db()`), API/Security test (OWASP A01, tính tái lập) và rà soát phát hiện 3 bug thật (`warranty_state`, `assign_technician`, HTTP status/error handling). | `BT2/tests/test_business_rules_extended.py`, `BT2/tests/db_test_helper.py`, `BT2/tests/test_integration_db.py`, `BT2/tests/test_api_routes.py`, `BT2/src/services/ticket_service.py`, `BT2/src/routes/helpers.py`, `BT2/src/routes/*.py`, `BT2/src/repositories/` | Tự chạy `pytest -v` **trước khi sửa** để chứng kiến 16 test FAIL thật (xác nhận `BUG-01`, `BUG-02`, `BUG-03`), đọc từng dòng sửa và chạy lại `pytest -v` đạt `61 passed`. |
| **Antigravity / ChatGPT** *(BT3)* | Hỗ trợ viết `Dockerfile`, `docker-compose.yml` (2 dịch vụ Flask + MySQL 8.0), `.env.example`, cập nhật `schema.sql`/`seed.sql` và endpoint `/health`. | `docker-compose.yml`, `.env.example`, `BT2/Dockerfile`, `BT2/requirements.txt`, `BT2/src/main.py`, `BT2/sql/schema.sql`, `BT2/sql/seed.sql` | Kiểm tra từng biến môi trường và healthcheck; đối chiếu hash mật khẩu sinh bằng `werkzeug.security.generate_password_hash` thực tế trên Python 3.11. |
| **Antigravity / ChatGPT** *(BT3)* | Hỗ trợ biên soạn cấu trúc và soát lỗi trình bày cho bộ tài liệu BT3 (`test-plan.md`, `test-report.md`, `bug-log.md`, `checklist-bao-mat.md`, `api-docs.md`, `thay-doi-thiet-ke.md`). | `BT2/docs/*.md`, `README.md` | Đối chiếu từng endpoint và ví dụ JSON trong `api-docs.md` bằng script probe chạy thật trên `app.test_client()`; kiểm tra các mục trong `checklist-bao-mat.md` khớp đúng mã nguồn (ghi trung thực `CHƯA LÀM` với phần chưa chạy `pip-audit`). |
| **Không sử dụng AI (Tự làm)** | Thiết kế giao diện HTML/CSS, phân tích nghiệp vụ SRS/ERD, kiểm thử thủ công trên trình duyệt và xác minh triển khai Docker thực tế trên máy. | `BT2/src/templates/`, `BT2/src/static/`, `BT2/docs/srs.md`, `BT2/docs/architecture-thuc-te.drawio` | Trực tiếp thao tác đăng nhập 4 tài khoản mẫu trên trình duyệt và chạy kiểm chứng quy trình tạo–phân công–xử lý–đóng phiếu. |

---

## Cam kết liêm chính học thuật
- Sinh viên hiểu rõ toàn bộ kiến trúc mã nguồn, ý nghĩa từng test case, nguyên nhân gốc của từng bug trong `bug-log.md` và cách hoạt động của cấu hình Docker Compose.
- Toàn bộ kết quả kiểm thử và ví dụ API trong tài liệu đều được thu thập từ lần chạy thực tế trên mã nguồn hiện tại; không có kết quả giả mạo hay tính năng chưa hiện thực được khai khống.
