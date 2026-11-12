"""Routes dành cho Kỹ thuật viên: UC05 xem phiếu, UC06 cập nhật trạng thái."""
from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   session, url_for)

from repositories import MySQLTicketRepository
from services import (STATUS_LABELS, TECH_TRANSITIONS, ValidationError,
                      mask_phone, update_tech_status, warranty_state)

from .auth_routes import login_required
from .helpers import (get_payload, internal_error_response,
                      validation_error_response, wants_json)

tech_bp = Blueprint("technician", __name__)


@tech_bp.route("/technician", endpoint="technician")
@login_required("KY_THUAT")
def technician_view():
    repo = MySQLTicketRepository()
    tickets = repo.find_tickets("t.technician_id = %s", (session["technician_id"],))
    for t in tickets:
        t["warranty"] = warranty_state(t)
        t["next_statuses"] = TECH_TRANSITIONS.get(t["ticket_status"], [])
    if wants_json():
        for t in tickets:
            t["customer_phone"] = mask_phone(t.get("customer_phone"))
        return jsonify(tickets=tickets), 200
    return render_template("technician.html", tickets=tickets)


@tech_bp.route("/technician/update/<int:ticket_id>", methods=["POST"], endpoint="update_status")
@login_required("KY_THUAT")
def update_status_route(ticket_id):
    repo = MySQLTicketRepository()
    new_status = get_payload().get("new_status")
    try:
        code, old_st, new_st = update_tech_status(
            repo,
            ticket_id,
            session["technician_id"],
            new_status,
            session["employee_id"],
        )
        if wants_json():
            return jsonify(ticket_code=code, old_status=old_st, new_status=new_st), 200
        flash(f"Phiếu {code}: {STATUS_LABELS[old_st]} → {STATUS_LABELS[new_st]}.", "success")
    except ValidationError as exc:
        repo.rollback()
        return validation_error_response(exc, "technician")
    except Exception as exc:
        repo.rollback()
        return internal_error_response(exc, "technician")
    return redirect(url_for("technician"))
