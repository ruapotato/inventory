inventory.py
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

Run ./inventoryCMD.py or Run FLASK server
------------------
  * New Scan
  * Pick Lab (Configure in ./env.config)
  * Pick rack to add servers. 
  * Pick Storage to add HDDs/SSDs/Stored HW
  * Enter info and scan/enter serials

With the Flask server running(run testrun.sh), navigate to http://127.0.0.1:5000/index.html 
Old CMD way: Open ./index.html
-----------------

Info
----
* Servers/'Stored stuff' are kept as txt files in ./configs/<lab>/
* In the scanner menu, left right key will switch U.
* Entered data can be edited by going back to the U in the scanner menu.
* Files are named: <serial>.config
* Debug via: tail -f /tmp/debug.txt

license
-------
GPL3
By David Hamner
