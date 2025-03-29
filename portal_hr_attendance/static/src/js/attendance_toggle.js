odoo.define('portal_hr_attendance.attendance_toggle', function (require) {
    "use strict";

    var PublicWidget = require('web.public.widget');  // Access web.public.widget
    var ajax = require('web.ajax'); // Access web.ajax

    var AttendanceToggle = PublicWidget.Widget.extend({ // Use PublicWidget.Widget
        selector: '.o_portal_attendance',
        events: {
            'click .o_portal_attendance_button': '_onClickAttendance',
        },

        _onClickAttendance: function (ev) {
            var self = this;
            ajax.jsonRpc('/my/attendance/check', 'call', {}).then(function (data) { // Use ajax
                if (data.error) {
                    // Handle error
                } else {
                    // Update the page
                    window.location.reload();
                }
            });
        },
    });

    PublicWidget.registry.AttendanceToggle = AttendanceToggle; // Register the widget

    return AttendanceToggle;
});