from flask import Blueprint, render_template, session, redirect, url_for
from models import get_db, status_badge, oid
from routes.decorators import role_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/admin")
@role_required("admin")
def admin():
    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS c FROM users WHERE is_deleted=0")
        total_users = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM equipment WHERE is_deleted=0")
        total_equipment = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM maintenance_requests WHERE (is_deleted IS NULL OR is_deleted=0)")
        total_req = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM maintenance_requests WHERE status='Pending' AND (is_deleted IS NULL OR is_deleted=0)")
        pending_req = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM maintenance_requests WHERE status='In Progress' AND (is_deleted IS NULL OR is_deleted=0)")
        inprogress_req = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM maintenance_logs")
        resolved_req = cur.fetchone()["c"]

        cur.execute(
            "SELECT e.name, COUNT(r.id) AS hits FROM equipment e "
            "JOIN maintenance_requests r ON e.id = r.equipment_id "
            "WHERE (e.is_deleted=0) "
            "GROUP BY e.id, e.name ORDER BY hits DESC LIMIT 5"
        )
        damaged_top = cur.fetchall()

        cur.execute(
            "SELECT DATE_FORMAT(date_reported, '%Y-%m') AS _id, COUNT(*) AS total "
            "FROM maintenance_requests WHERE (is_deleted IS NULL OR is_deleted=0) "
            "GROUP BY DATE_FORMAT(date_reported, '%Y-%m') ORDER BY _id ASC LIMIT 12"
        )
        monthly = cur.fetchall()

        cur.execute("SELECT status AS _id, COUNT(*) AS count FROM equipment WHERE is_deleted=0 GROUP BY status ORDER BY FIELD(status, 'Working', 'Under Repair', 'Not Working', 'Under Maintenance', 'Damaged')")
        status_dist = cur.fetchall()

        cur.execute("SELECT actor_id, action, details, target_type, target_id, created_at FROM activity_logs ORDER BY created_at DESC LIMIT 15")
        activity_logs = cur.fetchall()

        cur.execute(
            "SELECT AVG(TIMESTAMPDIFF(SECOND, date_reported, COALESCE(date_responded, NOW())) / 3600) AS avg_hours "
            "FROM maintenance_requests WHERE (is_deleted IS NULL OR is_deleted=0)"
        )
        avg_resp = float((cur.fetchone() or {}).get("avg_hours") or 0.0)

        cur.execute(
            "SELECT AVG(TIMESTAMPDIFF(SECOND, mr.date_reported, ml.date_completed) / 3600) AS avg_hours "
            "FROM maintenance_requests mr JOIN maintenance_logs ml ON mr.id = ml.request_id"
        )
        avg_res = float((cur.fetchone() or {}).get("avg_hours") or 0.0)

        cur.execute(
            "SELECT HOUR(date_reported) AS peak_hour, COUNT(*) as c FROM maintenance_requests "
            "WHERE (is_deleted IS NULL OR is_deleted=0) GROUP BY peak_hour ORDER BY c DESC LIMIT 1"
        )
        peak_row = cur.fetchone()
        peak_hour_str = f"{int(peak_row['peak_hour']):02d}:00" if peak_row and peak_row.get("peak_hour") is not None else "N/A"

        # 1. Active Work Tracker for Under Repair items
        cur.execute(
            """
            SELECT mr.id AS request_id,
                   e.id AS equipment_id,
                   e.name AS equipment_name,
                   e.category AS equipment_category,
                   e.location AS equipment_location,
                   e.status AS equipment_status,
                   mr.status AS request_status,
                   mr.urgency,
                   mr.affected_component,
                   mr.date_reported,
                   mr.repair_start,
                   tech.name AS technician_name,
                   tech.email AS technician_email
            FROM equipment e
            LEFT JOIN maintenance_requests mr ON mr.equipment_id = e.id AND (mr.is_deleted IS NULL OR mr.is_deleted=0) AND mr.status IN ('In Progress', 'Pending')
            LEFT JOIN users tech ON mr.technician_id = tech.id
            WHERE e.is_deleted = 0 AND (e.status = 'Under Repair' OR mr.status = 'In Progress')
            ORDER BY (CASE WHEN mr.repair_start IS NOT NULL THEN mr.repair_start ELSE mr.date_reported END) ASC
            """
        )
        under_repair_items = cur.fetchall()

        from models import format_duration_minutes, now_utc
        now_time = now_utc().replace(tzinfo=None)
        for item in under_repair_items:
            start = item.get("repair_start") or item.get("date_reported")
            if start:
                elapsed_mins = max(1, int(round((now_time - start).total_seconds() / 60.0)))
                item["elapsed_str"] = format_duration_minutes(elapsed_mins)
            else:
                item["elapsed_str"] = "—"

        # 2. Monthly Technician Metrics (assigned vs. completed)
        current_month_key = now_time.strftime("%Y-%m")
        current_month_label = now_time.strftime("%B %Y")
        cur.execute(
            """
            SELECT 
                u.id AS technician_id,
                u.name AS technician_name,
                u.email AS technician_email,
                COUNT(DISTINCT CASE WHEN DATE_FORMAT(mr.date_reported, '%Y-%m') = %s THEN mr.id END) AS month_assigned,
                COUNT(DISTINCT CASE WHEN DATE_FORMAT(ml.date_completed, '%Y-%m') = %s THEN ml.id END) AS month_completed,
                COUNT(DISTINCT CASE WHEN mr.status = 'In Progress' THEN mr.id END) AS active_in_progress,
                AVG(CASE WHEN DATE_FORMAT(ml.date_completed, '%Y-%m') = %s AND ml.duration_minutes IS NOT NULL THEN ml.duration_minutes END) AS avg_duration_mins
            FROM users u
            LEFT JOIN maintenance_requests mr ON mr.technician_id = u.id AND (mr.is_deleted IS NULL OR mr.is_deleted = 0)
            LEFT JOIN maintenance_logs ml ON ml.technician_id = u.id
            WHERE u.role = 'technician' AND (u.is_deleted IS NULL OR u.is_deleted = 0)
            GROUP BY u.id, u.name, u.email
            ORDER BY month_completed DESC, month_assigned DESC, u.name ASC
            """,
            (current_month_key, current_month_key, current_month_key)
        )
        technician_workload = cur.fetchall()
        for tw in technician_workload:
            ass = tw["month_assigned"] or 0
            comp = tw["month_completed"] or 0
            tw["efficiency_rate"] = round((comp / ass * 100), 1) if ass > 0 else (100.0 if comp > 0 else 0.0)
            tw["avg_duration_str"] = format_duration_minutes(tw["avg_duration_mins"]) if tw["avg_duration_mins"] else "—"

        # 3. Problem Identification & Problematic Device Watchlist
        cur.execute(
            """
            SELECT 
                e.id,
                e.name,
                e.category,
                e.location,
                e.status,
                COUNT(mr.id) AS failure_count,
                GROUP_CONCAT(DISTINCT COALESCE(mr.affected_component, 'General') ORDER BY mr.id DESC SEPARATOR ', ') AS recurring_parts,
                MAX(mr.date_reported) AS last_failure
            FROM equipment e
            JOIN maintenance_requests mr ON mr.equipment_id = e.id AND (mr.is_deleted IS NULL OR mr.is_deleted = 0)
            WHERE e.is_deleted = 0
            GROUP BY e.id, e.name, e.category, e.location, e.status
            HAVING failure_count >= 2
            ORDER BY failure_count DESC, last_failure DESC
            LIMIT 8
            """
        )
        problematic_devices = cur.fetchall()
        for pd in problematic_devices:
            cnt = pd["failure_count"]
            if cnt >= 3:
                pd["risk_level"] = "Critical"
                pd["badge_class"] = "badge-danger"
            else:
                pd["risk_level"] = "Elevated"
                pd["badge_class"] = "badge-warning"

        cur.close()

        return render_template(
            "dashboard/admin.html",
            total_users=total_users,
            total_equipment=total_equipment,
            total_req=total_req,
            pending_req=pending_req,
            inprogress_req=inprogress_req,
            resolved_req=resolved_req,
            damaged_top=damaged_top,
            monthly=monthly,
            status_dist=status_dist,
            avg_resp=round(avg_resp, 2),
            avg_res=round(avg_res, 2),
            peak_hour_str=peak_hour_str,
            activity_logs=activity_logs,
            under_repair_items=under_repair_items,
            technician_workload=technician_workload,
            current_month_label=current_month_label,
            problematic_devices=problematic_devices,
            status_badge=status_badge,
        )
    finally:
        db.close()


@dashboard_bp.route("/custodian")
@role_required("custodian", "admin")
def custodian():
    if session.get("user", {}).get("role") == "admin":
        return redirect(url_for("dashboard.admin"))
    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS c FROM equipment WHERE is_deleted=0")
        total_eq = cur.fetchone()["c"]

        cur.execute("SELECT status AS _id, COUNT(*) AS total FROM equipment WHERE is_deleted=0 GROUP BY status")
        status_rows = cur.fetchall()

        cur.execute(
            "SELECT *, id AS _id FROM equipment WHERE is_deleted=0 ORDER BY id DESC"
        )
        equipment = cur.fetchall()
        cur.close()

        with_qr    = [e for e in equipment if e.get("qr_code")]
        without_qr = [e for e in equipment if not e.get("qr_code")]

        return render_template(
            "dashboard/custodian.html",
            total_eq=total_eq,
            status_rows=status_rows,
            equipment=equipment,
            with_qr=with_qr,
            without_qr=without_qr,
            status_badge=status_badge,
        )
    finally:
        db.close()


@dashboard_bp.route("/technician")
@role_required("technician", "admin")
def technician():
    if session.get("user", {}).get("role") == "admin":
        return redirect(url_for("dashboard.admin"))
    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS c FROM maintenance_requests WHERE status='Pending' AND (is_deleted IS NULL OR is_deleted=0)")
        pending_count = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM maintenance_requests WHERE status='In Progress' AND (is_deleted IS NULL OR is_deleted=0)")
        in_progress_count = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM maintenance_logs")
        completed_repairs = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM equipment WHERE is_deleted=0")
        total_equipment = cur.fetchone()["c"]

        user_id = session.get("user", {}).get("id")
        cur.execute(
            "SELECT r.*, e.name AS equipment_name, e.location AS equipment_location, "
            "u.name AS reporter_name, tech.name AS technician_name FROM maintenance_requests r "
            "LEFT JOIN equipment e ON r.equipment_id = e.id "
            "LEFT JOIN users u ON r.reported_by = u.id "
            "LEFT JOIN users tech ON r.technician_id = tech.id "
            "WHERE r.status IN ('Pending', 'In Progress') AND (r.is_deleted IS NULL OR r.is_deleted=0) "
            "ORDER BY (CASE WHEN r.technician_id = %s THEN 0 ELSE 1 END), (CASE WHEN r.status = 'Pending' THEN 1 ELSE 2 END), r.id DESC LIMIT 10",
            (user_id,)
        )
        active_requests = cur.fetchall()

        cur.execute(
            "SELECT ml.id, ml.action_taken, ml.date_completed, e.name AS equipment_name, "
            "mr.urgency, u.name AS reporter_name FROM maintenance_logs ml "
            "JOIN equipment e ON ml.equipment_id = e.id "
            "JOIN maintenance_requests mr ON ml.request_id = mr.id "
            "LEFT JOIN users u ON mr.reported_by = u.id "
            "ORDER BY ml.date_completed DESC LIMIT 5"
        )
        recent_logs = cur.fetchall()

        cur.close()

        return render_template(
            "dashboard/technician.html",
            pending_count=pending_count,
            in_progress_count=in_progress_count,
            completed_repairs=completed_repairs,
            total_equipment=total_equipment,
            active_requests=active_requests,
            recent_logs=recent_logs,
            status_badge=status_badge,
        )
    finally:
        db.close()


@dashboard_bp.route("/faculty")
@role_required("faculty", "admin")
def faculty():
    if session.get("user", {}).get("role") == "admin":
        return redirect(url_for("dashboard.admin"))
    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        my_id = oid(session["user"]["id"])
        my_count = 0
        pending_count = 0
        resolved_count = 0
        recent_requests = []

        if my_id:
            cur.execute("SELECT COUNT(*) AS c FROM maintenance_requests WHERE reported_by=%s AND (is_deleted IS NULL OR is_deleted=0)", (my_id,))
            my_count = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM maintenance_requests WHERE reported_by=%s AND status IN ('Pending', 'In Progress') AND (is_deleted IS NULL OR is_deleted=0)", (my_id,))
            pending_count = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM maintenance_requests WHERE reported_by=%s AND status='Resolved' AND (is_deleted IS NULL OR is_deleted=0)", (my_id,))
            resolved_count = cur.fetchone()["c"]

            cur.execute(
                "SELECT r.*, e.name AS equipment_name, e.location AS equipment_location "
                "FROM maintenance_requests r JOIN equipment e ON r.equipment_id = e.id "
                "WHERE r.reported_by=%s AND (r.is_deleted IS NULL OR r.is_deleted=0) "
                "ORDER BY r.date_reported DESC LIMIT 5",
                (my_id,)
            )
            recent_requests = cur.fetchall()

        cur.close()

        return render_template(
            "dashboard/faculty.html",
            my_count=my_count,
            pending_count=pending_count,
            resolved_count=resolved_count,
            recent_requests=recent_requests,
            status_badge=status_badge,
        )
    finally:
        db.close()

