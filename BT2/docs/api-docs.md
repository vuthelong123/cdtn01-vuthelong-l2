# API Documentation — Mekong Mobile Warranty Management (L2 Service Desk)

- **Base URL (Docker Compose):** `http://localhost:8000`
- **Base URL (Local Dev):** `http://127.0.0.1:5000`
- **Content Negotiation:** Web browser forms use standard `application/x-www-form-urlencoded` and Post-Redirect-Get (`302` + flash messages). API clients sending `Accept: application/json` or `Content-Type: application/json` (and `/api/*`, `/health`) receive JSON responses with semantic HTTP status codes (`200`, `201`, `400`, `401`, `403`, `404`, `500`, `503`).
- **Authentication:** Cookie-based Flask session (`session` cookie obtained via `POST /login`).

---

## 1. `GET /health`
- **Method & Path:** `GET /health`
- **Business Description:** Checks application availability and executes a lightweight `SELECT 1` query against the active database (MySQL or SQLite). Used by Docker Compose healthchecks and deployment verification.
- **Authentication:** Public (no login required).
- **Parameters & Request Body:** None.
- **Success Response (`200 OK`):** JSON object `{"status": "ok", "database": "ok"}`.
- **Error Codes:**
  | Status | Condition | Body |
  | :---: | :--- | :--- |
  | `503` | Database unreachable or query failed | `{"status": "error", "database": "unavailable"}` |
- **Notes & Limits:** Does not expose DB host, credentials, or internal stack traces on failure.
- **Real Request & Response Example:**
  ```http
  GET /health HTTP/1.1
  Host: localhost:8000
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "database": "ok",
    "status": "ok"
  }
  ```

---

## 2. `GET /`
- **Method & Path:** `GET /`
- **Business Description:** Entry route redirecting unauthenticated users to `/login` or authenticated users to their role home page (`/reception`, `/admin`, or `/technician`).
- **Authentication:** Optional session cookie.
- **Parameters & Request Body:** None.
- **Success Response (`302 Found`):** Redirect `Location` header pointing to `/login`, `/reception`, `/admin`, or `/technician`.
- **Error Codes:** None (always redirects).
- **Notes & Limits:** HTML/browser entry route only; no JSON body.
- **Real Request & Response Example:**
  ```http
  GET / HTTP/1.1
  Host: localhost:8000
  ```
  ```http
  HTTP/1.1 302 FOUND
  Location: /login
  ```
  *(When authenticated as `TIEP_NHAN`: `HTTP/1.1 302 FOUND`, `Location: /reception`.)*

---

## 3. `GET /login`
- **Method & Path:** `GET /login`
- **Business Description:** Renders the HTML login page (`login.html`).
- **Authentication:** Public.
- **Parameters & Request Body:** None.
- **Success Response (`200 OK`):** `text/html` login page.
- **Error Codes:** None.
- **Notes & Limits:** Browser UI endpoint.
- **Real Request & Response Example:**
  ```http
  GET /login HTTP/1.1
  Host: localhost:8000
  ```
  ```http
  HTTP/1.1 200 OK
  Content-Type: text/html; charset=utf-8
  ```

---

## 4. `POST /login`
- **Method & Path:** `POST /login`
- **Business Description:** Authenticates an employee using `username` and `password` (verified via Werkzeug `check_password_hash`), initializes Flask session (`employee_id`, `full_name`, `role`, and `technician_id` for `KY_THUAT`).
- **Authentication:** Public.
- **Parameters & Request Body:** JSON or form fields:
  - `username` (`string`, required)
  - `password` (`string`, required)
- **Success Response:**
  - JSON (`200 OK`): `{"employee_id": int, "full_name": string, "role": string}`
  - HTML form (`302 Found`): Redirect to role home (`/reception`, `/admin`, or `/technician`) + `Set-Cookie: session=...`.
- **Error Codes:**
  | Status | Condition | Body (JSON) |
  | :---: | :--- | :--- |
  | `401` | Invalid username or wrong password | `{"error": "Sai tên đăng nhập hoặc mật khẩu."}` |
  | `403` | Inactive account or technician record missing | `{"error": "Tài khoản đã bị ngừng hoạt động."}` / `{"error": "Tài khoản chưa được cấu hình là kỹ thuật viên."}` |
- **Notes & Limits:** Passwords are stored hashed (`scrypt`); plain text passwords are never logged or returned.
- **Real Request & Response Example:**
  ```http
  POST /login HTTP/1.1
  Content-Type: application/json
  Accept: application/json

  {"username": "nhanvientiepnhan", "password": "123456"}
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "employee_id": 1,
    "full_name": "Nguyen Thi Lan",
    "role": "TIEP_NHAN"
  }
  ```

---

## 5. `GET /logout`
- **Method & Path:** `GET /logout`
- **Business Description:** Clears the current user session and logs the employee out.
- **Authentication:** Session cookie (safe to call even if already logged out).
- **Parameters & Request Body:** None.
- **Success Response:**
  - JSON (`200 OK` when `Accept: application/json`): `{"message": "Đã đăng xuất."}`
  - HTML (`302 Found`): Redirect to `/login`.
- **Error Codes:** None.
- **Notes & Limits:** Clears all keys in Flask `session`.
- **Real Request & Response Example:**
  ```http
  GET /logout HTTP/1.1
  Accept: application/json
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "message": "Đã đăng xuất."
  }
  ```

---

## 6. `GET /reception`
- **Method & Path:** `GET /reception`
- **Business Description:** Lists recent warranty tickets (up to `50` newest records) with computed warranty status (`ok`, `expired`, `unverified`) and masked customer phone numbers (`QT-15`).
- **Authentication:** Required (`role = TIEP_NHAN`).
- **Parameters & Request Body:** None.
- **Success Response (`200 OK`):** HTML view (`reception.html`) or JSON `{"tickets": [...]}` when `Accept: application/json`.
- **Error Codes:**
  | Status | Condition | Body (JSON) |
  | :---: | :--- | :--- |
  | `401` | Not logged in | `{"error": "Chưa đăng nhập."}` |
  | `403` | Logged in with role other than `TIEP_NHAN` | `{"error": "Bạn không có quyền truy cập chức năng này."}` |
- **Notes & Limits:** Fixed query limit of `50` most recent tickets; `customer_phone` is masked as `091****678`.
- **Real Request & Response Example:**
  ```http
  GET /reception HTTP/1.1
  Accept: application/json
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "tickets": [
      {
        "closed_at": null,
        "customer_id": 2,
        "customer_name": "Nguyen Van An",
        "customer_phone": "091****678",
        "device_id": 2,
        "due_date": "Wed, 28 Oct 2026 10:30:00 GMT",
        "issue_category": "PIN",
        "issue_desc": "Pin tut nhanh, may nong khi sac",
        "model_name": "Mekong Phone X2",
        "priority": "TRUNG_BINH",
        "purchase_date": "Fri, 10 Jan 2025 00:00:00 GMT",
        "received_at": "Sun, 25 Oct 2026 10:30:00 GMT",
        "received_by_employee_id": 1,
        "serial_no": "IMEI350000000000002",
        "tech_name": null,
        "technician_id": null,
        "ticket_code": "BH-0002",
        "ticket_id": 2,
        "ticket_status": "MOI",
        "warranty": "expired",
        "warranty_months": 12
      }
    ]
  }
  ```

---

## 7. `GET /api/customer`
- **Method & Path:** `GET /api/customer`
- **Business Description:** Looks up an existing customer by phone number (`QT-02` normalization to `0xxxxxxxxx`) and returns their registered devices for auto-filling the reception form (`US1-AC1`).
- **Authentication:** Required (`role = TIEP_NHAN`).
- **Parameters & Request Body:** Query parameter `phone` (`string`, required — accepts `0...`, `84...`, `+84...` with spaces/dots).
- **Success Response (`200 OK`):** JSON with `valid=true`, `found` (`true`/`false`), normalized `phone`, and `full_name` + `devices[]` when found.
- **Error Codes:**
  | Status | Condition | Body |
  | :---: | :--- | :--- |
  | `400` | Missing or invalid phone format | `{"error": "Số điện thoại không hợp lệ.", "valid": false}` |
  | `401` | Not logged in | `{"error": "Chưa đăng nhập."}` |
  | `403` | Role is not `TIEP_NHAN` | `{"error": "Bạn không có quyền truy cập chức năng này."}` |
- **Notes & Limits:** Deterministic/idempotent read endpoint; always normalizes to 10-digit `0\d{9}`.
- **Real Request & Response Example:**
  ```http
  GET /api/customer?phone=0843310647 HTTP/1.1
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "devices": [
      {
        "model_name": "Mekong Phone X1",
        "purchase_date": "2026-03-15",
        "serial_no": "IMEI350000000000001",
        "warranty_months": 12
      }
    ],
    "found": true,
    "full_name": "Vu The Long",
    "phone": "0843310647",
    "valid": true
  }
  ```

---

## 8. `POST /reception/create`
- **Method & Path:** `POST /reception/create`
- **Business Description:** Creates a new warranty ticket (`UC01`), reuses or creates customer (`QT-01`) and device (`QT-03`), computes SLA due date skipping Sundays (`QT-04`), initializes status `MOI` and writes `ticket_status_log` (`QT-06`).
- **Authentication:** Required (`role = TIEP_NHAN`).
- **Parameters & Request Body:** JSON or form body:
  - `phone` (`string`, required, valid 10-digit VN phone)
  - `full_name` (`string`, required for new customers)
  - `serial_no` (`string`, required, unique per device/customer)
  - `model_name` (`string`, required for new devices)
  - `purchase_date` (`YYYY-MM-DD`, optional)
  - `warranty_months` (`integer`, optional)
  - `issue_category` (`MAN_HINH` | `PIN` | `SAC` | `PHAN_MEM` | `NUOC_VAO` | `KHAC`, required)
  - `priority` (`CAO` | `TRUNG_BINH` | `THAP`, required)
  - `issue_desc` (`string`, required, minimum `10` non-whitespace characters per `FR2`)
- **Success Response:**
  - JSON (`201 Created`): `{"ticket_id", "ticket_code", "ticket_status": "MOI", "due_date"}`
  - HTML (`302 Found`): Redirect to `/reception` with flash message.
- **Error Codes:**
  | Status | Condition | Body (JSON) |
  | :---: | :--- | :--- |
  | `400` | Validation failure (`issue_desc < 10`, missing required field, invalid enum, serial owned by another customer) | `{"error": "...", "fields": [...]}` |
  | `401` | Not logged in | `{"error": "Chưa đăng nhập."}` |
  | `403` | Role is not `TIEP_NHAN` | `{"error": "Bạn không có quyền truy cập chức năng này."}` |
  | `500` | Unexpected DB failure (transaction rolled back) | `{"error": "Đã xảy ra lỗi hệ thống, vui lòng thử lại sau."}` |
- **Notes & Limits:** Atomic transaction; rolls back customer/device if serial ownership fails or DB fails mid-write.
- **Real Request & Response Example:**
  ```http
  POST /reception/create HTTP/1.1
  Content-Type: application/json
  Accept: application/json

  {
    "phone": "0966555444",
    "full_name": "Pham Minh Duc",
    "serial_no": "IMEI357777777777001",
    "model_name": "Mekong Phone S2",
    "purchase_date": "2026-06-01",
    "warranty_months": 12,
    "issue_category": "PIN",
    "priority": "CAO",
    "issue_desc": "Pin sac khong vao dien, may tu tat nguon"
  }
  ```
  ```json
  HTTP/1.1 201 Created
  Content-Type: application/json

  {
    "due_date": "2026-11-13T01:53:05",
    "ticket_code": "BH-0004",
    "ticket_id": 4,
    "ticket_status": "MOI"
  }
  ```

---

## 9. `POST /reception/classify/<int:ticket_id>`
- **Method & Path:** `POST /reception/classify/<int:ticket_id>`
- **Business Description:** Reclassifies a ticket's `issue_category` and `priority` (`UC02` / `FR3`) and recalculates `due_date` from `received_at`.
- **Authentication:** Required (`role = TIEP_NHAN`).
- **Parameters & Request Body:** Path param `ticket_id` (`int`); Body fields `issue_category` and `priority`.
- **Success Response (`200 OK` JSON / `302` HTML):** `{"ticket_code", "issue_category", "priority"}`.
- **Error Codes:**
  | Status | Condition | Body (JSON) |
  | :---: | :--- | :--- |
  | `400` | Invalid category/priority or ticket already `HOAN_TAT`/`DA_DONG` | `{"error": "...", "fields": []}` |
  | `401` | Not logged in | `{"error": "Chưa đăng nhập."}` |
  | `403` | Wrong role | `{"error": "Bạn không có quyền truy cập chức năng này."}` |
  | `404` | Ticket ID does not exist | `{"error": "Không tìm thấy phiếu.", "fields": []}` |
- **Notes & Limits:** Tickets in `HOAN_TAT` or `DA_DONG` cannot be reclassified.
- **Real Request & Response Example:**
  ```http
  POST /reception/classify/4 HTTP/1.1
  Content-Type: application/json
  Accept: application/json

  {"issue_category": "SAC", "priority": "TRUNG_BINH"}
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "issue_category": "SAC",
    "priority": "TRUNG_BINH",
    "ticket_code": "BH-0004"
  }
  ```

---

## 10. `POST /reception/edit-desc/<int:ticket_id>`
- **Method & Path:** `POST /reception/edit-desc/<int:ticket_id>`
- **Business Description:** Updates `issue_desc` of an existing open ticket (`FR2` min 10 chars enforced).
- **Authentication:** Required (`role = TIEP_NHAN`).
- **Parameters & Request Body:** Path param `ticket_id` (`int`); Body field `issue_desc` (`string`, min 10 chars).
- **Success Response (`200 OK` JSON / `302` HTML):** `{"ticket_code", "message": "Đã cập nhật mô tả."}`.
- **Error Codes:**
  | Status | Condition | Body (JSON) |
  | :---: | :--- | :--- |
  | `400` | Description `< 10` characters or ticket is `DA_DONG` | `{"error": "...", "fields": [...]}` |
  | `401` / `403` | Unauthenticated or wrong role | `{"error": "..."}` |
  | `404` | Ticket not found | `{"error": "Không tìm thấy phiếu.", "fields": []}` |
- **Notes & Limits:** Rejected once ticket status is `DA_DONG`.
- **Real Request & Response Example:**
  ```http
  POST /reception/edit-desc/4 HTTP/1.1
  Content-Type: application/json
  Accept: application/json

  {"issue_desc": "Cong sac Type-C bi long, khong nhan sac nhanh"}
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "message": "Đã cập nhật mô tả.",
    "ticket_code": "BH-0004"
  }
  ```

---

## 11. `POST /reception/close/<int:ticket_id>`
- **Method & Path:** `POST /reception/close/<int:ticket_id>`
- **Business Description:** Closes a completed ticket (`HOAN_TAT` → `DA_DONG`), sets `closed_at`, and appends a status log entry.
- **Authentication:** Required (`role = TIEP_NHAN`).
- **Parameters & Request Body:** Path param `ticket_id` (`int`). No body fields required.
- **Success Response (`200 OK` JSON / `302` HTML):** `{"ticket_code", "ticket_status": "DA_DONG"}`.
- **Error Codes:**
  | Status | Condition | Body (JSON) |
  | :---: | :--- | :--- |
  | `400` | Ticket status is not `HOAN_TAT` | `{"error": "Chỉ đóng được phiếu ở trạng thái Hoàn tất.", "fields": []}` |
  | `401` / `403` | Unauthenticated or wrong role | `{"error": "..."}` |
  | `404` | Ticket not found | `{"error": "Không tìm thấy phiếu.", "fields": []}` |
- **Notes & Limits:** Enforces `HOAN_TAT` prerequisite; administrators can also close via `/admin/update/<ticket_id>`.
- **Real Request & Response Example:**
  ```http
  POST /reception/close/4 HTTP/1.1
  Accept: application/json
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "ticket_code": "BH-0004",
    "ticket_status": "DA_DONG"
  }
  ```

---

## 12. `GET /admin`
- **Method & Path:** `GET /admin`
- **Business Description:** Administrator dashboard (`UC03` / `FR4`) returning filtered tickets (by `q` ticket code and `status`), status counts, active technicians with open ticket counts, and unmasked customer phone numbers (`QT-15`).
- **Authentication:** Required (`role = QUAN_TRI`).
- **Parameters & Request Body:** Optional query parameters:
  - `q` (`string`): substring match on `ticket_code`
  - `status` (`string`): exact `STATUS_LABELS` key (`MOI`, `DA_PHAN_CONG`, `DANG_XU_LY`, `CHO_LINH_KIEN`, `HOAN_TAT`, `DA_DONG`)
- **Success Response (`200 OK`):** HTML view (`admin.html`) or JSON `{"tickets": [...], "counts": {...}, "technicians": [...]}`.
- **Error Codes:** `401` unauthenticated, `403` wrong role.
- **Notes & Limits:** Maximum `200` tickets returned (`find_tickets` default limit). Only `QUAN_TRI` receives unmasked `customer_phone`.
- **Real Request & Response Example:**
  ```http
  GET /admin?status=MOI HTTP/1.1
  Accept: application/json
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "counts": {
      "DANG_XU_LY": 1,
      "DA_DONG": 1,
      "MOI": 2
    },
    "technicians": [
      {"full_name": "Le Hoang Nam", "open_tickets": 1, "technician_id": 1},
      {"full_name": "Pham Quoc Bao", "open_tickets": 0, "technician_id": 2}
    ],
    "tickets": [
      {
        "closed_at": null,
        "customer_id": 4,
        "customer_name": "Pham Minh Duc",
        "customer_phone": "0966555444",
        "device_id": 4,
        "due_date": "Mon, 16 Nov 2026 01:53:05 GMT",
        "issue_category": "SAC",
        "issue_desc": "Cong sac Type-C bi long, khong nhan sac nhanh",
        "model_name": "Mekong Phone S2",
        "priority": "TRUNG_BINH",
        "purchase_date": "Mon, 01 Jun 2026 00:00:00 GMT",
        "received_at": "Thu, 12 Nov 2026 01:53:05 GMT",
        "received_by_employee_id": 1,
        "serial_no": "IMEI357777777777001",
        "tech_name": null,
        "technician_id": null,
        "ticket_code": "BH-0004",
        "ticket_id": 4,
        "ticket_status": "MOI",
        "warranty": "ok",
        "warranty_months": 12
      }
    ]
  }
  ```

---

## 13. `POST /admin/assign/<int:ticket_id>`
- **Method & Path:** `POST /admin/assign/<int:ticket_id>`
- **Business Description:** Assigns exactly one active technician to a `MOI` ticket (`UC04` / `FR5`), transitions status to `DA_PHAN_CONG`, and writes a log record.
- **Authentication:** Required (`role = QUAN_TRI`).
- **Parameters & Request Body:** Path param `ticket_id` (`int`); Body field `technician_id` (`int`, required, active technician).
- **Success Response (`200 OK` JSON / `302` HTML):** `{"ticket_code", "technician_id", "ticket_status": "DA_PHAN_CONG"}`.
- **Error Codes:**
  | Status | Condition | Body (JSON) |
  | :---: | :--- | :--- |
  | `400` | Ticket already assigned, status != `MOI`, or technician nonexistent/inactive (`US4-AC3`) | `{"error": "...", "fields": [...]}` |
  | `401` / `403` | Unauthenticated or non-admin role | `{"error": "..."}` |
  | `404` | Ticket not found | `{"error": "Không tìm thấy phiếu.", "fields": []}` |
- **Notes & Limits:** Prevents assigning a second technician once `technician_id` is non-null.
- **Real Request & Response Example:**
  ```http
  POST /admin/assign/4 HTTP/1.1
  Content-Type: application/json
  Accept: application/json

  {"technician_id": 1}
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "technician_id": 1,
    "ticket_code": "BH-0004",
    "ticket_status": "DA_PHAN_CONG"
  }
  ```

---

## 14. `POST /admin/update/<int:ticket_id>`
- **Method & Path:** `POST /admin/update/<int:ticket_id>`
- **Business Description:** Comprehensive ticket update for administrators (`issue_category`, `priority`, `ticket_status`, `issue_desc`, `technician_id`), recalculating `due_date` when priority changes and recording `ticket_status_log` and `closed_at` when status changes.
- **Authentication:** Required (`role = QUAN_TRI`).
- **Parameters & Request Body:** Path param `ticket_id` (`int`); Optional body fields (defaults to existing values if omitted): `issue_category`, `priority`, `ticket_status`, `issue_desc` (min 10 chars), `technician_id` (int or empty/null).
- **Success Response (`200 OK` JSON / `302` HTML):** `{"ticket_code", "message": "Đã cập nhật thông tin phiếu."}`.
- **Error Codes:**
  | Status | Condition | Body (JSON) |
  | :---: | :--- | :--- |
  | `400` | Invalid category, priority, status, or description `< 10` chars | `{"error": "...", "fields": []}` |
  | `401` / `403` | Unauthenticated or non-admin role | `{"error": "..."}` |
  | `404` | Ticket not found | `{"error": "Không tìm thấy phiếu.", "fields": []}` |
- **Notes & Limits:** Admin updates bypass linear `TECH_TRANSITIONS` by design for administrative overrides; sets `closed_at` when moved to `DA_DONG` and clears it if reopened.
- **Real Request & Response Example:**
  ```http
  POST /admin/update/4 HTTP/1.1
  Content-Type: application/json
  Accept: application/json

  {"issue_category": "SAC", "priority": "CAO", "ticket_status": "HOAN_TAT", "technician_id": 1}
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "message": "Đã cập nhật thông tin phiếu.",
    "ticket_code": "BH-0004"
  }
  ```

---

## 15. `GET /technician`
- **Method & Path:** `GET /technician`
- **Business Description:** Returns only tickets assigned to the logged-in technician (`UC05` / `FR6`), including `next_statuses` allowed by linear workflow `TECH_TRANSITIONS` and masked customer phone numbers (`QT-15`).
- **Authentication:** Required (`role = KY_THUAT`, requires linked `technician_id` in session).
- **Parameters & Request Body:** None.
- **Success Response (`200 OK`):** HTML view (`technician.html`) or JSON `{"tickets": [...]}`.
- **Error Codes:** `401` unauthenticated, `403` non-technician role.
- **Notes & Limits:** Scoped strictly by `t.technician_id = session["technician_id"]`; `customer_phone` is masked as `084****647`.
- **Real Request & Response Example:**
  ```http
  GET /technician HTTP/1.1
  Accept: application/json
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "tickets": [
      {
        "closed_at": null,
        "customer_id": 1,
        "customer_name": "Vu The Long",
        "customer_phone": "084****647",
        "device_id": 1,
        "due_date": "Sun, 25 Oct 2026 09:00:00 GMT",
        "issue_category": "MAN_HINH",
        "issue_desc": "Man hinh bi soc doc, khong cam ung duoc",
        "model_name": "Mekong Phone X1",
        "next_statuses": ["CHO_LINH_KIEN"],
        "priority": "CAO",
        "purchase_date": "Sun, 15 Mar 2026 00:00:00 GMT",
        "received_at": "Sat, 24 Oct 2026 09:00:00 GMT",
        "received_by_employee_id": 1,
        "serial_no": "IMEI350000000000001",
        "tech_name": "Le Hoang Nam",
        "technician_id": 1,
        "ticket_code": "BH-0001",
        "ticket_id": 1,
        "ticket_status": "DANG_XU_LY",
        "warranty": "ok",
        "warranty_months": 12
      }
    ]
  }
  ```

---

## 16. `POST /technician/update/<int:ticket_id>`
- **Method & Path:** `POST /technician/update/<int:ticket_id>`
- **Business Description:** Advances an assigned ticket along the strict linear technician progression (`DA_PHAN_CONG` → `DANG_XU_LY` → `CHO_LINH_KIEN` → `HOAN_TAT`) and writes a `ticket_status_log` entry (`UC06` / `QT-06`).
- **Authentication:** Required (`role = KY_THUAT`) + **Ownership check (`OWASP A01`)**: `ticket.technician_id == session["technician_id"]`.
- **Parameters & Request Body:** Path param `ticket_id` (`int`); Body field `new_status` (`string`, must match `TECH_TRANSITIONS[current_status]`).
- **Success Response (`200 OK` JSON / `302` HTML):** `{"ticket_code", "old_status", "new_status"}`.
- **Error Codes:**
  | Status | Condition | Body (JSON) |
  | :---: | :--- | :--- |
  | `400` | Invalid transition (skip or backward step) | `{"error": "Chuyển trạng thái không hợp lệ (không được quay lại hoặc bỏ bước).", "fields": []}` |
  | `401` | Not logged in | `{"error": "Chưa đăng nhập."}` |
  | `403` | Non-technician role OR ticket belongs to another technician (IDOR blocked) | `{"error": "Phiếu này không được phân công cho bạn.", "fields": []}` |
  | `404` | Ticket not found | `{"error": "Không tìm thấy phiếu.", "fields": []}` |
- **Notes & Limits:** Enforces `403` even on plain form POSTs when ownership check fails.
- **Real Request & Response Example:**
  *Success (owner `kythuatvien`):*
  ```http
  POST /technician/update/1 HTTP/1.1
  Content-Type: application/json
  Accept: application/json

  {"new_status": "CHO_LINH_KIEN"}
  ```
  ```json
  HTTP/1.1 200 OK
  Content-Type: application/json

  {
    "new_status": "CHO_LINH_KIEN",
    "old_status": "DANG_XU_LY",
    "ticket_code": "BH-0001"
  }
  ```
  *Ownership violation (non-owner `kythuatvien2` attempting IDOR):*
  ```json
  HTTP/1.1 403 FORBIDDEN
  Content-Type: application/json

  {
    "error": "Phiếu này không được phân công cho bạn.",
    "fields": []
  }
  ```

