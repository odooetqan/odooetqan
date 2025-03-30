'use strict';
odoo.define('portal_attendance_artx.attendance', [], function (require) {

    require('web.dom_ready');
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    // Use native JavaScript to select the button element
    var button = document.getElementById("attendanceBtn");
    var isCheckIn = true;  // Initialize as true (assuming default is check-in)

    var updateButtonStatus = function() {
        // Fetch the current attendance status when the page loads
        $.ajax({
            url: '/portal/get_attendance_status',
            type: 'GET',
            success: function(response) {

                // No need to parse, response is already a JavaScript object
                if (response.success) {
                    if (response.message === 'Currently checked in') {
                        $('#btnText').text('Click to Check Out');
                        isCheckIn = false;  // Set to false, meaning next action will be check-out
                    } else {
                        $('#btnText').text('Click to Check In');
                        isCheckIn = true;  // Set to true, meaning next action will be check-in
                    }
                } else {
                    // If not checked in, default to check-in
                    $('#btnText').text('Click to Check In');
                    isCheckIn = true;
                }
            },
            error: function(error) {
                console.log('Error fetching attendance status:', error);
                $('#btnText').text('Click to Check In');
                isCheckIn = true;  // If there's an error, assume next action is check-in
            }
        });
    };

    var _onButton = function(e) {
        const currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ');

        let formData = new FormData();
        if (isCheckIn) {
            formData.append('check_in', currentTime);  // Append check-in time
        } else {
            formData.append('check_out', currentTime);  // Append check-out time
        }

        $.ajax({
            url: '/portal/add_attendance',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                // No need to parse, response is already a JavaScript object
                if (response.success) {
                    if (isCheckIn) {
                        $('#btnText').text('Click to Check Out');
                    } else {
                        $('#btnText').text('Click to Check In');
                    }
                    isCheckIn = !isCheckIn;  // Toggle the check-in/check-out state
                } else {
                    alert('Failed to record attendance: ' + response.message);
                }
            },
            error: function(error) {
                alert('An error occurred while recording attendance');
                console.log(error);
            }
        });
    };

    // Check if the button exists before attaching the event listener
    if (button) {
        button.addEventListener('click', _onButton);
        updateButtonStatus();  // Check the current status when the page loads
    }
});
