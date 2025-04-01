// portal_approval/static/src/js/portal_approval.js
console.log("Dynamic approval form JS loaded!");

var _mtm = window._mtm = window._mtm || [];
_mtm.push({'mtm.startTime': (new Date().getTime()), 'event': 'mtm.Start'});
(function() {
  var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
  g.async=true; g.src='https://cdn.matomo.cloud/zabiah-alban.matomo.cloud/container_A7uHuFOC.js'; s.parentNode.insertBefore(g,s);
})();

document.addEventListener("DOMContentLoaded", function () {
    const categorySelect = document.getElementById('category_id');
    const dynamicFieldsContainer = document.getElementById('dynamic_fields_template');

    if (!categorySelect || !dynamicFieldsContainer) return;

    categorySelect.addEventListener('change', async function () {
        const categoryId = this.value;
        if (!categoryId) {
            dynamicFieldsContainer.innerHTML = '';
            return;
        }

        try {
            const response = await fetch('/my/approval/get_dynamic_fields_template', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({ category_id: categoryId })
            });

            const result = await response.json();
            if (result.success && result.html) {
                dynamicFieldsContainer.innerHTML = result.html;
            } else {
                dynamicFieldsContainer.innerHTML = '';
            }
        } catch (err) {
            console.error('Fetch error:', err);
        }
    });
});


// odoo.define('portal_approval.portal_approval', function (require) {
//     'use strict';
//     console.log('Dynamic approval form JS loaded!');

//     document.addEventListener('DOMContentLoaded', function () {
//         const categorySelect = document.getElementById('category_id');
//         const dynamicFieldsContainer = document.getElementById('dynamic_fields_template');

//         if (!categorySelect || !dynamicFieldsContainer) return;

//         categorySelect.addEventListener('change', async function () {
//             const categoryId = this.value;
//             if (!categoryId) {
//                 dynamicFieldsContainer.innerHTML = '';
//                 return;
//             }

//             try {
//                 const response = await fetch('/my/approval/get_dynamic_fields_template', {
//                     method: 'POST',
//                     headers: {
//                         'Content-Type': 'application/x-www-form-urlencoded'
//                     },
//                     body: new URLSearchParams({ category_id: categoryId })
//                 });

//                 const result = await response.json();
//                 if (result.success && result.html) {
//                     dynamicFieldsContainer.innerHTML = result.html;
//                 } else {
//                     console.warn('No dynamic fields returned.');
//                     dynamicFieldsContainer.innerHTML = '';
//                 }
//             } catch (err) {
//                 console.error('Failed to fetch dynamic fields:', err);
//             }
//         });
//     });
// });

// // console.log('Dynamic approval form JS loaded!');

// // document.addEventListener('DOMContentLoaded', function () {
// //     const categorySelect = document.getElementById('category_id');
// //     const dynamicFieldsContainer = document.getElementById('dynamic_fields_template');

// //     if (!categorySelect || !dynamicFieldsContainer) return;

// //     categorySelect.addEventListener('change', async function () {
// //         const categoryId = this.value;
// //         if (!categoryId) {
// //             dynamicFieldsContainer.innerHTML = '';
// //             return;
// //         }

// //         try {
// //             const response = await fetch('/my/approval/get_dynamic_fields_template', {
// //                 method: 'POST',
// //                 headers: {
// //                     'Content-Type': 'application/x-www-form-urlencoded'
// //                 },
// //                 body: new URLSearchParams({ category_id: categoryId })
// //             });

// //             const result = await response.json();
// //             if (result.success && result.html) {
// //                 dynamicFieldsContainer.innerHTML = result.html;
// //             } else {
// //                 console.warn('No dynamic fields returned.');
// //                 dynamicFieldsContainer.innerHTML = '';
// //             }
// //         } catch (err) {
// //             console.error('Failed to fetch dynamic fields:', err);
// //         }
// //     });
// // });
