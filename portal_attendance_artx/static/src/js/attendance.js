odoo.define('portal_attendance_artx.attendance', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    var AttendanceButton = publicWidget.Widget.extend({
        selector: '#attendanceBtn',
        events: {
            'click': '_onButtonClick',
        },

        start: function () {
            this._super.apply(this, arguments);
            this.updateButtonStatus();
        },

        updateButtonStatus: function () {
            var self = this;
            ajax.jsonRpc('/portal/get_attendance_status', 'call', {})
                .then(function (response) {
                    if (response.success && response.message === 'Currently checked in') {
                        $('#btnText').text('Click to Check Out');
                        self.isCheckIn = false;
                    } else {
                        $('#btnText').text('Click to Check In');
                        self.isCheckIn = true;
                    }
                }).fail(function () {
                    console.error('Error fetching attendance status');
                    $('#btnText').text('Click to Check In');
                    self.isCheckIn = true;
                });
        },

        _onButtonClick: function () {
            var self = this;
            var currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ');
            var requestData = this.isCheckIn
                ? { check_in: currentTime }
                : { check_out: currentTime };

            $('#attendanceBtn').prop('disabled', true);

            ajax.jsonRpc('/portal/add_attendance', 'call', requestData)
                .then(function (response) {
                    if (response.success) {
                        $('#btnText').text(self.isCheckIn ? 'Click to Check Out' : 'Click to Check In');
                        self.isCheckIn = !self.isCheckIn;
                    } else {
                        alert('Failed: ' + response.message);
                    }
                }).fail(function () {
                    alert('Error occurred while recording attendance.');
                }).always(function () {
                    $('#attendanceBtn').prop('disabled', false);
                });
        }
    });

    publicWidget.registry.AttendanceButton = AttendanceButton;
    return AttendanceButton;
});
