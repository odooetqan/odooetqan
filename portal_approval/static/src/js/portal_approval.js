odoo.define('portal_attendance_artx.portal_approval', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.PortalApprovalForm = publicWidget.Widget.extend({
        selector: '#category_id',
        events: {
            'change': '_onCategoryChange',
        },

        _onCategoryChange: function (ev) {
            var categoryId = $(ev.target).val();
            if (!categoryId) {
                $('#dynamic_fields').empty();
                return;
            }

            $.ajax({
                // url: '/my/approval/get_fields',
                url: '/my/approval/get_dynamic_fields',
                data: {category_id: categoryId},
                success: function (data) {
                    $('#dynamic_fields').html(data);
                }
            });
        },
    });
});
