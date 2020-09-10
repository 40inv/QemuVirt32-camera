# OpengCV monitoring system
OpengCV monitoring system using USB camera with Flask server for QemuVirt32.

## HOW TO
**QEMU and Linux are required.**
1. Run build.sh
2. After compilation has finished go to buildroot directory and execute "make linux-menuconfig" command
3. Close appeared menu and execute "make" command
4. Go to parent directory
6. Open with text editor "runme" script and change Vendor and Product ID to your camera ID  
7. Start "run_before" script and then "runme" script

Server starts automatically. It can be found in the following directory: cd /opt/myServer/  
To access server: run your browser and use this address: http://localhost:8888/  
Login and password: admin admin


## Technologies
* QEMU
* Linux  
* Python3 
* Flask
* OpenCV
  

