
import xmlrpc.client

# Local Odoo credentials
LOCAL_ODOO_URL = "http://etqan_attendance.sirelkhatim.uk"
DB_NAME = "hr"
USERNAME = "hr"
PASSWORD = "hr"

# Odoo.sh credentials
ODOO_SH_URL = "https://etqan17.odoo.com/"
SH_DB_NAME = "odooetqan-odooetqan-main-11657895"
SH_USERNAME = "odoo@etqan-ltd.com"
SH_PASSWORD = "123456"

# Mapping punch_type to attendance_type
def get_attendance_type(punch_type):
    punch_to_attendance = {
        '0': '1',   # Check In -> Finger
        '1': '1',   # Check Out -> Finger
        '2': '4',   # Break Out -> Card
        '3': '4',   # Break In -> Card
        '4': '15',  # Overtime In -> Face
        '5': '15',  # Overtime Out -> Face
        '255': '255' # Duplicate
    }
    return punch_to_attendance.get(str(punch_type), '1')  # Default to '1' (Finger) if not found

# Authenticate to local Odoo
common = xmlrpc.client.ServerProxy(f'{LOCAL_ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})

if uid:
    models = xmlrpc.client.ServerProxy(f'{LOCAL_ODOO_URL}/xmlrpc/2/object')

    # Fetch attendance data
    attendances = models.execute_kw(DB_NAME, uid, PASSWORD, 'zk.machine.attendance', 'search_read', [[]], {
        'fields': ['id', 'employee_id', 'punching_time', 'device_id_num', 'attendance_type', 'punch_type', 'address_id']
    })

    print(f"Fetched {len(attendances)} attendance records from Local Odoo")

    # Authenticate to Odoo.sh
    common_sh = xmlrpc.client.ServerProxy(f'{ODOO_SH_URL}/xmlrpc/2/common')
    sh_uid = common_sh.authenticate(SH_DB_NAME, SH_USERNAME, SH_PASSWORD, {})

    if sh_uid:
        models_sh = xmlrpc.client.ServerProxy(f'{ODOO_SH_URL}/xmlrpc/2/object')

        # DEBUG: Check the expected data type for attendance_type
        fields = models_sh.execute_kw(SH_DB_NAME, sh_uid, SH_PASSWORD, 'zk.machine.attendance', 'fields_get', [], {'attributes': ['type']})
        print(f"Field Type for attendance_type: {fields['attendance_type']}")

        # Push attendance data to Odoo.sh
        for attendance in attendances:
            device_id_num = attendance['device_id_num']
            address_id = attendance['address_id'][0] if isinstance(attendance['address_id'], list) else attendance['address_id']

            # Search for employee_id in Odoo.sh using device_id_num
            employee = models_sh.execute_kw(SH_DB_NAME, sh_uid, SH_PASSWORD, 'hr.employee', 'search_read', [[('device_id_num', '=', device_id_num)]], {'fields': ['id']})

            if not employee:
                print(f"Skipping record: No employee found for device_id_num {device_id_num}")
                continue  # Skip if employee is not found

            employee_id = employee[0]['id']

            # Ensure attendance_type is mapped correctly
            attendance_type = get_attendance_type(attendance['punch_type'])

            # DEBUG: Print the record before sending
            print(f"Creating attendance record for Employee {employee_id}: punch_type={attendance['punch_type']}, mapped attendance_type={attendance_type}")

            # Create attendance record in Odoo.sh
            models_sh.execute_kw(SH_DB_NAME, sh_uid, SH_PASSWORD, 'zk.machine.attendance', 'create', [{
                'employee_id': employee_id,
                'punching_time': attendance['punching_time'],
                'device_id_num': device_id_num,
                'punch_type': attendance['punch_type'],
                'attendance_type': attendance_type,  # Ensure it's properly mapped
                'address_id': address_id
            }])

        print("✅ Attendance data successfully pushed to Odoo.sh")





















# import xmlrpc.client

# # Local Odoo credentials
# LOCAL_ODOO_URL = "http://etqan_attendance.sirelkhatim.uk"
# DB_NAME = "hr"
# USERNAME = "hr"
# PASSWORD = "hr"

# # Authenticate to local Odoo
# common = xmlrpc.client.ServerProxy(f'{LOCAL_ODOO_URL}/xmlrpc/2/common')
# uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})

# if uid:
#     models = xmlrpc.client.ServerProxy(f'{LOCAL_ODOO_URL}/xmlrpc/2/object')

#     # Fetch attendance data
#     attendances = models.execute_kw(DB_NAME, uid, PASSWORD, 'zk.machine.attendance', 'search_read', [[]], {
#         'fields': ['id', 'employee_id', 'punching_time', 'device_id_num', 'attendance_type', 'punch_type', 'address_id']
#     })

#     print(attendances)

#     # Odoo.sh credentials
#     ODOO_SH_URL = "https://etqan17-stage-17482206.dev.odoo.com/"
#     SH_DB_NAME = "etqan17-stage-17482206"
#     SH_USERNAME = "odoo@etqan-ltd.com"
#     SH_PASSWORD = "123456"

#     # Authenticate to Odoo.sh
#     common_sh = xmlrpc.client.ServerProxy(f'{ODOO_SH_URL}/xmlrpc/2/common')
#     sh_uid = common_sh.authenticate(SH_DB_NAME, SH_USERNAME, SH_PASSWORD, {})

#     if sh_uid:
#         models_sh = xmlrpc.client.ServerProxy(f'{ODOO_SH_URL}/xmlrpc/2/object')

#         # Push attendance data to Odoo.sh
#         for attendance in attendances:
#             device_id_num = attendance['device_id_num']
#             address_id = attendance['address_id'][0] if isinstance(attendance['address_id'], list) else attendance['address_id']

#             # Search for employee_id in Odoo.sh using device_id_num
#             employee = models_sh.execute_kw(SH_DB_NAME, sh_uid, SH_PASSWORD, 'hr.employee', 'search_read', [[('device_id_num', '=', device_id_num)]], {'fields': ['id']})

#             if not employee:
#                 print(f"Skipping record: No employee found for device_id_num {device_id_num}")
#                 continue  # Skip if employee is not found

#             employee_id = employee[0]['id']

#             # Ensure attendance_type is an integer
#             attendance_type = int(str(attendance['attendance_type']).strip()) if str(attendance['attendance_type']).strip().isdigit() else 0

#             # Create attendance record in Odoo.sh
#             models_sh.execute_kw(SH_DB_NAME, sh_uid, SH_PASSWORD, 'zk.machine.attendance', 'create', [{
#                 'employee_id': employee_id,
#                 'punching_time': attendance['punching_time'],
#                 'device_id_num': device_id_num,
#                 'punch_type': attendance['punch_type'],
#                 'address_id': address_id
#             }])














# # import xmlrpc.client

# # # Local Odoo credentials
# # LOCAL_ODOO_URL = "http://etqan_attendance.sirelkhatim.uk"
# # DB_NAME = "hr"
# # USERNAME = "hr"
# # PASSWORD = "hr"

# # # Authenticate to local Odoo
# # common = xmlrpc.client.ServerProxy(f'{LOCAL_ODOO_URL}/xmlrpc/2/common')
# # uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})

# # if uid:
# #     models = xmlrpc.client.ServerProxy(f'{LOCAL_ODOO_URL}/xmlrpc/2/object')

# #     # Fetch attendance data
# #     attendances = models.execute_kw(DB_NAME, uid, PASSWORD, 'zk.machine.attendance', 'search_read', [[]], {'fields': ['id', 'employee_id', 'punching_time', 'device_id_num', 'attendance_type', 'punch_type', 'address_id']})

# #     print(attendances)

# #     # Odoo.sh credentials
# #     ODOO_SH_URL = "https://etqan17-stage-17482206.dev.odoo.com/"
# #     SH_DB_NAME = "etqan17-stage-17482206"
# #     SH_USERNAME = "odoo@etqan-ltd.com"
# #     SH_PASSWORD = "123456"

# #     # Authenticate to Odoo.sh
# #     common_sh = xmlrpc.client.ServerProxy(f'{ODOO_SH_URL}/xmlrpc/2/common')
# #     sh_uid = common_sh.authenticate(SH_DB_NAME, SH_USERNAME, SH_PASSWORD, {})

# #     if sh_uid:
# #         models_sh = xmlrpc.client.ServerProxy(f'{ODOO_SH_URL}/xmlrpc/2/object')

# #         # Push attendance data to Odoo.
# #         for attendance in attendances:
# #             employee_id = attendance['employee_id'][0] if isinstance(attendance['employee_id'], list) else attendance['employee_id']
# #             address_id = attendance['address_id'][0] if isinstance(attendance['address_id'], list) else attendance['address_id']

# #             # Ensure attendance_type is an integer
# #             attendance_type = int(str(attendance['attendance_type']).strip()) if str(attendance['attendance_type']).strip().isdigit() else 0

# #             models_sh.execute_kw(SH_DB_NAME, sh_uid, SH_PASSWORD, 'zk.machine.attendance', 'create', [{
# #                 'employee_id': employee_id,
# #                 'punching_time': attendance['punching_time'],
# #                 'device_id_num': attendance['device_id_num'],
# #                 # 'attendance_type': attendance_type,  # Ensure it's an integer
# #                 'punch_type': attendance['punch_type'],
# #                 'address_id': address_id
# #             }])


# # sh
# #       #   for attendance in attendances:
# #       #       employee_id = attendance['employee_id'][0] if isinstance(attendance['employee_id'], list) else attendance['employee_id']
# #       #       address_id = attendance['address_id'][0] if isinstance(attendance['address_id'], list) else attendance['address_id
# #             '        #     # fields = models_sh.execute_kw(SH_DB_NAME, sh_uid, SH_PASSWORD, 'zk.machine.attendance', 'fields_get', [], {'attributes': ['type']})
# #         #     # print(fields['attendance_type'])
# # ]

# #       #       models_sh.execute_kw(SH_DB_NAME, sh_uid, SH_PASSWORD, 'zk.machine.attendance', 'create', [{
# #       #           'employee_id': employee_id,
# #       #           'punching_time': attendance['punching_time'],
# #       #           'device_id_num': attendance['device_id_num'],
# #       #           'attendance_type': attendance['attendance_type'],
# #       #           'punch_type': attendance['punch_type'],
# #       #           'address_id': address_id
# #       #       }])























# # import xmlrpc.client

# # # Local Odoo credentials
# # LOCAL_ODOO_URL = "http://etqan_attendance.sirelkhatim.uk"
# # DB_NAME = "hr"
# # USERNAME = "hr"
# # PASSWORD = "hr"

# # # Authenticate to local Odoo
# # common = xmlrpc.client.ServerProxy(f'{LOCAL_ODOO_URL}/xmlrpc/2/common')
# # uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})

# # if uid:
# #     models = xmlrpc.client.ServerProxy(f'{LOCAL_ODOO_URL}/xmlrpc/2/object')

# #     # Fetch data (Example: Fetching customers)
# #     customers = models.execute_kw(DB_NAME, uid, PASSWORD, 'zk.machine.attendance', 'search_read', [[]], {'fields': ['id', 'employee_id', 'punching_time', 'device_id_num', 'attendance_type', 'punch_type', 'address_id']})

# #     print(customers)



# #     ODOO_SH_URL = "https://etqan17-stage-17482206.dev.odoo.com/"
# #     SH_DB_NAME = "etqan17-stage-17482206"
# #     SH_USERNAME = "odoo@etqan-ltd.com"
# #     SH_PASSWORD = "123456"

# #     # Authenticate to Odoo.sh
# #     common_sh = xmlrpc.client.ServerProxy(f'{ODOO_SH_URL}/xmlrpc/2/common')
# #     sh_uid = common_sh.authenticate(SH_DB_NAME, SH_USERNAME, SH_PASSWORD, {})

# #     if sh_uid:
# #         models_sh = xmlrpc.client.ServerProxy(f'{ODOO_SH_URL}/xmlrpc/2/object')

# #         # Push customers to Odoo.sh
# #         for customer in customers:
# #             models_sh.execute_kw(SH_DB_NAME, sh_uid, SH_PASSWORD, 'res.partner', 'create', [{
# #                 'id': customer['id'],
# #                 'employee_id': customer['employee_id'],
# #                 'punching_time': customer['punching_time'],
# #                 'device_id_num': customer['device_id_num'],
# #                 'attendance_type': customer['attendance_type'],
# #                 'punch_type': customer['punch_type'],
# #                 'address_id': customer['address_id']
# #             }])
