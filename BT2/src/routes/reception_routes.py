"""Routes dành cho Nhân viên tiếp nhận: UC01 tạo phiếu, UC02 phân loại, sửa mô tả, đóng phiếu."""
from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)

from repositories import MySQLTicketRepository, query
from services import (ValidationError, classify_ticket, close_ticket,
                      create_ticket, mask_phone, normalize_phone,
                      update_ticket_description, warranty_state)

from .auth_routes import login_required
from .helpers import (get_payload, internal_error_response,
                      validation_error_response, wants_json)

reception_bp = Blueprint("reception", __name__)


@reception_bp.route("/reception", endpoint="reception")
@login_required("TIEP_NHAN")
def reception_view():
    repo = MySQLTicketRepository()
    tickets = repo.find_tickets(limit=50)
    for t in tickets:
        t["warranty"] = warranty_state(t)
    if wants_json():
        for t in tickets:
            t["customer_phone"] = mask_phone(t.get("customer_phone"))
        return jsonify(tickets=tickets), 200
    return render_template("reception.html", tickets=tickets)


@reception_bp.route("/api/customer", endpoint="api_customer")
@login_required("TIEP_NHAN")
def api_customer():
    """US1-AC1: Tìm khách bằng SĐT, tự động trả về thông tin và thiết bị có sẵn (kèm ngày mua, hạn BH)."""
    phone = normalize_phone(request.args.get("phone"))
    if not phone:
        return jsonify(valid=False, error="Số điện thoại không hợp lệ."), 400

    cust = query("SELECT customer_id, full_name, email FROM customer WHERE phone = %s", (phone,), one=True)
    if not cust:
        return jsonify(valid=True, found=False, phone=phone)

    devices = query(
        "SELECT serial_no, model_name, purchase_date, warranty_months FROM device WHERE customer_id = %s",
        (cust["customer_id"],),
    )
    devices_data = []
    for d in devices:
        p_date = d.get("purchase_date")
        if p_date:
            if hasattr(p_date, "strftime"):
                p_date = p_date.strftime("%Y-%m-%d")
            else:
                p_date = str(p_date)[:10]
        devices_data.append({
            "serial_no": d["serial_no"],
            "model_name": d["model_name"],
            "purchase_date": p_date or "",
            "warranty_months": d.get("warranty_months") if d.get("warranty_months") is not None else "",
        })

    return jsonify(valid=True, found=True, phone=phone, full_name=cust["full_name"], devices=devices_data)


@reception_bp.route("/reception/create", methods=["POST"], endpoint="create_ticket")
@login_required("TIEP_NHAN")
def create_ticket_route():
    """UC01: Ủy quyền tạo phiếu cho ticket_service."""
    repo = MySQLTicketRepository()
    try:
        res = create_ticket(repo, get_payload(), session["employee_id"])
        if wants_json():
            return jsonify(
                ticket_id=res["ticket_id"],
                ticket_code=res["ticket_code"],
                ticket_status=res["ticket_status"],
                due_date=res["due_date"].isoformat(),
            ), 201
        flash(f"Đã tạo phiếu {res['ticket_code']}. Hạn cam kết: {res['due_date']:%d/%m/%Y %H:%M}.", "success")
    except ValidationError as exc:
        return validation_error_response(exc, "reception")
    except Exception as exc:
        return internal_error_response(exc, "reception")
    return redirect(url_for("reception"))


@reception_bp.route("/reception/classify/<int:ticket_id>", methods=["POST"], endpoint="classify_ticket")
@login_required("TIEP_NHAN")
def classify_ticket_route(ticket_id):
    """UC02: Phân loại nhóm sự cố và mức ưu tiên."""
    repo = MySQLTicketRepository()
    payload = get_payload()
    category = payload.get("issue_category")
    priority = payload.get("priority")
    try:
        code = classify_ticket(repo, ticket_id, category, priority)
        if wants_json():
            return jsonify(ticket_code=code, issue_category=category, priority=priority), 200
        flash(f"Đã phân loại phiếu {code}.", "success")
    except ValidationError as exc:
        repo.rollback()
        return validation_error_response(exc, "reception")
    except Exception as exc:
        repo.rollback()
        return internal_error_response(exc, "reception")
    return redirect(url_for("reception"))


@reception_bp.route("/reception/close/<int:ticket_id>", methods=["POST"], endpoint="close_ticket")
@login_required("TIEP_NHAN")
def close_ticket_route(ticket_id):
    """Nhân viên tiếp nhận đóng phiếu bảo hành khi đã hoàn tất."""
    repo = MySQLTicketRepository()
    try:
        code = close_ticket(repo, ticket_id, session["employee_id"])
        if wants_json():
            return jsonify(ticket_code=code, ticket_status="DA_DONG"), 200
        flash(f"Đã đóng phiếu {code} và hoàn tất quy trình.", "success")
    except ValidationError as exc:
        repo.rollback()
        return validation_error_response(exc, "reception")
    except Exception as exc:
        repo.rollback()
        return internal_error_response(exc, "reception")
    return redirect(url_for("reception"))


@reception_bp.route("/reception/edit-desc/<int:ticket_id>", methods=["POST"], endpoint="edit_ticket_desc")
@login_required("TIEP_NHAN")
def edit_ticket_desc_route(ticket_id):
    """Nhân viên tiếp nhận chỉnh sửa mô tả cho phiếu đã tạo."""
    repo = MySQLTicketRepository()
    new_desc = get_payload().get("issue_desc")
    try:
        code = update_ticket_description(repo, ticket_id, new_desc, session["employee_id"])
        if wants_json():
            return jsonify(ticket_code=code, message="Đã cập nhật mô tả."), 200
        flash(f"Đã cập nhật mô tả phiếu {code}.", "success")
    except ValidationError as exc:
        repo.rollback()
        return validation_error_response(exc, "reception")
    except Exception as exc:
        repo.rollback()
        return internal_error_response(exc, "reception")
    return redirect(url_for("reception"))
