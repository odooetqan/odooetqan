class PortalDiscount(http.Controller):

    @http.route(['/my/discounts'], type='http', auth='user', website=True)
    def portal_my_discounts(self, **kwargs):
        employee = request.env.user.employee_id
        discounts = request.env['hr.discount'].sudo().search([('employee_id', '=', employee.id)])

        return request.render('hr_attendance_discount.portal_my_discounts', {
            'discounts': discounts
        })
