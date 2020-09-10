import gpiod
import threading
import queue
import time
from app import serverStart
from detecCam import detectCamera

chip = gpiod.Chip('gpiochip0')
button = chip.get_line(13)
led30 = chip.get_line(30)
led31 = chip.get_line(31)
button.request(consumer="its_me", type=gpiod.LINE_REQ_EV_FALLING_EDGE)
led30.request(consumer="its_me", type=gpiod.LINE_REQ_DIR_OUT)
led31.request(consumer="its_me", type=gpiod.LINE_REQ_DIR_OUT)
mode = 0 # 0 detection mode; 1 stream
led31.set_value(0)
led30.set_value(1)
bounceFlag = 0
com_queue = queue.Queue()
cam = detectCamera()
switchFlag = 0

try:
   threading.Thread(target=cam.proc, args=(com_queue,)).start()
   threading.Thread(target=serverStart, args=(com_queue,)).start()
except:
   print("Error: unable to start thread")

while True:
   ev_line = button.event_wait(sec=1) 
   try:
        servCh = com_queue.get(timeout=0)
        if servCh == 2:
            switchFlag = 1
        else:
            com_queue.put(mode)
   except queue.Empty:
        pass

   if ev_line:
     event = button.event_read()
     print("Event detected")
     bounceFlag = 1
     while bounceFlag == 1:
        ev_line = button.event_wait(sec=1) # I checked __init__ from package and idi not find how to set 0.2 sec
        if ev_line:
           continue
        else:
           bounceFlag = 0
           break;
     print("event after bounce")
     print(mode)
     if mode == 0:
        mode = 1
        com_queue.put(mode)
        led30.set_value(0) # idk why but leds are working...  lets say bad so you must press reconnect each time you change mode
        led31.set_value(1)
     else:
        mode = 0
        com_queue.put(mode)
        led31.set_value(0)
        led30.set_value(1)
        time.sleep(1)
        threading.Thread(target=cam.proc, args=(com_queue,)).start()
   elif switchFlag == 1:
        switchFlag = 0
        print(mode)
        if mode == 0:
            mode = 1
            com_queue.put(mode)
            led30.set_value(0)
            led31.set_value(1)
        else:
            mode = 0
            com_queue.put(mode)
            led31.set_value(0)
            led30.set_value(1)
            time.sleep(1)
            threading.Thread(target=cam.proc, args=(com_queue,)).start()
