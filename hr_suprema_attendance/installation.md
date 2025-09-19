1) What to install (pick one stack)
    A) BioStar 2 Server (REST & WebSocket)


    Install BioStar 2 server on Windows (10 works well; 11 can be finicky with drivers/services/firewall). 
    supremainc.com

    Download: https://download.supremainc.com/download-center/pages/prod-resource.asp

    You can get real-time events via WebSocket from the BioStar 2 server (no SDK coding) by hosting a simple HTML on the built-in nginx. 
    You can also pull event logs via REST for polling scenarios. 
    https://support.supremainc.com
    

    B) Suprema API 

For BioStar 2 REST: test /v2/events/search (or per “Retrieve Event Logs” guide) with proper auth to confirm logs are flowing
https://bs2api.biostar2.com/


2) Quick install notes
 BioStar 2 Server (Windows)

Run the BioStar 2 installer (Admin PC/Server).
Ensure HTTPS is enabled (required for the WebSocket helper page from Suprema KB).
Open firewall for BioStar services and nginx. 
Install Device Gateway (from G-SDK docs/releases).
(Optional) Install Master Gateway only for multi-site; it needs a license.
Use your preferred client library (Python is great for quick webhooks). 

3) Odoo Installation:
    Download hr_suprema_attendance.zip extract and upload to odoo server.

    A) Upload Odoo Module to your Server SH/other Hosting server.
    B) Restart Odoo Service or Update models from server side
    C) Update list apps from odoo Apps 
    D) install hr_suprema_attendance

4) Use App:
    After installation go to attendace module in your odoo apps and you an find Biostar menu 
    A) select Devices 
        Insert api  server 
            1- url
            2- user
            3 password
            4- Device ip 
        Repeat A) if there is more than one Device 
    B) Dowload Users from button and link any user with it is employee 
    C) Pull Events Last Day or Last 365 Days.
