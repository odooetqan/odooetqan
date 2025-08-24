#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Push zk.machine.attendance from Local Odoo to Odoo.sh, limited to the last N days.

Usage:
  python3 push_attendance_last_days.py           # uses DAYS_BACK default
  python3 push_attendance_last_days.py 3         # last 3 days
"""

import sys
import xmlrpc.client
from datetime import datetime, timedelta, timezone

# ----------------- CONFIG -----------------
# How many days back to fetch if no CLI argument is given
DAYS_BACK_DEFAULT = 2

# Local Odoo credentials
LOCAL_ODOO_URL = "http://etqan_attendance.sirelkhatim.uk"
DB_NAME        = "hr"
USERNAME       = "hr"
PASSWORD       = "hr"

# Odoo.sh credentials
ODOO_SH_URL    = "https://etqan17.odoo.com/"
SH_DB_NAME     = "odooetqan-odooetqan-main-11657895"
SH_USERNAME    = "odoo@etqan-ltd.com"
SH_PASSWORD    = "123456"
# ------------------------------------------

# Mapping punch_type to attendance_type
def get_attendance_type(punch_type):
    punch_to_attendance = {
        '0': '1',    # Check In  -> Finger
        '1': '1',    # Check Out -> Finger
        '2': '4',    # Break Out -> Card
        '3': '4',    # Break In  -> Card
        '4': '15',   # Overtime In  -> Face
        '5': '15',   # Overtime Out -> Face
        '255': '255' # Duplicate
    }
    return punch_to_attendance.get(str(punch_type), '1')

def parse_days_back():
    if len(sys.argv) >= 2:
        try:
            n = int(sys.argv[1])
            if n <= 0:
                raise ValueError
            return n
        except ValueError:
            print(f"[!] Invalid days argument: {sys.argv[1]!r}. Using default {DAYS_BACK_DEFAULT}.")
    return DAYS_BACK_DEFAULT

def main():
    days_back = parse_days_back()
    # Compute date_from in UTC; Odoo accepts naive 'YYYY-MM-DD HH:MM:SS' strings.
    # We'll format as naive string (no timezone). Adjust if your local Odoo expects a specific TZ.
    now_utc = datetime.now(timezone.utc)
    date_from = now_utc - timedelta(days=days_back)
    date_from_str = date_from.strftime("%Y-%m-%d %H:%M:%S")

    print(f"[i] Fetching attendance from the last {days_back} day(s), i.e. from {date_from_str} onwards.")

    # Authenticate to local Odoo
    common = xmlrpc.client.ServerProxy(f"{LOCAL_ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})
    if not uid:
        print("[x] Failed to authenticate to local Odoo.")
        sys.exit(1)

    models = xmlrpc.client.ServerProxy(f"{LOCAL_ODOO_URL}/xmlrpc/2/object")

    # Domain: only logs with punching_time >= date_from
    domain = [['punching_time', '>=', date_from_str]]
    fields = ['id', 'employee_id', 'punching_time', 'device_id_num', 'attendance_type', 'punch_type', 'address_id']

    # Read in batches to be safe with large sets
    limit = 2000
    offset = 0
    all_attendances = []

    print("[i] Reading local attendance in batches...")
    while True:
        batch = models.execute_kw(
            DB_NAME, uid, PASSWORD,
            'zk.machine.attendance', 'search_read',
            [domain],
            {'fields': fields, 'limit': limit, 'offset': offset, 'order': 'punching_time asc'}
        )
        if not batch:
            break
        all_attendances.extend(batch)
        offset += limit
        print(f"   ... fetched {len(all_attendances)} so far")

    print(f"[i] Total fetched from local: {len(all_attendances)}")

    # Authenticate to Odoo.sh
    common_sh = xmlrpc.client.ServerProxy(f"{ODOO_SH_URL}/xmlrpc/2/common")
    sh_uid = common_sh.authenticate(SH_DB_NAME, SH_USERNAME, SH_PASSWORD, {})
    if not sh_uid:
        print("[x] Failed to authenticate to Odoo.sh.")
        sys.exit(1)

    models_sh = xmlrpc.client.ServerProxy(f"{ODOO_SH_URL}/xmlrpc/2/object")

    # Optional: check field type once
    try:
        sh_fields = models_sh.execute_kw(
            SH_DB_NAME, sh_uid, SH_PASSWORD,
            'zk.machine.attendance', 'fields_get', [], {'attributes': ['type']}
        )
        print(f"[i] Odoo.sh field type for attendance_type: {sh_fields.get('attendance_type')}")
    except Exception as e:
        print(f"[!] Could not fetch fields_get on Odoo.sh: {e}")

    created = 0
    skipped_no_employee = 0
    skipped_duplicates = 0
    errors = 0

    for a in all_attendances:
        try:
            device_id_num = a.get('device_id_num')
            punching_time = a.get('punching_time')    # expected as 'YYYY-MM-DD HH:MM:SS'
            punch_type    = a.get('punch_type')

            # Normalize address_id to an integer ID if many2one
            addr = a.get('address_id')
            address_id = addr[0] if isinstance(addr, list) else addr

            # Find employee on Odoo.sh by device_id_num
            emp = models_sh.execute_kw(
                SH_DB_NAME, sh_uid, SH_PASSWORD,
                'hr.employee', 'search_read',
                [[('device_id_num', '=', device_id_num)]],
                {'fields': ['id'], 'limit': 1}
            )
            if not emp:
                skipped_no_employee += 1
                print(f"[-] Skip: no employee on Odoo.sh for device_id_num={device_id_num}")
                continue

            employee_id = emp[0]['id']
            attendance_type = get_attendance_type(punch_type)

            # Dedup: check if a record already exists on Odoo.sh with the same (employee_id, device_id_num, punching_time, punch_type)
            existing = models_sh.execute_kw(
                SH_DB_NAME, sh_uid, SH_PASSWORD,
                'zk.machine.attendance', 'search',
                [[
                    ('employee_id', '=', employee_id),
                    ('device_id_num', '=', device_id_num),
                    ('punching_time', '=', punching_time),
                    ('punch_type', '=', punch_type),
                ]],
                {'limit': 1}
            )
            if existing:
                skipped_duplicates += 1
                # You can print less if too chatty
                # print(f"[=] Duplicate found, skipping: emp={employee_id}, time={punching_time}, device={device_id_num}, punch={punch_type}")
                continue

            # Create on Odoo.sh
            models_sh.execute_kw(
                SH_DB_NAME, sh_uid, SH_PASSWORD,
                'zk.machine.attendance', 'create',
                [{
                    'employee_id': employee_id,
                    'punching_time': punching_time,
                    'device_id_num': device_id_num,
                    'punch_type': punch_type,
                    'attendance_type': attendance_type,
                    'address_id': address_id,
                }]
            )
            created += 1
        except Exception as e:
            errors += 1
            print(f"[x] Error creating record for device={device_id_num}, time={punching_time}: {e}")

    print("\n==== SUMMARY ====")
    print(f"Created on Odoo.sh:     {created}")
    print(f"Skipped (no employee):  {skipped_no_employee}")
    print(f"Skipped (duplicates):   {skipped_duplicates}")
    print(f"Errors:                 {errors}")

if __name__ == "__main__":
    main()
