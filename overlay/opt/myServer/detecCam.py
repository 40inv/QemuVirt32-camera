import numpy as np
import cv2
import time
import os
import queue

class detectCamera(object):
    mode = 0
    def proc(self,com_queue):
        CURR_TIME = time.asctime()
        # Change sdthresh to suit camera and conditions,
        # 10 is usually within the threshold range.
        sdThresh = 15
         
        # Used to count individualy named frames as jpgs.
        img_index = 0
        picture_taken_time = time.time();
        mode = 0; # 0 - take move detection; 1 - stream
         
        # Set up cv font
        font = cv2.FONT_HERSHEY_SIMPLEX
         
        def distMap(frame1, frame2):
            '''outputs pythagorean distance between two frames'''
            frame1_32 = np.float32(frame1)
            frame2_32 = np.float32(frame2)
            diff32 = frame1_32 - frame2_32
            norm32 = np.sqrt(diff32[:,:,0]**2 + diff32[:,:,1]**2 + diff32[:,:,2]**2)/np.sqrt(255**2 + 255**2 + 255**2)
            dist = np.uint8(norm32*255)
            return dist
         
        def print_date_time():
            '''Updates current date and time on to video'''
            CURR_TIME = time.asctime()
            cv2.putText(frame2,str(CURR_TIME),(10,450),font, 0.8, (0,255,0),2, cv2.LINE_AA)
         
        # Capture video stream.
        cap = cv2.VideoCapture(0)
        _, frame1 = cap.read()
        _, frame2 = cap.read()
         
        while(1):
            try:
                mode = com_queue.get(timeout=0)
                if mode == 1:
                    cap.release()
                    print("cap rel")
                    break
                else:
                    com_queue.put(mode)
            except queue.Empty:
                pass

            try:
                _, frame3 = cap.read()
                rows, cols, _ = np.shape(frame3)
                dist = distMap(frame1, frame3)
            except:
                print("Camera not found.")
                exit(0)
         
            frame1 = frame2
            frame2 = frame3
         
            # Apply Gaussian smoothing.
            mod = cv2.GaussianBlur(dist, (9,9), 0)
            # Apply thresholding.
            _, thresh = cv2.threshold(mod, 100, 255, 0)
            # Calculate st dev test.
            _, stDev = cv2.meanStdDev(mod)
            
            # If motion dectected.
            if mode == 0:
                if stDev > sdThresh:
                    if (time.time() - picture_taken_time) >= 1:
                        picture_taken_time = time.time()
                        print("Motion detected")
                        cv2.putText(frame2,"MD", (0,20),font, 0.8, (0,255,0),2, cv2.LINE_AA)
                        print_date_time()
             
                        # Save jpg.
                        file_name = time.asctime()+str(".jpg")
                        path = './dir'
                        cv2.imwrite(os.path.join(path,file_name.replace(" ", "")), frame2)
                        print("saved", file_name)
                        img_index +=1

    
