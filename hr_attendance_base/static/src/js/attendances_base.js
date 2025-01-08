odoo.define('hr_attendance_base.base_attendances', function (require) {
"use strict";

var core = require('web.core');
var MyAttendances = require('hr_attendance.my_attendances');
var QWeb = core.qweb;
var config = require('web.config');
var field_utils = require('web.field_utils');

var BaseAttendances = MyAttendances.include({
    //template: 'HrAttendanceMyMainMenu',
    init: function() {
        // state when end request /hr_attendance_base
        this.state_read = $.Deferred();
        // after read, we write data to memory 
        this.state_save = $.Deferred();
        // after save we render page template
        this.state_render = $.Deferred();
        // after render we bind click action on template and add map
        this._super.apply(this, arguments);
    },

    willStart: function () {
        return this._super.apply(this, arguments).then(result =>{
            // if kiosk mode enable, recognition already done and emloyee exist
            if (this.searchModelConfig &&
                this.searchModelConfig.context &&
                this.searchModelConfig.context.employee){

                this.kiosk = this.searchModelConfig.context.face_recognition_force;
                this.face_recognition_auto = this.searchModelConfig.context.face_recognition_auto;
                this.webcam_snapshot = this.searchModelConfig.context.webcam_snapshot;
                this.face_recognition_image = this.searchModelConfig.context.face_recognition_image;
                this.employee = this.searchModelConfig.context.employee;
                this.hours_today = field_utils.format.float_time(this.employee.hours_today);
            }
        })
    },

    start: function() {
        var self = this;
        var _super = this._super.bind(this);
        var token = window.localStorage.getItem('token');
        if (!Object.keys(self).includes("geo_coords")){
            this.geo_coords = $.Deferred();
            this.geo_coords.resolve();
        }

        this.geo_coords.then(()=>{
            this._rpc({
                route: '/hr_attendance_base',
                params: {
                    token: token,
                    employee: this.employee,
                    employee_from_kiosk: this.kiosk,
                    latitude: self.latitude,
                    longitude: self.longitude
                },
            }).then((data) =>{
                self.data = data;
                self.state_read.resolve();

                if (!data.length){
                    self.state_save.resolve();
                }
                self.state_save.then(function(data1) {


                    console.log(self);
                    if (self.kiosk){     
                        //self.$el.html(QWeb.render("HrAttendanceMyMainMenu", {widget: self}));
                        self.renderElement();
                        self.state_render.resolve(data1);
                        //return $.when(_super.apply(self,arguments));
                    }
                    else{
                        //self.renderElement();
                        return $.when(_super.apply(self,arguments)).then(function(data2,data3) {
                            // do timeout 200 ms for wait render qweb template in parent
                            // or do redefine all parent
                            self.renderElement();
                            //setTimeout(function tick() {
                                self.state_render.resolve(data2);
                                // auto click attendance if settings true
                                if (self.face_recognition_auto)
                                    self.update_attendance();
                           // }, 5000);
                        });
                    }
                });
            });
        });
        return self.state_render;
    },
    update_attendance: function () {
        var self = this;
        var token = window.localStorage.getItem('token');
        self.state_read = $.Deferred();
        self.state_save = $.Deferred();

        if (Object.keys(self.data).includes("geo_enable")){
            self.parse_data_geo();
            self.geolocation();
        }
        if (Object.keys(self.data).includes("webcam_enable"))
            self.parse_data_webcam();
        if (Object.keys(self.data).includes("ip_enable"))
            self.parse_data_ip();
        if (Object.keys(self.data).includes("token_enable"))
            self.parse_data_token();
        if (Object.keys(self.data).includes("face_recognition_enable"))
            self.parse_data_face_recognition();

        if (Object.keys(self.data).includes("geospatial_enable"))
            self.parse_data_geospatial();
        else
            self.geo_coords.resolve();

        self.geo_coords.then(result =>{
            this._rpc({
                route: '/hr_attendance_base',
                params: {
                    token: token,
                    employee: this.employee,
                    employee_from_kiosk: this.kiosk,
                    latitude: self.latitude,
                    longitude: self.longitude
                },
            }).then(function(data) {
                self.data = data;
                self.state_read.resolve();
                if (!data.length){
                    self.state_save.resolve();
                }
                self.state_save.then(function(data) {
                    if (self.webcam_live){
                        console.log("webcam_live");
                        Webcam.snap(function(data_uri) {
                            self.webcam_access = true;
                            // base64 data
                            self.webcam_snapshot = data_uri.split(',')[1];
                            if (self.check_access())
                                self.send_data();
                        });
                    }
                    else{
                        if (self.check_access())
                            self.send_data();
                    }
                });
            });
        });
    },
    check_access: function() {
        var self = this;

        if ((!self.ip_access && self.ip_enable) || (!self.token_access && self.token_enable)
            || (!self.geo_access && self.geo_enable) || (!self.webcam_access && self.webcam_enable)
            || (!self.face_recognition_access && self.face_recognition_enable)
            || (!self.geospatial_access && self.geospatial_enable)){
            Swal.fire({
              title: 'Access denied',
              text: "One of access point is not completed",
              icon: 'error',
              confirmButtonColor: '#3085d6',
              confirmButtonText: 'Ok'
            });
            return false;
        }

        return true;
    },

    send_data: function() {
        var self = this, geo_str = null;

        if (self.latitude && self.longitude)
            var geo_str = self.latitude.toString() + " " + self.longitude.toString();

        var access_allowed = QWeb.render("HrAttendanceAccessAllowed", {widget: self});
        var access_denied = QWeb.render("HrAttendanceAccessDenied", {widget: self});
        var access_allowed_disable = QWeb.render("HrAttendanceAccessAllowedDisable", {widget: self});
        var access_denied_disable = QWeb.render("HrAttendanceAccessDeniedDisable", {widget: self});
        
        var accesses = {};
        if (self.ip_access !== undefined) 
            accesses['ip_access'] = {'access': self.ip_access, 'enable': self.ip_enable};
        if (self.token_access !== undefined) 
            accesses['token_access'] = {'access': self.token_access, 'enable': self.token_enable};
        if (self.geo_access !== undefined) 
            accesses['geo_access'] = {'access': self.geo_access, 'enable': self.geo_enable};
        if (self.webcam_access !== undefined) 
            accesses['webcam_access'] = {'access': self.webcam_access, 'enable': self.webcam_enable};
        if (self.face_recognition_access !== undefined) 
            accesses['face_recognition_access'] = {'access': self.face_recognition_access, 'enable': self.face_recognition_enable};
        if (self.geospatial_access !== undefined) 
            accesses['geospatial_access'] = {'access': self.geospatial_access, 'enable': self.geospatial_enable};

        self._rpc({
            model: 'hr.employee',
            method: 'attendance_manual',
            args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
            context: {
                    'ismobile': config.device.isMobile,
                    'ip': self.ip,
                    'ip_id': self.ip_id,
                    'geospatial_id': self.geospatial_id,
                    'geo': geo_str,
                    'token': self.token_id,
                    'user_agent_html': self.user_agent_html,
                    'webcam': self.webcam_snapshot,
                    'face_recognition_image': self.face_recognition_image,
                    'access_allowed': access_allowed,
                    'access_denied': access_denied,
                    'access_allowed_disable': access_allowed_disable,
                    'access_denied_disable': access_denied_disable,
                    'accesses': accesses,
                    'kiosk_shop_id': self.kiosk_shop_id
                },
        })
        .then(function(result) {
            if (self.kiosk)
                result.action.next_action = 'hr_attendance_kiosk_mode';
            if (result.action) {
                self.do_action(result.action);
            } else if (result.warning) {
                self.do_warn(result.warning);
            }
        });
    }

});
return BaseAttendances;
});
