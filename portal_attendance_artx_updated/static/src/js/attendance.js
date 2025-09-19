// odoo.define('portal_attendance_artx_updated.attendance', function (require) {
'use strict';
var publicWidget = require('web.public.widget');
var ajax = require('web.ajax');

publicWidget.registry.AttendanceButton = publicWidget.Widget.extend({
  selector: '#attendanceBtn',
  events: { click: '_onClick' },
  start() { this.isCheckIn = true; return this._super(...arguments); },
  _onClick() {
    const self = this;
    navigator.geolocation.getCurrentPosition(function (pos) {
      const now = new Date().toISOString().slice(0,19).replace('T',' ');
      const payload = self.isCheckIn ? {check_in: now} : {check_out: now};
      payload.lat = pos.coords.latitude;
      payload.lng = pos.coords.longitude;
      ajax.jsonRpc('/portal/add_attendance', 'call', payload).then(function (res) {
        if (res.success) self.isCheckIn = !self.isCheckIn;
        alert(res.message || 'Done');
      });
    }, function () { alert('Please allow location.'); });
  },
});
// });
