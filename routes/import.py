import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from models import get_db, now_utc
from routes.decorators import role_required
from models.security import csrf_protect, normalize_text

import_bp = Blueprint('import', __name__, url_prefix='/admin_import')

ALLOWED_EXT = {'csv'}

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

@import_bp.route('/', methods=['GET', 'POST'])
@role_required('admin')
@csrf_protect
def equipment_import():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file or not _allowed_file(file.filename):
            flash('Please upload a valid CSV file.', 'error')
            return redirect(url_for('import.equipment_import'))

        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        required_fields = {'name', 'category', 'location', 'purchase_cost', 'maintenance_cost', 'status', 'qr_code'}
        missing = required_fields - set(reader.fieldnames or [])
        if missing:
            flash(f'Missing required columns: {", ".join(missing)}', 'error')
            return redirect(url_for('import.equipment_import'))

        db = get_db()
        cur = db.cursor()
        inserted = 0
        for row in reader:
            name = normalize_text(row.get('name'))
            if not name:
                continue
            category = normalize_text(row.get('category')) or 'Desktop Workstation'
            raw_loc = normalize_text(row.get('location'))
            # Normalize to Laboratory 1 through Laboratory 7
            import re
            loc_match = re.search(r'([1-7])', raw_loc)
            if loc_match:
                location = f"Laboratory {loc_match.group(1)}"
            else:
                location = "Laboratory 1"

            purchase_cost = float(row.get('purchase_cost') or 0)
            maintenance_cost = float(row.get('maintenance_cost') or 0)
            raw_status = normalize_text(row.get('status'))
            if raw_status in ("Under Repair", "Under Maintenance"):
                status = "Under Repair"
            elif raw_status in ("Not Working", "Damaged"):
                status = "Not Working"
            else:
                status = "Working"

            qr_code = normalize_text(row.get('qr_code'))
            cur.execute(
                "INSERT INTO equipment (name, category, location, purchase_cost, maintenance_cost, status, qr_code, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (name, category, location, purchase_cost, maintenance_cost, status, qr_code, now_utc().replace(tzinfo=None))
            )
            inserted += 1
        db.commit()
        cur.close()
        flash(f'Successfully imported {inserted} equipment records.', 'success')
        return redirect(url_for('equipment.index'))
    return render_template('admin_import.html')
