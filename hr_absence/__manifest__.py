{
"name": "Attendance: Absence Daylines",
"version": "18.0.1.0.0",
"summary": "Compute per‑day/shift absence and show it next to HR Attendance",
"description": """
Adds a lightweight daily/shift "dayline" for each employee so you can see:
- hr_absence / Present / Partial per day
- Expected vs attended minutes, lateness, early checkout
- Smart button on Employee to open Daylines
- Menu under Attendances to review and filter hr_absence


Designed to play nicely with existing biometric processing that writes hr.attendance.
You can set your working timezone in user preferences. Defaults to Asia/Riyadh.
""",
"author": "Sirelkhatim",
"category": "Human Resources/Attendance",
"depends": ["hr_attendance", "hr_payroll"],
"data": [
"security/ir.model.access.csv",
"views/hr_absence_views.xml",
"views/hr_payslip.xml",
"data/cron.xml",
],
"license": "LGPL-3",
"installable": True,
"application": False,
}