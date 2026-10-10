import os
import subprocess
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, session
from models import get_db, oid, now_utc, format_date, log_activity, backup_database
import config
from routes.decorators import role_required
from models.security import validate_user_payload, normalize_text, csrf_protect

user_mgmt_bp = Blueprint("user_mgmt", __name__, url_prefix="/user_management")


@user_mgmt_bp.route("/", methods=["GET", "POST"])
@role_required("admin")
@csrf_protect
def index():
    db = get_db()
    try:
        cur = db.cursor(dictionary=True)

        if request.method == "POST":
            name = normalize_text(request.form.get("name"))
            email = normalize_text(request.form.get("email"))
            role = normalize_text(request.form.get("role", "faculty"))
            raw_pwd = request.form.get("password", "")

            errors, name, email, role = validate_user_payload(name, email, role, raw_pwd)
            if errors:
                flash(" ".join(errors), "error")
                cur.close()
                return redirect(url_for("user_mgmt.index"))

            cur.execute("SELECT id FROM users WHERE email=%s AND (is_deleted IS NULL OR is_deleted=0) LIMIT 1", (email,))
            if cur.fetchone():
                flash("A user with this email address already exists.", "error")
                cur.close()
                return redirect(url_for("user_mgmt.index"))

            hashed = bcrypt.hashpw(raw_pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cur.execute(
                "INSERT INTO users (name, email, password, role, created_at) VALUES (%s, %s, %s, %s, %s)",
                (name, email, hashed, role, now_utc().replace(tzinfo=None)),
            )
            new_uid = cur.lastrowid
            db.commit()

            admin_id = oid(session.get("user", {}).get("id"))
            try:
                log_activity(db, admin_id, "create_user", f"Created user {email} with role {role}", "user", new_uid)
            except Exception:
                pass
            cur.close()
            flash("User created successfully.", "success")
            return redirect(url_for("user_mgmt.index"))

        # Fallback query parameter deletion
        if "delete" in request.args:
            uid = oid(request.args["delete"])
            admin_id = oid(session.get("user", {}).get("id"))
            if uid and uid != admin_id:
                cur.execute("SELECT id, role, email FROM users WHERE id=%s LIMIT 1", (uid,))
                u = cur.fetchone()
                if u and u.get("role") != "admin":
                    cur.execute("DELETE FROM users WHERE id=%s", (uid,))
                    db.commit()
                    try:
                        log_activity(db, admin_id, "delete_user", f"Deleted user {u.get('email')}", "user", uid)
                    except Exception:
                        pass
                    flash("User deleted successfully.", "success")
            cur.close()
            return redirect(url_for("user_mgmt.index"))

        cur.execute("SELECT id, name, email, role, created_at FROM users WHERE (is_deleted IS NULL OR is_deleted=0) ORDER BY id ASC")
        users = cur.fetchall()
        cur.close()
        return render_template(
            "user_management.html",
            users=users,
            format_date=format_date
        )
    finally:
        db.close()


@user_mgmt_bp.route("/delete/<int:user_id>", methods=["POST"])
@role_required("admin")
@csrf_protect
def delete_user(user_id):
    admin_id = oid(session.get("user", {}).get("id"))
    if user_id == admin_id:
        flash("You cannot delete your own active administrator account.", "error")
        return redirect(url_for("user_mgmt.index"))

    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id, role, email FROM users WHERE id=%s LIMIT 1", (user_id,))
        u = cur.fetchone()
        if not u:
            flash("User not found.", "error")
        elif u.get("role") == "admin":
            flash("Cannot delete an administrator account directly.", "error")
        else:
            cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
            db.commit()
            try:
                log_activity(db, admin_id, "delete_user", f"Deleted user {u.get('email')}", "user", user_id)
            except Exception:
                pass
            flash("User deleted successfully.", "success")
        cur.close()
    finally:
        db.close()
    return redirect(url_for("user_mgmt.index"))


@user_mgmt_bp.route("/backup")
@role_required("admin")
def backup_db():
    backup_path = backup_database("uploads/backup.sql")
    with open(backup_path, "rb") as handle:
        content = handle.read()
    return Response(
        content,
        mimetype="application/sql",
        headers={"Content-Disposition": f"attachment; filename={os.path.basename(backup_path)}"}
    )


@user_mgmt_bp.route("/restore", methods=["POST"])
@role_required("admin")
@csrf_protect
def restore_db():
    file_storage = request.files.get("backup_file")
    if not file_storage or not file_storage.filename:
        flash("Please choose a backup file (.sql) to restore.", "error")
        return redirect(url_for("user_mgmt.index"))

    try:
        sql_text = file_storage.read().decode("utf-8")
        cmd = [
            "mysql",
            "--host", config.MYSQL_HOST,
            "--port", str(config.MYSQL_PORT),
            "--user", config.MYSQL_USER,
        ]
        if config.MYSQL_PASSWORD:
            cmd.append(f"--password={config.MYSQL_PASSWORD}")
        cmd.append(config.MYSQL_DB)

        subprocess.run(
            cmd,
            input=sql_text,
            text=True,
            check=True,
        )
        flash("Database restore completed successfully.", "success")
    except FileNotFoundError:
        flash("The MySQL client utility is not available on this server host path.", "error")
    except subprocess.CalledProcessError as exc:
        flash(f"Database restore failed: {exc}", "error")

    return redirect(url_for("user_mgmt.index"))
