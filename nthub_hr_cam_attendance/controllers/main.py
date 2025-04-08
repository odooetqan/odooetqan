# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import base64
import logging
import time

from odoo import fields, http, _
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

import face_recognition as fr
import numpy as np
import cv2 as cv

_logger = logging.getLogger(__name__)

class AttendancePortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'attendance_count' in counters:
            attendance_count = request.env['hr.attendance'].search_count([])
            values['attendance_count'] = attendance_count
        return values


    """
    controller used to open template that have button called [Check in/out] that open web cam to match user face capture with it's image profile
    and if ok display info success message that user has successfully checked in
    if not recognise then display warning message
    """
    @http.route(['/my/attendance/checkin'], type='http', auth="user", website=True)
    def portal_attendance(self, **kw):
        return request.render("nthub_hr_cam_attendance.attendance_check_out_done_template")
    @http.route(['/my/attendance'], type='http', auth="user", website=True)
    def portal_check_in(self, **kw):
        cap = cv.VideoCapture('http://192.168.10.241:8080')
        cv.namedWindow("ATTENDANCE")
        if not cap.isOpened():
            exit()
        image_string = request.env.user.image_1920
        encodeListKnown = self.findEncodings(image_string)
        timeout = time.time() + 10 # 30 seconds from now
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            imgS = cv.resize(frame, (0, 0), None, 0.25, 0.25)
            # convert resized img to rgb
            imgS = cv.cvtColor(imgS, cv.COLOR_BGR2RGB)
            # find location or border of face in resized image
            faceCurFrame = fr.face_locations(imgS)

            # encode capture Image
            encodesCurFrame = fr.face_encodings(imgS, faceCurFrame)
            # cv.createButton("Back", self.makeAttendence(), None, cv.QT_PUSH_BUTTON, 1)
            # if frame is read correctly ret is True
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break
            for encodeFace, faceLocation in zip(encodesCurFrame, faceCurFrame):
                matches = fr.compare_faces(encodeListKnown, encodeFace)
                print('matches',matches)
                faceDis = fr.face_distance(encodeListKnown,encodeFace)  # find ratio of defrence between faces when the value is low images become same
                # now we want to get the index of smallist distance image
                matchIndex = np.argmin(faceDis)
                # now we knew the name of the unkown person
                if matches[matchIndex]:
                    print(matches)
                    name = request.env.user.name.upper()
                    y1, x2, y2, x1 = faceLocation
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4  # as we scale it for quarter before
                    cv.rectangle(frame, (x1, y2 - 53), (x2, y2), (255, 0, 255), cv.FILLED)
                    cv.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
                    cv.putText(frame, name, (x1 + 6, y2 - 6), cv.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                    test = 0
            if time.time() > timeout:
                break



            # Our operations on the frame come here
            # Display the resulting frame
            cv.imshow('webcam',frame)
            if cv.waitKey(1) == ord('q'):
                break
        # When everything done, release the capture
        cap.release()
        cv.destroyAllWindows()
        #make attendance
        if self.makeAttendence():
            return request.render("nthub_hr_cam_attendance.attendance_done_template")
        else:
            return request.render("nthub_hr_cam_attendance.attendance_fail_template")

    # function to encode all images
    def findEncodings(self,image_string):
        # create empty list to store encoded images
        encodeList = []
        jpg_original = base64.b64decode(image_string)
        jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
        img = cv.imdecode(jpg_as_np, flags=1)
        # first convert images to rgb
        # img = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        # encode image
        encode = fr.face_encodings(img)[0]  # we use index 0 as image may have more than one face so we need first face
        # append encode image to encodeList
        encodeList.append(encode)
        return encodeList

    # ___________________________________________________
    # function to open attendance  table and store employee name and time
    def makeAttendence(self):
        user = request.env.user
        ch_s = fields.datetime.now().replace(hour=3, minute=0, second=0, microsecond=0)
        ch_e = fields.datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        attendance = request.env['hr.attendance'].sudo()
        record = attendance.search([('employee_id','=',user.employee_id.id),('check_in','>',ch_s),('check_in','<',ch_e)])
        if not record:
            vals = {
                'employee_id':user.employee_id.id,
                'check_in': fields.datetime.now(),
            }
            try:
                attendance.create(vals)
                return True
            except Exception as e:
                return False
        else:
            vals = {
                'check_out': fields.datetime.now(),
            }
            try:
                record.sudo().update(vals)
                return True
            except Exception as e:
                return False
    # ___________________________________________________


