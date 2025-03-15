import math
from datetime import datetime

import pytz
from odoo import models, fields, api, tools, _
from odoo.http import request
import base64
import logging
import time
from odoo.exceptions import UserError

try:
    import face_recognition as fr
except ImportError:
    raise ImportError('''This module needs face_recognition to could recognise face images. Please install face_recognition 
                      and other lib before on your system. (sudo pip install install cmake)
                                                           (sudo pip install dlib)
                                                           (sudo pip install face-recognition)
                                                            ''')

import numpy as np
try :
    import cv2 as cv
except ImportError:
    raise ImportError('This module needs opencv to could open and edit images. Please install opencv on your system. (sudo pip install opencv-python)')
try:
    from geopy.geocoders import Nominatim
except ImportError:
    raise ImportError('This module needs geopy to could work with location. Please install geopy on your system. (sudo pip install geopy)')


_logger = logging.getLogger(__name__)
class HRAttendance(models.Model):
    _inherit = "hr.attendance"
    location = fields.Selection([('inside_company', 'Inside Company'), ('outside_company', 'Outside Company')])



    '''
    this fuction called from js receve list of encoded images and long,lat cordenates
    '''
    @api.model
    def action_attend_js(self,base64_list,latitude,longitude):
        match = []
        _logger.log(25,"Starting execute attend js with image... ")
        encodeed_cupture_img = self.findVedioEncoding(base64_list)
        user_image_string = self.env.user.image_1920
        if not user_image_string:
                raise UserError(_("user image not found"))
        encoded_user_img = self.findUserIMGEncodings(user_image_string)
        _logger.log(25, "longitude... %s" % (longitude))
        for encodeFace in encodeed_cupture_img:
            matches = fr.compare_faces(encoded_user_img, encodeFace)
            for m in matches:
                match.append(m)
        _logger.log(25,"is Match... %s" % (match))
        if match:
            if any(m == True for m in match):
                return self.makeAttendence(latitude,longitude)
            else:
                return False
        else:
            return False

    '''
    this function get encoded list of image and return list of encoded faces from each image
    '''
    def findVedioEncoding(self,base64_list):
        # create empty list to store encoded images
        _logger.log(25,"Starting encode vedio image...")
        encodeList = []
        for base64_string in base64_list:
            if not base64_string:
                continue
            # base64_string = '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'

            try:
                # Decode the base64 string into an image
                jpg_original = base64.b64decode(base64_string)
                jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
                img = cv.imdecode(jpg_as_np, flags=1)
            except Exception as e:
                _logger.error(f"Failed to decode image: {e}")
                raise UserError(_("Failed to decode image."))

            # Resize the image for faster processing
            for scale in [1, 0.75, 0.5, 0.25]:
                imgS = cv.resize(img, (0, 0), None, scale, scale)
                # imgS = cv.cvtColor(imgS, cv.COLOR_BGR2RGB)
                # Ensure image is in RGB format
                if len(imgS.shape) == 2:  # Grayscale image
                    imgS = cv.cvtColor(imgS, cv.COLOR_GRAY2RGB)
                elif imgS.shape[2] == 3:  # 3-channel BGR image
                    imgS = cv.cvtColor(imgS, cv.COLOR_BGR2RGB)

                if imgS.dtype != np.uint8:
                    _logger.error("Image is not 8-bit.")
                    raise UserError(_("Image is not 8-bit."))
                
                _logger.log(25, f"Image shape after resizing: {imgS.shape}")

                # Detect face locations
                face_location = fr.face_locations(imgS)
                _logger.log(25, f"Detected face locations: {face_location}")

                if face_location:
                    break  # Stop resizing if faces are found

            if not face_location:
                raise UserError(_("no face detected in this frame."))
                _logger.warning("No face detected in this frame. Skipping...")
                continue

            # Encode the first face found in the image
            face_encoding_lis = fr.face_encodings(imgS, face_location)
            if not face_encoding_lis:
                raise UserError(_("no face location detected in this frame."))
            if face_encoding_lis:
                _logger.log(25, "Face encoding started...")
                encode = face_encoding_lis[0]  # Use the first detected face
                encodeList.append(encode)

        if not encodeList:
                raise UserError(_("no encodeList in this frame."))
        _logger.log(25, "Finished encoding video images.")
        return encodeList

        #     jpg_original = base64.b64decode(base64_string)
        #     _logger.log(25, "JPJ B64 IMG... ")
        #     jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
        #     img = cv.imdecode(jpg_as_np, flags=1)
        #     imgS = cv.resize(img, (0, 0), None, 0.25, 0.25)
        #     # convert resized img to rgb
        #     imgS = cv.cvtColor(imgS, cv.COLOR_BGR2RGB)
        #     # find location or border of face in resized image
        #     face_location = fr.face_locations(imgS)
        #     _logger.log(25, "CV2 IMG...")
        #     face_encoding_lis = fr.face_encodings(imgS, face_location)
        #     # encode image
        #     if face_encoding_lis:
        #         _logger.log(25,"Face encoding start... ")
        #         encode = face_encoding_lis[0]  # we use index 0 as image may have more than one face so we need first face
        #         encodeList.append(encode)
        # return encodeList

    '''
    this function return encoded face from user profile image
    '''
    def findUserIMGEncodings(self,image_string):
        # create empty list to store encoded images
        encodeList = []
        _logger.log(25,"Start encoding profile image encoding start... ")
        jpg_original = base64.b64decode(image_string)
        jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
        img = cv.imdecode(jpg_as_np, flags=1)
        imgS = cv.resize(img, (0, 0), None, 0.25, 0.25)
        # convert resized img to rgb
        imgS = cv.cvtColor(imgS, cv.COLOR_BGR2RGB)
        # find location or border of face in resized image
        faceCurFrame = fr.face_locations(imgS)
        encodesCurFrame = fr.face_encodings(imgS, faceCurFrame)
        return encodesCurFrame
    '''
    date:19/3/2023
    autor:m.eldeeb
    task code: 005
    '''
    def makeAttendence(self,latitude,longitude):
        _logger.log(25,"Start attend User... ")

        company_long = float(self.env['ir.config_parameter'].sudo().get_param('nthub_hr_cam_attendance.long'))
        company_lat = float(self.env['ir.config_parameter'].sudo().get_param('nthub_hr_cam_attendance.lat'))
        max_distance = float(self.env['ir.config_parameter'].sudo().get_param('nthub_hr_cam_attendance.max_distance'))

        ch_s = fields.datetime.now().replace(hour=3, minute=0, second=0, microsecond=0)
        ch_e = fields.datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        attendance = self.env['hr.attendance'].sudo()

        record = attendance.search([('employee_id','=',self.env.user.employee_id.id),('check_in','>',ch_s),('check_in','<',ch_e)])
        distance_to_company_m = self.calculate_distance(latitude, longitude, company_lat, company_long)
        if distance_to_company_m <= max_distance:
            location = 'inside_company'
        else:
            location = 'outside_company'

        d = self.deside_check_in_or_out(record)
        if d == 'checkin':
            return self.action_checkin(latitude,longitude,location)
        elif d == 'checkout':
            return self.action_checkout(latitude,longitude,record)
        elif d == 'check_in_out':
            return self.action_checkin_checkout(latitude,longitude,location)



    # def get_geo_location(self):
    #     latitude  = request.session['geoip'].get('latitude') or 0.0,
    #     longitude = request.session['geoip'].get('longitude') or 0.0,
    #     return latitude,longitude
    def get_city_from_lat_long(self,latitude,longitude):
        # initialize Nominatim API
        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.reverse(str(latitude) + "," + str(longitude))
        address = location.raw['address']
        city = address.get('city', '')
        if city == 'cairo' or city == 'القاهرة':
           return 'inside_cairo'
        else:
            return 'outside_cairo'
        # state = address.get('state', '')
        # country = address.get('country', '')
        # code = address.get('country_code')
        # zipcode = address.get('postcode')

    def deside_check_in_or_out(self,record):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        if not record:
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
            # utc_today = pytz.utc.localize(datetime.now()).astimezone(user_tz)
            # offset = utc_today.utcoffset().seconds / 3600
            current_date = pytz.utc.localize(datetime.now()).astimezone(user_tz).replace(tzinfo=None)

            working_from = float(get_param('nthub_hr_cam_attendance.working_from'))
            working_to = float(get_param('nthub_hr_cam_attendance.working_to'))
            behavior = get_param('nthub_hr_cam_attendance.behavior')
            if current_date.hour > working_from and current_date.hour < working_to:
                return 'checkin'
            elif current_date.hour > working_to:
                if behavior == 'none':
                    return 'none'
                else:
                    return 'check_in_out'
            else:
                return 'checkin'

        else:
            return 'checkout'

    def action_checkin(self,latitude,longitude,location):
        vals = {
            'employee_id': self.env.user.employee_id.id,
            'check_in': fields.datetime.now(),
            'location': location,
            'in_latitude': str(latitude),
            'in_longitude': str(longitude),
        }
        try:
            self.env['hr.attendance'].sudo().create(vals)
            _logger.log(25, "Checkin successfully User... ")
            return True
        except Exception as e:
            _logger.log(25, "error checkin... ")
            return False

    def action_checkout(self,latitude,longitude,record):
        vals = {
            'check_out': fields.datetime.now(),
            'out_latitude': str(latitude),
            'out_longitude': str(longitude),
        }
        try:
            record.sudo().update(vals)
            _logger.log(25, "Checkout successfully User... ")
            return True
        except Exception as e:
            _logger.log(25, "error checkout... ")
            return False

    def action_checkin_checkout(self,latitude,longitude,location):
        vals = {
            'employee_id': self.env.user.employee_id.id,
            'check_in': fields.datetime.now(),
            'check_out': fields.datetime.now(),
            'location':location,
            'in_latitude': str(latitude),
            'in_longitude': str(longitude),
            'out_latitude': str(latitude),
            'out_longitude': str(longitude),
        }
        try:
            self.env['hr.attendance'].sudo().create(vals)
            _logger.log(25, "Checkin successfully User... ")
            return True
        except Exception as e:
            _logger.log(25, "error checkin... ")
            return False

    # return distance between user and company in Metres
    def calculate_distance(self,lat1, lon1, lat2, lon2):
        # Radius of the Earth in kilometers
        R = 6371

        # Convert latitude and longitude to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Calculate the differences between coordinates
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine formula
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Calculate the distance in Meter
        distance = R * c * 1000

        return distance


