odoo.define('portal_attendance_artx.attendance',[], function (require) {
    console.log('hey i am mohammad!');


        var isCheckIn = true;  // Initialize as true (assuming default is check-in)

        // Function to update button status by checking attendance status
        var updateButtonStatus = async function() {
            try {
                const response = await fetch('/portal/get_attendance_status', {
                    method: 'GET'
                });
                const data = await response.json();  // Parse the JSON response

                if (data.success) {
                    if (data.message === 'Currently checked in') {
                        document.getElementById('btnText').textContent = 'Click to Check Out';
                        isCheckIn = false;  // Next action will be check-out
                    } else {
                        document.getElementById('btnText').textContent = 'Click to Check In';
                        isCheckIn = true;  // Next action will be check-in
                    }
                } else {
                    document.getElementById('btnText').textContent = 'Click to Check In';
                    isCheckIn = true;
                }
            } catch (error) {
                console.error('Error fetching attendance status:', error);
                document.getElementById('btnText').textContent = 'Click to Check In';
                isCheckIn = true;  // On error, assume next action is check-in
            }
        };

        // Function to handle button click for check-in/check-out
        var _onButton = async function(e) {
            const currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ');

            let formData = new FormData();
            if (isCheckIn) {
                formData.append('check_in', currentTime);  // Append check-in time
            } else {
                formData.append('check_out', currentTime);  // Append check-out time
            }

            try {
                const response = await fetch('/portal/add_attendance', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();  // Parse the JSON response

                if (data.success) {
                    document.getElementById('btnText').textContent = isCheckIn ? 'Click to Check Out' : 'Click to Check In';
                    isCheckIn = !isCheckIn;  // Toggle the check-in/check-out state
                } else {
                    alert('Failed to record attendance: ' + data.message);
                }
            } catch (error) {
                alert('An error occurred while recording attendance');
                console.error(error);
            }
        };

        // Attach the event listener to the button
        var button = document.getElementById("attendanceBtn");
        if (button) {
            button.addEventListener('click', _onButton);
            updateButtonStatus();  // Check the current status when the page loads
        }


});
