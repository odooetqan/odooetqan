/** portal_attendance_artx/static/src/js/attendance_portal.js */
'use strict';

odoo.define('portal_attendance_artx.attendance', ['web.dom_ready'], function (require) {
    require('web.dom_ready');

    // --- helpers ---
    function getPos() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) return resolve(null);
            navigator.geolocation.getCurrentPosition(
                (p) => resolve({ lat: p.coords.latitude, lng: p.coords.longitude }),
                () => resolve(null),
                { enableHighAccuracy: true, timeout: 8000 }
            );
        });
    }

    function setBtnText(txt) {
        var span = document.getElementById('btnText');
        if (span) span.textContent = txt;
    }

    function setBusy(btn, busy) {
        if (!btn) return;
        btn.disabled = !!busy;
        btn.classList.toggle('disabled', !!busy);
    }

    // --- DOM elements ---
    var button = document.getElementById('attendanceBtn');
    var isCheckIn = true; // default guess; will be updated on load

    // --- initial status fetch ---
    function updateButtonStatus() {
        $.ajax({
            url: '/portal/get_attendance_status',
            type: 'GET',
            dataType: 'json',
            success: function (response) {
                if (response && response.success && response.message === 'Currently checked in') {
                    setBtnText('Click to Check Out');
                    isCheckIn = false;
                } else {
                    setBtnText('Click to Check In');
                    isCheckIn = true;
                }
            },
            error: function () {
                // fallback: assume next action is check-in
                setBtnText('Click to Check In');
                isCheckIn = true;
            }
        });
    }

    // --- click handler (sends coords!) ---
    async function onButtonClick(e) {
        e.preventDefault();
        if (!button) return;

        setBusy(button, true);

        // timestamp (server expects "YYYY-MM-DD HH:mm:ss")
        var ts = new Date().toISOString().slice(0, 19).replace('T', ' ');

        // geolocation (REQUIRED for check-in by your geofence module)
        var geo = await getPos();
        if (isCheckIn && !geo) {
            setBusy(button, false);
            alert('Location access is required to check in. Please allow location and try again.');
            return;
        }

        var fd = new FormData();
        if (isCheckIn) fd.append('check_in', ts);
        else fd.append('check_out', ts);

        if (geo) {
            fd.append('lat', String(geo.lat));
            fd.append('lng', String(geo.lng));
        }

        $.ajax({
            url: '/portal/add_attendance',
            type: 'POST',
            data: fd,
            processData: false,
            contentType: false,
            dataType: 'json',
            success: function (response) {
                if (response && response.success) {
                    // toggle UI text
                    if (isCheckIn) setBtnText('Click to Check Out');
                    else setBtnText('Click to Check In');

                    isCheckIn = !isCheckIn;
                    // refresh to update any counters/cards
                    window.location.reload();
                } else {
                    var msg = (response && response.message) || 'Failed to record attendance';
                    alert(msg);
                }
            },
            error: function (xhr) {
                // try to show server message (e.g., geofence violations)
                var msg = 'An error occurred while recording attendance';
                try {
                    var j = JSON.parse(xhr && xhr.responseText);
                    if (j && j.message) msg = j.message;
                } catch (_) {}
                alert(msg);
            },
            complete: function () {
                setBusy(button, false);
            }
        });
    }

    // wire up
    if (button) {
        button.addEventListener('click', onButtonClick);
        updateButtonStatus();
    }
});
