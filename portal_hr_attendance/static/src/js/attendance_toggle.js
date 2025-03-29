/** @odoo-module **/

import publicWidget from 'web.public.widget';
import ajax from 'web.ajax';

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
