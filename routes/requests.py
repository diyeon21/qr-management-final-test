from flask import Blueprint, render_template, request, redirect, url_for, session
from models import get_db, status_badge, oid, now_utc, log_activity
from routes.decorators import role_required
from models.security import csrf_protect

requests_bp = Blueprint("requests", __name__, url_prefix="/maintenance_requests")

ALLOWED_REQUEST_STATUSES = {"Pending", "In Progress", "Resolved", "Rejected"}


@requests_bp.route("/assign/<int:request_id>", methods=["POST"])
@role_required("admin")
@csrf_protect
def assign_technician(request_id):
    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        tech_val = (request.form.get("technician_id") or "").strip()
        new_tech_id = oid(tech_val) if tech_val else None

        cur.execute("SELECT technician_id FROM maintenance_requests WHERE id=%s", (request_id,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE maintenance_requests SET technician_id=%s WHERE id=%s", (new_tech_id, request_id))
            if new_tech_id:
                cur.execute(
                    "SELECT r.id, e.name AS equipment_name, u.name AS tech_name FROM maintenance_requests r "
                    "JOIN equipment e ON r.equipment_id = e.id "
                    "JOIN users u ON u.id = %s WHERE r.id = %s",
                    (new_tech_id, request_id)
                )
                tinfo = cur.fetchone()
                if tinfo:
                    from models.db import create_notification
                    create_notification(
                        db,
                        new_tech_id,
                        f"You have been assigned to repair equipment '{tinfo['equipment_name']}'",
                        url_for("requests.index")
                    )
                    try:
                        log_activity(db, session.get("user", {}).get("id"), "assign_technician", f"Assigned technician {tinfo['tech_name']} to request #{request_id}", "maintenance_request", request_id)
                    except Exception:
                        pass
            else:
                try:
                    log_activity(db, session.get("user", {}).get("id"), "unassign_technician", f"Unassigned technician from request #{request_id}", "maintenance_request", request_id)
                except Exception:
                    pass
            db.commit()
        cur.close()
    finally:
        db.close()
    return redirect(url_for("requests.index"))


@requests_bp.route("/", methods=["GET", "POST"])
@role_required("technician", "admin")
@csrf_protect
def index():
    db = get_db()
    try:
        cur = db.cursor(dictionary=True)

        if request.method == "POST":
            req_oid = oid(request.form.get("request_id"))
            if not req_oid:
                cur.close()
                return redirect(url_for("requests.index"))

            status = request.form.get("status", "Pending")
            if status not in ALLOWED_REQUEST_STATUSES:
                status = "Pending"

            # Validate action_taken is required when resolving
            if status == "Resolved":
                action = (request.form.get("action_taken") or "").strip()
                if not action:
                    cur.close()
                    return redirect(url_for("requests.index", error="action_required"))

            now_time = now_utc().replace(tzinfo=None)

            # If user is technician and request unassigned, assign to self
            logged_user = session.get("user", {})
            if logged_user.get("role") == "technician" and status in ("In Progress", "Resolved"):
                cur.execute("UPDATE maintenance_requests SET technician_id = COALESCE(technician_id, %s) WHERE id=%s", (logged_user.get("id"), req_oid))

            if status == "In Progress":
                cur.execute(
                    "UPDATE maintenance_requests SET status=%s, date_responded=%s, repair_start=COALESCE(repair_start, %s) WHERE id=%s",
                    (status, now_time, now_time, req_oid),
                )
            else:
                cur.execute(
                    "UPDATE maintenance_requests SET status=%s, date_responded=%s WHERE id=%s",
                    (status, now_time, req_oid),
                )

            # If admin also selected technician in this form
            if logged_user.get("role") == "admin" and "technician_id" in request.form:
                tech_val = (request.form.get("technician_id") or "").strip()
                new_tech_id = oid(tech_val) if tech_val else None
                cur.execute("UPDATE maintenance_requests SET technician_id=%s WHERE id=%s", (new_tech_id, req_oid))
                if new_tech_id:
                    cur.execute(
                        "SELECT r.id, e.name AS equipment_name, u.name AS tech_name FROM maintenance_requests r "
                        "JOIN equipment e ON r.equipment_id = e.id "
                        "JOIN users u ON u.id = %s WHERE r.id = %s",
                        (new_tech_id, req_oid)
                    )
                    tinfo = cur.fetchone()
                    if tinfo:
                        from models.db import create_notification
                        create_notification(
                            db,
                            new_tech_id,
                            f"You have been assigned to repair equipment '{tinfo['equipment_name']}'",
                            url_for("requests.index")
                        )

            if status == "Resolved":
                cur.execute(
                    "SELECT equipment_id, technician_id, repair_start, date_reported FROM maintenance_requests WHERE id=%s",
                    (req_oid,)
                )
                req_doc = cur.fetchone() or {}
                eq_id = req_doc.get("equipment_id")
                tech_id = req_doc.get("technician_id")
                start_time = req_doc.get("repair_start") or req_doc.get("date_reported") or now_time

                # Calculate duration in minutes
                try:
                    delta_seconds = (now_time - start_time).total_seconds()
                    duration_minutes = max(1, int(round(delta_seconds / 60.0)))
                except Exception:
                    duration_minutes = 0

                if eq_id:
                    cur.execute(
                        "INSERT INTO maintenance_logs (equipment_id, request_id, cost, action_taken, date_completed, repair_start, duration_minutes, technician_id) "
                        "VALUES (%s, %s, 0, %s, %s, %s, %s, %s)",
                        (eq_id, req_oid, action, now_time, start_time, duration_minutes, tech_id),
                    )
                    cur.execute(
                        "UPDATE equipment SET status='Working' WHERE id=%s",
                        (eq_id,),
                    )
            elif status == "In Progress":
                eq_id = oid(request.form.get("equipment_id"))
                if not eq_id:
                    cur.execute("SELECT equipment_id FROM maintenance_requests WHERE id=%s", (req_oid,))
                    r_row = cur.fetchone()
                    eq_id = r_row.get("equipment_id") if r_row else None
                if eq_id:
                    cur.execute("UPDATE equipment SET status='Under Repair' WHERE id=%s", (eq_id,))

            # Notify reporting faculty member
            cur.execute(
                "SELECT r.reported_by, e.name AS equipment_name FROM maintenance_requests r JOIN equipment e ON r.equipment_id = e.id WHERE r.id=%s",
                (req_oid,)
            )
            req_info = cur.fetchone()
            if req_info:
                from models.db import create_notification
                create_notification(
                    db,
                    req_info["reported_by"],
                    f"Your request for '{req_info['equipment_name']}' was updated to '{status}'",
                    url_for("my_req.index")
                )

            db.commit()
            try:
                log_activity(db, session.get("user", {}).get("id"), "update_request", f"Updated maintenance request id {req_oid} to '{status}'", "maintenance_request", req_oid)
            except Exception:
                pass

            cur.close()
            return redirect(url_for("requests.index"))

        cur.execute(
            "SELECT r.*, e.name AS equipment_name, e.location AS equipment_location, "
            "u.name AS reporter_name, tech.name AS technician_name, tech.email AS technician_email "
            "FROM maintenance_requests r "
            "LEFT JOIN equipment e ON r.equipment_id = e.id "
            "LEFT JOIN users u ON r.reported_by = u.id "
            "LEFT JOIN users tech ON r.technician_id = tech.id "
            "LEFT JOIN maintenance_logs ml ON r.id = ml.request_id "
            "WHERE r.status NOT IN ('Resolved', 'Rejected') AND ml.id IS NULL AND (r.is_deleted IS NULL OR r.is_deleted=0) "
            "ORDER BY r.id DESC"
        )
        rows = cur.fetchall()

        cur.execute("SELECT id, name, email FROM users WHERE role='technician' AND (is_deleted IS NULL OR is_deleted=0) ORDER BY name ASC")
        technicians = cur.fetchall()
        cur.close()

        return render_template(
            "maintenance_requests.html",
            rows=rows,
            technicians=technicians,
            status_badge=status_badge,
        )
    finally:
        db.close()
