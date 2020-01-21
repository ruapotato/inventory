DC inventory
============
Simple script for Data center infrastructure management
Uses Flask


Usage:
====
edit ./env.config
-----------------
  * Server Rooms
  * Server Racks
  * Hardware types

delete example configs
----------------------
  * rm -r ./configs/*

Run FLASK server (testing)
------------------
With the Flask server running(./testrun.sh), navigate to http://127.0.0.1:5000/index.html 

Install Server (SSL)
------------
  * copy inventory to /
  * cd /inventory
  * openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout key.pem -out cert.pem
  * cp inventory.service /etc/systemd/system/
  * systemctl start inventory

-----------------

Info
----
* Servers/'Stored stuff' are kept as txt files in ./configs/<lab>/
* Files are named: <serial>.config
* Debug via: tail -f /tmp/debug.txt

license
-------
GPL3
By David Hamner
