# Attendance Location Module

## Overview

The Attendance Location module enhances the attendance tracking functionality in Odoo by incorporating location-based restrictions. It allows companies to define an office location and set a specific distance within which employees must be present for their attendance to be considered valid.

## Features

- Calculation of attendance based on the office location and allowed distance.
- Automatic validation of employee check-in locations against the configured office location.
- Flexible configuration options to set the office latitude, longitude, and allowed distance.
- Seamless integration with the existing attendance tracking system in Odoo.

## Installation

1. Download the Attendance Location module from the Odoo Apps Store or another trusted source.
2. Upload the module to your Odoo instance using the Apps menu.
3. Install the module and its dependencies.
4. Configure the office location and allowed distance settings according to your organization's requirements.

## Configuration

### Setting the Office Location

1. Navigate to the Settings menu in Odoo.
2. Select the Attendance Location module.
3. Locate the configuration options for setting the office latitude and longitude.
4. Enter the coordinates of the office location obtained from maps or GPS devices.

### Specifying the Allowed Distance

1. In the same configuration page, find the setting for the allowed distance.
2. Enter the maximum distance (in kilometers) within which employees' check-in locations must be from the office.

## Usage

1. Once the module is installed and configured, employees can mark their attendance as usual.
2. When an employee checks in, the module automatically calculates the distance between their location and the configured office location.
3. If the distance exceeds the allowed distance, the system displays a warning indicating that the employee is outside the office premises.
4. Administrators or managers can view attendance reports and monitor instances where employees are outside the allowed range.

## Compatibility

- This module is compatible with Odoo versions 13.0 and above.
- It may require additional customization to integrate with older versions or customized Odoo instances.

## Support

For any issues or inquiries related to the Attendance Location module, please contact our support team at support@aptuem.com.

