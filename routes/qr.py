import re
from flask import Blueprint, render_template, request, Response, redirect, url_for, abort
import requests as http_req
from models import get_db, oid
from routes.decorators import role_required

qr_bp = Blueprint("qr", __name__, url_prefix="/qr")


@qr_bp.route("/download/<equipment_id>")
@role_required("custodian", "technician", "admin")
def download(equipment_id):
    eq_oid = oid(equipment_id)
    if not eq_oid:
        abort(400, "Invalid equipment ID.")

    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id AS _id, name, qr_code FROM equipment WHERE id=%s AND is_deleted=0", (eq_oid,))
        eq = cur.fetchone()
        cur.close()
    finally:
        db.close()

    if not eq or not eq.get("qr_code"):
        abort(404, "QR code not found. Add the equipment first to generate its QR.")

    qr_url = eq["qr_code"]
    name = re.sub(r'[^a-z0-9_\-]', '_', eq.get("name", "equipment"), flags=re.IGNORECASE)
    filename = f"QR_{name}.png"

    try:
        resp = http_req.get(qr_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        image_data = resp.content
        return Response(
            image_data,
            mimetype="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-store",
            }
        )
    except Exception:
        return redirect(qr_url)


@qr_bp.route("/print")
@role_required("custodian", "technician", "admin")
def print_sheet():
    filter_ids = []
    ids_param = request.args.get("ids", "")
    if ids_param:
        for raw in ids_param.split(","):
            o = oid(raw.strip())
            if o:
                filter_ids.append(o)

    db = get_db()
    try:
        cur = db.cursor(dictionary=True)
        base_sql = """
            SELECT id AS _id, name, category, location, qr_code
            FROM equipment
            WHERE qr_code IS NOT NULL AND qr_code <> '' AND is_deleted=0
        """
        params = []
        if filter_ids:
            placeholders = ",".join(["%s"] * len(filter_ids))
            base_sql += f" AND id IN ({placeholders})"
            params.extend(filter_ids)
        base_sql += " ORDER BY name ASC"
        cur.execute(base_sql, tuple(params))
        equipment = cur.fetchall()
        cur.close()
    finally:
        db.close()

    return render_template("qr_print.html", equipment=equipment)
