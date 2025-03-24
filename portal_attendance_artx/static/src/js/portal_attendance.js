/*document.addEventListener("DOMContentLoaded", function () {
    const attendanceBtn = document.getElementById("attendanceBtn");
    const checkoutBtn = document.getElementById("checkoutBtn");

    if (attendanceBtn) {
        attendanceBtn.addEventListener("click", function () {
            fetch('/portal/add_attendance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    attendanceBtn.classList.add("d-none");
                    checkoutBtn.classList.remove("d-none");
                    alert("تم تسجيل الدخول بنجاح!");
                } else {
                    alert(data.message || "حدث خطأ أثناء تسجيل الدخول.");
                }
            })
            .catch(error => console.error("Error:", error));
        });
    }

    if (checkoutBtn) {
        checkoutBtn.addEventListener("click", function () {
            fetch('/portal/check_out', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    attendanceBtn.classList.remove("d-none");
                    checkoutBtn.classList.add("d-none");
                    alert("تم تسجيل الخروج بنجاح!");
                } else {
                    alert(data.message || "حدث خطأ أثناء تسجيل الخروج.");
                }
            })
            .catch(error => console.error("Error:", error));
        });
    }
});
*/
/* 
{<template id="portal_attendance_js" name="Portal Attendance JS">
    <script>
        function handleAttendance() {
            fetch('/portal/add_attendance', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById("attendanceBtn").classList.add("d-none");
                    document.getElementById("checkoutBtn").classList.remove("d-none");
                    alert("تم تسجيل الدخول بنجاح!");
                } else {
                    alert(data.message || "حدث خطأ أثناء تسجيل الدخول.");
                }
            })
            .catch(error => console.error("Error:", error));
        }

        function handleCheckout() {
            fetch('/portal/check_out', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById("attendanceBtn").classList.remove("d-none");
                    document.getElementById("checkoutBtn").classList.add("d-none");
                    alert("تم تسجيل الخروج بنجاح!");
                } else {
                    alert(data.message || "حدث خطأ أثناء تسجيل الخروج.");
                }
            })
            .catch(error => console.error("Error:", error));
        }
    </script>
</template> }*/
