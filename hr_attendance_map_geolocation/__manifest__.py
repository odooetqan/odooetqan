# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hr Attendance maps Geolocation",
    "summary": """
        With this module, the user's geolocation is tracked at the check-in/check-out stage, and manger can even set the attendance range for the employee.""",
    "version": "1.1.0",
    'license': 'OPL-1',
    "author": "Ahmed Mnasri",
    "website": "https://polyline.xyz",
    "depends": ["base_geolocalize","hr_attendance"],
    "data": [
        "views/hr_attendance_views.xml",
        "views/hr_emplyee_view.xml",
        "views/res_config_view.xml",
        "data/location_data.xml",
    ],
    "external_dependencies": {
        "python": ["geopy"],
    },
    "assets": {
        "web.assets_backend": [
            "hr_attendance_map_geolocation/static/src/js/my_attendances.js",

        ]
    },
    "installable": True,
    "auto_install": False,
    "application": False,
    "price": 50,
    "currency": "EUR",
    "live_test_url": 'https://www.youtube.com/watch?v=YI15MyFsT58',
    "images": ['static/description/Banner.gif']
}
