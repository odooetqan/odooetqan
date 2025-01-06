/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('itsys_real_estate.init', function (require) {
    "use strict";
    var rpc = require('web.rpc');
    //default key
    var default_key = 'AIzaSyCLe7MRT7q5Rkd3kuyOoNSLb7wL-bk0Ip4';

    rpc.query({
        model: 'gmap.config',
        method: 'get_key_api',
        args: []
    }).then(function (key) {
        if (!key) {
            key = default_key;
        }
        $.getScript('http://maps.googleapis.com/maps/api/js?key=' + key + '&libraries=places&sensor=true');
    });
});