// odoo.define('hr_attendance_base.kiosk_mode', function(require) {
// "use strict";

// var core = require('web.core');
// var KioskModeConfirm = require('hr_attendance.kiosk_confirm');
// var config = require('web.config');

// var QWeb = core.qweb;


// var BaseKioskModeConfirm = KioskModeConfirm.include({
//     events: _.extend({}, KioskModeConfirm.prototype.events, {
//         "click .o_hr_attendance_sign_in_out_icon": _.debounce(function () {
//             this.update_attendance();
//         }, 200, true),
//     }),


//     update_attendance: function () {
//         var self = this;
//         var token = window.localStorage.getItem('token');
//         self.state_read = $.Deferred();
//         self.state_save = $.Deferred();

//         if (Object.keys(self.data).includes("geo_enable")){
//             self.parse_data_geo();
//             self.geolocation();
//         }
//         if (Object.keys(self.data).includes("webcam_enable"))
//             self.parse_data_webcam();
//         if (Object.keys(self.data).includes("ip_enable"))
//             self.parse_data_ip();
//         if (Object.keys(self.data).includes("token_enable"))
//             self.parse_data_token();
//         if (Object.keys(self.data).includes("face_recognition_enable"))
//             self.parse_data_face_recognition();

//         if (Object.keys(self.data).includes("geospatial_enable"))
//             self.parse_data_geospatial();
//         else
//             self.geo_coords.resolve();

//         console.log(this.employee)
//         console.log(this.kiosk)
//         console.log(this.employee_id)

//         self.geo_coords.then(result =>{
//             this._rpc({
//                 route: '/hr_attendance_base',
//                 params: {
//                     token: token,
//                     employee: {id: this.employee_id},
//                     employee_from_kiosk: this.kiosk
//                 },
//             }).then(function(data) {

//                 self.data = data;
//                 self.state_read.resolve();
//                 self.state_save.then(function(data) {
//                     console.log('TUTUTUT')
//                     if (self.webcam_live){
//                         console.log("webcam_live");
//                         Webcam.snap(function(data_uri) {
//                             self.webcam_access = true;
//                             // base64 data
//                             self.webcam_snapshot = data_uri.split(',')[1];
//                             if (self.check_access())
//                                 self.send_data();
//                         });
//                     }
//                     else{
//                         if (self.check_access())
//                             self.send_data();
//                     }
//                 });
//             });
//         });
//     },
//     check_access: function() {
//         var self = this;

//         if ((!self.ip_access && self.ip_enable) || (!self.token_access && self.token_enable)
//             || (!self.geo_access && self.geo_enable) || (!self.webcam_access && self.webcam_enable)
//             || (!self.face_recognition_access && self.face_recognition_enable)){
//             Swal.fire({
//               title: 'Access denied',
//               text: "One of access point is not completed",
//               icon: 'error',
//               confirmButtonColor: '#3085d6',
//               confirmButtonText: 'Ok'
//             });
//             return false;
//         }

//         return true;
//     },

//     send_data: function() {
//         var self = this, geo_str = null;

//         if (self.latitude && self.longitude)
//             var geo_str = self.latitude.toString() + " " + self.longitude.toString();

//         var access_allowed = QWeb.render("HrAttendanceAccessAllowed", {widget: self});
//         var access_denied = QWeb.render("HrAttendanceAccessDenied", {widget: self});
//         var access_allowed_disable = QWeb.render("HrAttendanceAccessAllowedDisable", {widget: self});
//         var access_denied_disable = QWeb.render("HrAttendanceAccessDeniedDisable", {widget: self});
        
//         var accesses = {};
//         if (self.ip_access !== undefined) 
//             accesses['ip_access'] = {'access': self.ip_access, 'enable': self.ip_enable};
//         if (self.token_access !== undefined) 
//             accesses['token_access'] = {'access': self.token_access, 'enable': self.token_enable};
//         if (self.geo_access !== undefined) 
//             accesses['geo_access'] = {'access': self.geo_access, 'enable': self.geo_enable};
//         if (self.webcam_access !== undefined) 
//             accesses['webcam_access'] = {'access': self.webcam_access, 'enable': self.webcam_enable};
//         if (self.face_recognition_access !== undefined) 
//             accesses['face_recognition_access'] = {'access': self.face_recognition_access, 'enable': self.face_recognition_enable};

//         self._rpc({
//             model: 'hr.employee',
//             method: 'attendance_manual',
//             args: [[this.employee_id], this.next_action],
//            // args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
//             context: {
//                     'ismobile': config.device.isMobile,
//                     'ip': self.ip,
//                     'ip_id': self.ip_id,
//                     'geo': geo_str,
//                     'token': self.token_id,
//                     'user_agent_html': self.user_agent_html,
//                     'webcam': self.webcam_snapshot,
//                     'face_recognition_image': self.face_recognition_image,
//                     'access_allowed': access_allowed,
//                     'access_denied': access_denied,
//                     'access_allowed_disable': access_allowed_disable,
//                     'access_denied_disable': access_denied_disable,
//                     'accesses': accesses
//                 },
//         })
//         .then(function(result) {
//                     if (result.action) {
//                         self.do_action(result.action);
//                     } else if (result.warning) {
//                         self.do_warn(result.warning);
//                         self.$('.o_hr_attendance_PINbox').val('');
//                         setTimeout( function() { self.$('.o_hr_attendance_pin_pad_button_ok').removeAttr("disabled"); }, 500);
//                     }
//         });
//     },

//     init: function (parent, options) {

//         // state when end request /hr_attendance_base
//         this.state_read = $.Deferred();
//         // after read, we write data to memory 
//         this.state_save = $.Deferred();
//         // after save we render page template
//         this.state_render = $.Deferred();
//         // after render we bind click action on template and add map
//         this._super(parent, options);
//     },

//     start: function() {
//         var self = this;
//         var _super = this._super.bind(this);
//         var token = window.localStorage.getItem('token');
//         if (!Object.keys(self).includes("geo_coords")){
//             this.geo_coords = $.Deferred();
//             this.geo_coords.resolve();
//         }

//         this.geo_coords.then(()=>{
//             this._rpc({
//                 route: '/hr_attendance_base',
//                 params: {
//                     token: token,
//                     employee: this.employee,
//                     employee_from_kiosk: this.kiosk
//                 },
//             }).then(function(data) {
//                 self.data = data;
//                 self.state_read.resolve();
//                 self.state_save.then(function(data1) {
//                     return $.when(_super.apply(self,arguments)).then(function(data2,data3) {
//                         // do timeout 200 ms for wait render qweb template in parent
//                         // or do redefine all parent
//                         //self.renderElement();
//                         setTimeout(function tick() {
//                             self.state_render.resolve(data2);
//                         }, 200);
//                     });
//                 });
//             });
//         });
//         return self.state_render;
//     },
// });
// });
