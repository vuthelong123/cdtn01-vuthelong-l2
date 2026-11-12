"""Routes dành cho Quản trị viên: UC03 tra cứu, UC04 gán KTV, cập nhật phiếu."""
from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)

from repositories import MySQLTicketRepository
from services import (STATUS_LABELS, ValidationError, admin_update_ticket,
                      assign_technician, warranty_state)

from .auth_routes import login_required
from .helpers import (get_payload, internal_error_response,
                      validation_error_response, wants_json)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin", endpoint="admin")
@login_required("QUAN_TRI")
def admin_view():
    repo = MySQLTicketRepository()
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")

    conds, args = [], []
    if q:
        conds.append("t.ticket_code LIKE %s")
        args.append(f"%{q}%")
    if status in STATUS_LABELS:
        conds.append("t.ticket_status = %s")
        args.append(status)

    tickets = repo.find_tickets(" AND ".join(conds), args)
    for t in tickets:
        t["warranty"] = warranty_state(t)

    counts = repo.get_status_counts()
    technicians = repo.get_active_technicians()

    if wants_json():
        return jsonify(tickets=tickets, counts=counts, technicians=technicians), 200

    return render_template(
        "admin.html",
        tickets=tickets,
        counts=counts,
        technicians=technicians,
        q=q,
        status=status,
    )


@admin_bp.route("/admin/assign/<int:ticket_id>", methods=["POST"], endpoint="assign_ticket")
@login_required("QUAN_TRI")
def assign_ticket_route(ticket_id):
    repo = MySQLTicketRepository()
    raw_tech = get_payload().get("technician_id")
    try:
        tech_id = int(raw_tech) if raw_tech not in (None, "") else None
    except (TypeError, ValueError):
        tech_id = None
    try:
        code = assign_technician(repo, ticket_id, tech_id, session["employee_id"])
        if wants_json():
            return jsonify(ticket_code=code, technician_id=tech_id, ticket_status="DA_PHAN_CONG"), 200
        flash(f"Đã phân công phiếu {code}.", "success")
    except ValidationError as exc:
        repo.rollback()
        return validation_error_response(exc, "admin")
    except Exception as exc:
        repo.rollback()
        return internal_error_response(exc, "admin")
    return redirect(request.referrer or url_for("admin"))


@admin_bp.route("/admin/update/<int:ticket_id>", methods=["POST"], endpoint="admin_update_ticket")
@login_required("QUAN_TRI")
def admin_update_ticket_route(ticket_id):
    repo = MySQLTicketRepository()
    try:
        code = admin_update_ticket(repo, ticket_id, get_payload(), session["employee_id"])
        if wants_json():
            return jsonify(ticket_code=code, message="Đã cập nhật thông tin phiếu."), 200
        flash(f"Đã cập nhật thông tin phiếu {code}.", "success")
    except ValidationError as exc:
        repo.rollback()
        return validation_error_response(exc, "admin")
    except Exception as exc:
        repo.rollback()
        return internal_error_response(exc, "admin")
    return redirect(request.referrer or url_for("admin"))
