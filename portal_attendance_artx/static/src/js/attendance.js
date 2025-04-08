'use strict';

odoo.define('portal_attendance_artx.attendance', function (require) {
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.AttendanceButton = publicWidget.Widget.extend({
        selector: '#attendanceBtn',
        events: {
            'click': '_onButtonClick',
        },

        /**
         * Start function that runs on page load
         */
        start: function () {
            this._super.apply(this, arguments);
            this.updateButtonStatus();
        },

        /**
         * Fetch the current attendance status and update the button text accordingly
         */
        updateButtonStatus: function () {
            var self = this;
            ajax.jsonRpc('/portal/get_attendance_status', 'call', {})
                .then(function (response) {
                    if (response.success) {
                        if (response.message === 'Currently checked in') {
                            $('#btnText').text('Click to Check Out');
                            self.isCheckIn = false; // Set to false, meaning next action will be check-out
                        } else {
                            $('#btnText').text('Click to Check In');
                            self.isCheckIn = true; // Set to true, meaning next action will be check-in
                        }
                    } else {
                        $('#btnText').text('Click to Check In');
                        self.isCheckIn = true;
                    }
                }).fail(function () {
                    console.error('Error fetching attendance status');
                    $('#btnText').text('Click to Check In');
                    self.isCheckIn = true; // Assume check-in if there's an error
                });
        },

        /**
         * Handles the click event for check-in/check-out
         */
        _onButtonClick: function (event) {
            var self = this;
            var currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ');

            var requestData = {};
            if (this.isCheckIn) {
                requestData['check_in'] = currentTime;
            } else {
                requestData['check_out'] = currentTime;
            }

            // Disable button to prevent multiple clicks
            $('#attendanceBtn').prop('disabled', true);

            ajax.jsonRpc('/portal/add_attendance', 'call', requestData)
                .then(function (response) {
                    if (response.success) {
                        $('#btnText').text(self.isCheckIn ? 'Click to Check Out' : 'Click to Check In');
                        self.isCheckIn = !self.isCheckIn; // Toggle the check-in/check-out state
                    } else {
                        alert('Failed to record attendance: ' + response.message);
                    }
                }).fail(function () {
                    alert('An error occurred while recording attendance');
                }).always(function () {
                    // Re-enable button after request completion
                    $('#attendanceBtn').prop('disabled', false);
                });
        }
    });

    publicWidget.registry.AttendanceButton;
});
