# QR Code-Enabled Equipment Repair and Maintenance Management System (MySQL + PHP)

Full-stack portal uses **Python Flask** and **MySQL** (`qr_maintenance_db`), with complete tracking of equipment lifecycle, QR dispatch, and maintenance workflows.

## Prerequisites

1. **XAMPP** (or Apache + PHP 8.x)
2. **MySQL Community Server** running locally (`mysql://127.0.0.1:27017`)
3. **Composer** — [getcomposer.org](https://getcomposer.org/)
4. PHP **`mysql` extension** (required by the driver)

### Enable `mysql` in XAMPP (Windows)

1. Download a **Thread Safe** `php_mysql.dll` matching your PHP version from [PECL mysql](https://pecl.php.net/package/mysql) or use the DLL bundled with your PHP build if available.
2. Copy `php_mysql.dll` into your PHP `ext` folder (e.g. `C:\xampp\php\ext\`).
3. Edit `php.ini` and add: `extension=mysql`
4. Restart Apache.

Verify:

```powershell
php -m | findstr mysql
```

## Setup

1. Clone/copy project to `c:\xampp\htdocs\WEBBASED` (or your docroot).

2. Install PHP dependencies:

   ```powershell
   cd c:\xampp\htdocs\WEBBASED
   composer install
   ```

3. **Seed MySQL** (default users — same passwords as before):

   ```powershell
   mongosh --file c:\xampp\htdocs\WEBBASED\mongo_seed.mongosh.js
   ```

4. Optional: override connection via environment variables:

   - `MONGODB_URI` (default `mysql://127.0.0.1:27017`)
   - `MONGODB_DB` (default `qr_maintenance_db`)

5. Open **`http://localhost/WEBBASED`**

### Default accounts

| Role | Email | Password |
|------|--------|----------|
| Admin | admin@school.edu | admin123 |
| Custodian | custodian@school.edu | custodian123 |
| Faculty | faculty@school.edu | faculty123 |

## Important details

- **IDs:** Equipment and requests use **MySQL ObjectIds** (24 hex chars). QR URLs look like `...?equipment_id=<ObjectId>`.
- **Geospatial:** Equipment stores `latitude`, `longitude`, and GeoJSON `geo` for **`$geoNear`** on **Nearby equipment**.
- **Legacy MySQL:** Previous schema is archived in **`archive_mysql_schema.sql`** (reference only).

## ITIM03 written submission

- Full short-bond–style narrative matching the case sheet (**Tasks 1–5**, scenario, checkpoints): **`ITIM03_Case_Project_Paper.txt`** — paste into Word, set Calibri 11, 1″ margins, single spacing, then add screenshots where marked.

## ITIM03 coursework (`mysql/` folder)

Separate **`mysql/`** package for class demos (`qr_maintenance_coursework`, Node demo UI, mongosh scripts). See **`mysql/README.md`**.

## Key files

| File | Purpose |
|------|---------|
| `config.php` | MySQL client + indexes |
| `includes/mongo_helpers.php` | ObjectId / date helpers |
| `mongo_seed.mongosh.js` | Seed users |
| `equipment.php` | Equipment CRUD + QR + geo fields |
| `nearby_equipment.php` | `$geoNear` listing |
| `admin_reports.php` | Aggregation pipelines + CSV |
