from flask import Blueprint, render_template
from routes.decorators import login_required, role_required

scan_bp = Blueprint("scan", __name__)

@scan_bp.route("/scan")
@login_required
@role_required("admin", "custodian", "technician", "faculty")
def camera():
    return render_template("scan_camera.html")
