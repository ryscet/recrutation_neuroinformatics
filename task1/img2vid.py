"""
Converts a folder of images to a video. Only for convienience.
"""

import numpy as np
import cv2
import glob

# Get the paths of all images. Make sure these are in correct order, as they determine the frame number 
img_paths = glob.glob('images/*')

#All images must have the same resolution
first_img = cv2.imread(img_paths[0],1)

#Frame rate for the output video
frameRate = 25

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
# Pass the name, codec, frame rate and resolution to the VideoWriter
out = cv2.VideoWriter('rat_video.avi',fourcc, frameRate, (first_img.shape[1], first_img.shape[0]))

# Loop over all images
for path in img_paths:
        img = cv2.imread(path,1)
        # Write the frame to the video
        out.write(img)
        
        # Uncomment to play the video in a window
        #cv2.imshow('frame',img)
        #if cv2.waitKey(1) & 0xFF == ord('q'):
            #break

# Release everything if job is finished
cap.release()
out.release()
cv2.destroyAllWindows()