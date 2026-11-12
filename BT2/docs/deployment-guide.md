# DEPLOYMENT GUIDE — BÀI TẬP 3 (TRACK SE)

- **Hệ thống:** Quản lý Yêu cầu Bảo hành — Mekong Mobile (Luồng L2 - Service Desk)
- **Sinh viên thực hiện:** Vũ Thế Long — MSSV: `2374802010286`
- **Repository & Tag nộp bài:** `https://github.com/vuthelong123/CDTN01` (`v1.0`)

---

## 1. Kiến trúc đóng gói

Hệ thống được đóng gói bằng **Docker Compose** tại tệp [`docker-compose.yml`](../../docker-compose.yml) (thư mục gốc repo), gồm **2 container** tách biệt kết nối qua mạng nội bộ Docker:

1. **Dịch vụ `db` (`mysql:8.0`):**
   - Lưu trữ dữ liệu bền vững bằng Docker volume `mysql_data` (`/var/lib/mysql`).
   - Tự động khởi tạo bảng và dữ liệu mẫu ngay lần dựng đầu tiên thông qua 2 tệp mount read-only:
     - `./BT2/sql/schema.sql` → `/docker-entrypoint-initdb.d/01-schema.sql`
     - `./BT2/sql/seed.sql` → `/docker-entrypoint-initdb.d/02-seed.sql`
   - Healthcheck: `mysqladmin ping` mỗi `5s` (`retries: 20`, `start_period: 15s`). Dịch vụ `web` chỉ khởi động sau khi `db` đạt trạng thái `service_healthy`.

2. **Dịch vụ `web` (`./BT2/Dockerfile` trên nền `python:3.11-slim`):**
   - Cài đặt các thư viện đã ghim phiên bản bằng `==` trong [`BT2/requirements.txt`](../requirements.txt) (`Flask==3.0.3`, `Werkzeug==3.1.3`, `mysql-connector-python==8.4.0`, `gunicorn==23.0.0`, `pytest==9.1.1`, `python-dotenv==1.1.0`).
   - Khởi chạy bằng Gunicorn WSGI server (`gunicorn --bind 0.0.0.0:8000 --workers 2 main:app`), mở cổng `8000` (ánh xạ qua biến `${PORT:-8000}:8000`).
   - Healthcheck: gọi HTTP tới `http://127.0.0.1:8000/health` mỗi `5s` (`retries: 10`).

---

## 2. Yêu cầu môi trường & Biến môi trường

### Phần mềm cần có trên máy triển khai
- **Git** (để clone mã nguồn từ GitHub Public).
- **Docker Desktop** (Windows/macOS) hoặc **Docker Engine + Docker Compose plugin** (`docker compose` v2) trên Linux.
- Cổng **`8000`** đang trống (hoặc đổi biến `PORT` trong `.env`).

### Danh sách biến môi trường (`.env.example`)
Sao chép tệp mẫu [`.env.example`](../../.env.example) ở thư mục gốc thành `.env` trước khi chạy (`.gitignore` đã chặn không đưa `.env` lên Git):

| Biến môi trường | Giá trị mẫu (`.env.example`) | Mô tả |
| :--- | :--- | :--- |
| `MYSQL_ROOT_PASSWORD` | `root_sample_password_change_me` | Mật khẩu tài khoản `root` của container MySQL. |
| `MYSQL_DATABASE` | `warranty_db` | Tên database khởi tạo tự động trên MySQL. |
| `MYSQL_USER` | `warranty_user` | Tên tài khoản ứng dụng kết nối vào `warranty_db`. |
| `MYSQL_PASSWORD` | `warranty_sample_password_change_me` | Mật khẩu cho `MYSQL_USER`. |
| `DB_TYPE` | `mysql` | Loại CSDL sử dụng (`mysql` hoặc `sqlite`). |
| `DB_HOST` | `db` | Tên host dịch vụ MySQL trong mạng Docker Compose. |
| `DB_PORT` | `3306` | Cổng MySQL nội bộ. |
| `DB_NAME` | `warranty_db` | Tên schema/database ứng dụng truy vấn. |
| `DB_USER` | `warranty_user` | Tài khoản đăng nhập DB từ ứng dụng Flask. |
| `DB_PASSWORD` | `warranty_sample_password_change_me` | Mật khẩu đăng nhập DB từ ứng dụng Flask. |
| `FLASK_SECRET` | `sample-dev-secret-change-in-production` | Khóa bí mật ký Flask `session` (nên tạo chuỗi ngẫu nhiên mới khi triển khai công khai). |
| `FLASK_DEBUG` | `false` | Tắt chế độ debug để tránh rò rỉ stack trace (OWASP). |
| `PORT` | `8000` | Cổng public trên máy host ánh xạ vào cổng `8000` của container `web`. |

---

## 3. Hướng dẫn triển khai bằng Docker Compose (2 lệnh)

Áp dụng cho phép thử máy trắng (từ một máy mới chưa từng chạy dự án):

```bash
# Bước 1: Clone đúng phiên bản từ GitHub Public (không cần đăng nhập)
git clone --branch v1.0 https://github.com/vuthelong123/CDTN01.git kiem-tra
cd kiem-tra

# Bước 2: Tạo file .env từ mẫu và khởi dựng hệ thống
# - Linux / macOS / Git Bash / PowerShell:
cp .env.example .env
# - Windows CMD:
# copy .env.example .env

docker compose up -d --build
```

Sau khi lệnh hoàn tất, truy cập ứng dụng tại:
- **Giao diện Web:** `http://localhost:8000`
- **Healthcheck API:** `http://localhost:8000/health`

---

## 4. Xác minh hệ thống & Chạy bộ kiểm thử sau triển khai

```bash
# 1. Kiểm tra cả 2 container (db và web) phải ở trạng thái healthy
docker compose ps

# 2. Kiểm tra endpoint sức khỏe kết nối CSDL thật
curl -s http://localhost:8000/health
# Kỳ vọng: {"database":"ok","status":"ok"}

# 3. Chạy toàn bộ 61 test case (Unit + Integration MySQL thật + API/Security)
docker compose exec web pytest -v
# Kỳ vọng: 61 passed
```

### Tài khoản đăng nhập mẫu (Mật khẩu chung: `123456`)
| Vai trò | Tên đăng nhập | Chức năng chính |
| :--- | :--- | :--- |
| Nhân viên tiếp nhận (`TIEP_NHAN`) | `nhanvientiepnhan` | Tra cứu SĐT, tạo phiếu (UC01), phân loại (UC02), sửa mô tả, đóng phiếu (UC07) |
| Quản trị viên (`QUAN_TRI`) | `quantrivien` | Dashboard lọc phiếu (UC03), phân công KTV (UC04), cập nhật toàn diện phiếu |
| Kỹ thuật viên 1 (`KY_THUAT`) | `kythuatvien` | Xem phiếu được gán (UC05), cập nhật trạng thái tuyến tính (UC06) |
| Kỹ thuật viên 2 (`KY_THUAT`) | `kythuatvien2` | Kiểm thử cô lập quyền sở hữu giữa các KTV (OWASP A01) |

---

## 5. Vận hành, Dừng & Khôi phục dữ liệu mẫu

- **Xem log container theo thời gian thực:**
  ```bash
  docker compose logs -f web
  docker compose logs -f db
  ```
- **Dừng hệ thống nhưng giữ lại dữ liệu đã nhập trong DB:**
  ```bash
  docker compose down
  ```
- **Dừng hệ thống và xóa sạch volume DB để nạp lại dữ liệu mẫu ban đầu (`schema.sql` + `seed.sql`):**
  ```bash
  docker compose down -v
  docker compose up -d
  ```

---

## 6. Tùy chọn triển khai khác

### 6.1. Chạy cục bộ không cần Docker (Python + SQLite nhúng)
Phù hợp để chạy Unit Test và thử nhanh giao diện mà không cần cài MySQL:
```bash
cd BT2
pip install -r requirements.txt
pytest -v
python src/main.py
```
Ứng dụng tự khởi tạo tệp `BT2/warranty.db` (SQLite) kèm dữ liệu mẫu và chạy tại `http://127.0.0.1:5000`.

### 6.2. Triển khai bản thử nghiệm lên Render (1 dịch vụ Web)
- **Root Directory:** `BT2`
- **Runtime `Python 3` (khuyên dùng với SQLite nhúng):**
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `gunicorn --chdir src --bind 0.0.0.0:$PORT --workers 1 main:app`
  - Environment Variables: `DB_TYPE=sqlite`, `FLASK_DEBUG=false`, `FLASK_SECRET=<chuỗi bí mật ngẫu nhiên sinh mới>`, Health Check Path: `/health`.
- **Runtime `Docker` (nếu nối tới MySQL Cloud như Aiven / TiDB):** giữ `Root Directory=BT2`, `Dockerfile Path=./Dockerfile`, đặt `PORT=8000`, `DB_TYPE=mysql` và điền đầy đủ `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `FLASK_SECRET`, `FLASK_DEBUG=false`.
