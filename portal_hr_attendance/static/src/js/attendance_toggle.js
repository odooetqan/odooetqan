
/** @odoo-module **/
// import publicWidget from 'web.public.widget';
// import ajax from 'web.ajax';
/** @odoo-module **/

import publicWidget from 'web.public.widget';
import ajax from 'web.ajax';



odoo.define('portal_hr_attendance.attendance_toggle', function (require) {
    "use strict";


    
    publicWidget.registry.AttendanceToggle = publicWidget.Widget.extend({
        selector: '.btn-attendance-toggle',
        events: {
            'click': '_onToggleAttendance',
        },

        /**
         * Handle Check-In/Check-Out toggle
         */
        _onToggleAttendance: function (ev) {
            ev.preventDefault();
            fetch("/my/attendance/toggle", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({}),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    window.location.reload();  // Refresh after success
                } else {
                    alert(data.message || "Error toggling attendance.");
                }
            })
            .catch(err => {
                console.error(err);
                alert("An error occurred. Check the console for details.");
            });
        },
    });

    // Register the widget
    publicWidget.registry.AttendanceToggle;


    // Make the toggleAttendance function available globally
    window.toggleAttendance = function () {
        fetch("/my/attendance/toggle", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                // Reload the page to reflect new status
                window.location.reload();
            } else {
                alert(data.message || "Error toggling attendance");
            }
        })
        .catch(err => {
            console.error(err);
            alert("An error occurred. See console for details.");
        });
    };
});
