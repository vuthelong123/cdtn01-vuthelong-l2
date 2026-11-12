# Hệ thống Quản lý Yêu cầu Bảo hành — Mekong Mobile (Luồng L2)

- **Môn học:** Chuyên đề tốt nghiệp 01 (CDTN01) — Track SE
- **Sinh viên thực hiện:** Vũ Thế Long — MSSV: `2374802010286`

---

## 1. Lấy mã nguồn từ GitHub (Tag `v1.0`)

Repo để ở chế độ **Public** (không cần đăng nhập GitHub hay cấp quyền). Trên máy bất kỳ có cài sẵn Git và Docker, mở terminal và chạy:

```bash
git clone --branch v1.0 https://github.com/vuthelong123/CDTN01.git kiem-tra
cd kiem-tra
```

---

## 2. Chạy hệ thống bằng 2 lệnh (Docker Compose)

Yêu cầu: **Docker Desktop / Docker Engine** (có plugin `docker compose`) và cổng **`8000`** đang trống.

```bash
cp .env.example .env
docker compose up -d --build
```

Sau khi hai container (`db` MySQL 8.0 và `web` Flask + Gunicorn) khởi động xong (dữ liệu mẫu được nạp tự động từ `BT2/sql/schema.sql` và `BT2/sql/seed.sql`), truy cập ứng dụng tại:

- **Web UI:** http://localhost:8000

---

## Kiểm tra hệ thống & Chạy bộ kiểm thử

```bash
# 1. Kiểm tra trạng thái container (cả db và web phải ở trạng thái healthy)
docker compose ps

# 2. Kiểm tra endpoint sức khỏe hệ thống
curl -s http://localhost:8000/health
# Kỳ vọng: {"database":"ok","status":"ok"}

# 3. Chạy toàn bộ 61 test case (Unit + Integration DB thật + API/Security)
docker compose exec web pytest -v
```

*(Tùy chọn chạy cục bộ không cần Docker: vào `BT2/`, cài `pip install -r requirements.txt`, chạy `pytest -v` và `python src/main.py` để dùng SQLite nhúng trên cổng `5000`.)*

---

## Tài khoản đăng nhập mẫu (Mật khẩu chung: `123456`)

| Vai trò | Tài khoản | Mật khẩu | Chức năng chính |
| :--- | :--- | :---: | :--- |
| Nhân viên tiếp nhận | `nhanvientiepnhan` | `123456` | Tra cứu khách theo SĐT, tạo phiếu (UC01), phân loại (UC02), sửa mô tả, đóng phiếu |
| Quản trị viên | `quantrivien` | `123456` | Tra cứu/lọc phiếu (UC03), phân công KTV (UC04), cập nhật toàn diện phiếu |
| Kỹ thuật viên 1 | `kythuatvien` | `123456` | Xem phiếu được phân công (UC05), cập nhật trạng thái tuyến tính (UC06) |
| Kỹ thuật viên 2 | `kythuatvien2` | `123456` | Kiểm thử cách ly quyền sở hữu giữa các kỹ thuật viên (OWASP A01) |

---

## Cấu trúc thư mục chính

- `docker-compose.yml`, `.env.example`, `.gitignore`: Cấu hình đóng gói 2 container (`web` + `db`) ở gốc repo.
- `BT2/src/`: Mã nguồn Flask 4 tầng (`routes/`, `services/`, `validators/`, `repositories/`).
- `BT2/tests/`: Bộ 61 kiểm thử tự động (`pytest -v`).
- `BT2/sql/`: Lược đồ và dữ liệu mẫu MySQL (`schema.sql`, `seed.sql`).
- `BT2/docs/`: Tài liệu kiểm thử & kỹ thuật BT3 (`test-plan.md`, `test-report.md`, `bug-log.md`, `checklist-bao-mat.md`, `api-docs.md`, `thay-doi-thiet-ke.md`, `ai-disclosure.md`, `srs.md`).
