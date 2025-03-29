/** @odoo-module **/

import publicWidget from 'web.public.widget';
import ajax from 'web.ajax';

const AttendanceToggle = publicWidget.Widget.extend({
    selector: '.btn-attendance-toggle',
    events: {
        'click': '_onToggleAttendance',
    },
    _onToggleAttendance(ev) {
        ev.preventDefault();
        fetch("/my/attendance/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                window.location.reload();
            } else {
                alert(data.message || "Error toggling attendance");
            }
        })
        .catch(err => {
            console.error(err);
            alert("An error occurred. Check the console for details.");
        });
    },
});

publicWidget.registry.AttendanceToggle = AttendanceToggle;
