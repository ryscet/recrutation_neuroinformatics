"""
Uses OpenCV 3 to track the rat in a cage and save its' x and y coordinates.
NOTE: The input video must have an empty background as the first frame.

Steps taken in the tracking algorithm:

   1) Converting a video frame to greyscale
   2) Smoothing the pixel values with gaussian blur
   3) Computing the absolute difference between the first frame and the current frame
   4) Finding the pixels above threshold value
   5) Dillating the thresholded pixels to fill in gaps
   6) Fitting contours to areas above threshold
   7) Selecting only the largest contour   
"""


import cv2
import pandas as pd


# Load the input video with the rat moving around the cage
clip = cv2.VideoCapture('rat_video.avi')
# Get video parameters
height = int(clip.get(cv2.CAP_PROP_FRAME_HEIGHT))
width = int(clip.get(cv2.CAP_PROP_FRAME_WIDTH))
n_frames = clip.get(cv2.CAP_PROP_FRAME_COUNT)

# Create the output video for saving the results of object tracking
fourcc = cv2.VideoWriter_fourcc(*'XVID') # specify the codec
out = cv2.VideoWriter('obj_track.avi',fourcc, 10.0, (width,height)) # path, codec, frame rate, dimensions (must be the same dimension as the input video)

# initialize the first frame in the video stream - has to be the background image!
first_frame = None
# intialize the dataframe for saving rat position
rat_path = pd.DataFrame(columns = ['x_cords', 'y_cords'])
# initialize a list of frames where rat was not detected - it might remain empty
missed_frames_idx = []

# Define room borders
left_border = 276
right_border = 463

# loop over the frames of the video
while True:
	# get current frame, idx corresponds to image filename
	frame_idx = clip.get(cv2.CAP_PROP_POS_FRAMES)

	# grab the current frame
	(grabbed, frame) = clip.read()

	# if the frame could not be grabbed, then we have reached the end of the video
	if not grabbed:
		break

	# Convert the frame to grayscale and blur it
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)

	# if the first frame is None, initialize it (has to be only bakground view)
	if first_frame is None:
		first_frame = gray
		continue

	# compute the absolute difference between the current frame and first frame
	frameDelta = cv2.absdiff(first_frame, gray)
	# threshold the frame
	thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
 
	# dilate the thresholded image to fill in holes, then find contours on thresholded image
	thresh = cv2.dilate(thresh, None, iterations=2)

	(_, contours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 

	# Check for detecting the rat - this should not fail too often, best never
	if not contours:
		print("No contour found at frame: %i" %frame_idx)
		rat_path.loc[frame_idx, :] = [None, None]
		missed_frames_idx.append(frame_idx)
		continue

    # select only the largest contour -  extra fix in case gaussian blurring does not get rid of extra contours
	areaArray = []

	# loop over the contours and get their area
	for i, c in enumerate(contours):
	    area = cv2.contourArea(c)
	    areaArray.append(area)

	# sort the array by area
	sorteddata = sorted(zip(areaArray, contours), key=lambda x: x[0], reverse=True)

	# get the largest contour 
	largest_contour = sorteddata[0][1]

	# compute the bounding box for the contour
	(x, y, w, h) = cv2.boundingRect(largest_contour)
	# draw it on the frame
	cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

	#Storet he center of the contour in the rat position dataframe
	rat_path.loc[frame_idx, :] = [x + w/2.0, y + h/2.0]
	
	# Get occupied room number and print it on the video
	if rat_path.loc[frame_idx, 'x_cords'] <= left_border:
		text = "room_1"
	elif (rat_path.loc[frame_idx, 'x_cords'] >= right_border):
		text = "room_3"
	else:
		text = "room_2"

	cv2.putText(frame,text,(10,40), cv2.FONT_HERSHEY_SIMPLEX, 1.5,(0,0,255),1,cv2.LINE_AA)

	# Draw room borders on the video
	cv2.line(frame,(276,0),(276,height),(255,0,0),2)
	cv2.line(frame,(463,0),(463,height),(255,0,0),2)


	# play the frame in the window
	cv2.imshow("cage view", frame)
	# save the frame to the output video
	out.write(frame)

	# Other views, uncomment if needed
	#cv2.imshow("Thresh", thresh)
	#cv2.imshow("Frame Delta", frameDelta)

	# Specify the window refresh rate
	key = cv2.waitKey(1) & 0xFF 
	if key == ord("q"):
		break

# Save the path of the rat to a csv file 
rat_path.to_csv('rat_path.csv', index = False)

# Check the performance of the tracking
# n_frames -1 because first frame is the empty background 
missed_frames = n_frames -1 - len(rat_path.dropna())
if missed_frames != 0:
	print('Missed %i frames at indices:' %missed_frames)
	print(missed_frames_idx)

# cleanup the clip and close any windows
clip.release()
out.release()
cv2.destroyAllWindows()

