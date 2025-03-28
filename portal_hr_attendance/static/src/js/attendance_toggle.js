odoo.define('your_module.attendance_toggle', function (require) {
    "use strict";
    
    // Expose the toggleAttendance function globally
    window.toggleAttendance = function () {
        fetch("/my/attendance/toggle", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({})
        })
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            if (data.success) {
                alert(data.message);
                window.location.reload();
            } else {
                alert(data.message || "Error toggling attendance");
            }
        })
        .catch(function (err) {
            console.error(err);
            alert("An error occurred. See console for details.");
        });
    };
});
