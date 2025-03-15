/** @odoo-module **/

    import { registry } from "@web/core/registry";
    import { jsonrpc } from "@web/core/network/rpc_service";
    import { Dialog } from "@web/core/dialog/dialog";
    import { _t } from "@web/core/l10n/translation";


    var img_data = false
    var img_data_base64 = false
    var image_list = []
    var longitude = 0
    var latitude = 0
    function saveAndClose() {

        for (var i = 0; i < 3;i++) {
            Webcam.snap(function (data) {
            img_data = data;

            // Display Snap besides Live WebCam Preview
            img_data_base64 = img_data.split(",")[1];

            });
            image_list.push(img_data_base64)
        }
        Webcam.reset();
        $("#live_webcam").html('<img src="' + img_data + '"/>');
        getLocation();

    };

    function actionAttend(image_list,latitude,longitude){
        jsonrpc('/web/dataset/call_kw/hr.attendance/action_attend_js' ,{
                model: 'hr.attendance',
                method: 'action_attend_js',
                args: [image_list,latitude,longitude],
                kwargs: {}
        }).then((result,self) => {
                if (result){
                $('#info_message_attendance_success').css('display','block');
                $('.container-cam').css('display','none');
                }
                else {
                    $('#info_message_attendance_warning').css('display','block');
                    $('#live_webcam').css('display','none');
                    $("#info_message_attendance_warning").delay(3000).fadeOut(500);

                }
            })
    };

    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function (position){
                latitude = position.coords.latitude ;
                longitude =  position.coords.longitude;
                console.log(latitude+'  long ..'+longitude);
                actionAttend(image_list,latitude,longitude)
//                return [latitude,longitude];
            });
        }
        else {
            console.log("Geolocation is not supported by this browser.");
//            return [latitude,longitude];

        }
//        return [latitude,longitude];
    };

    // this function used to catch check in/out button to make all processing
    $('.btn-link-attend').on('click', function (e) {
        var self = this,
        img_data = false;
        let w = document.getElementById("live_webcam").offsetWidth
        let h = document.getElementById("live_webcam").offsetHeight
        document.getElementById("live_webcam").style.display = 'block';
        console.log('WWWWWWW',w,h)
        let screen_width = screen.width;
        console.log(screen_width)
        Webcam.set({
                width: w,
                height: h,
                dest_width: w,
                dest_height: h,
                image_format: "jpeg",
                jpeg_quality: 95,
                force_flash: false,
                fps: 60,
                swfURL: "/web_widget_image_webcam/static/src/lib/webcam.swf",
            });
        Webcam.attach( '#live_webcam' );
        console.log('WWWWWWW',w)
        setTimeout(saveAndClose, 5000);

    });

