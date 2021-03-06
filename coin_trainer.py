#!/usr/bin/env python
#!/usr/bin/python

import sys
sys.path.append( "../lib/" )

import easygui as eg
from img_processing_tools import *
#from PIL import Image
from PIL import ImageStat, Image, ImageDraw
import cv, cv2 
import time
import math
import mahotas
from mahotas.features import surf
import numpy as np
import pickle
import csv
import milk
from threading import *
from pylab import *
import scipy.spatial
from CoinServoDriver import *
from coin_tools import *
import glob
import pylab
from SimpleCV import *
import itertools

def get_new_coin(servo, dc_motor):
	servo.arm_down()
	base_frame = snap_shot(1)
	#time.sleep(1)
	new_coin = False
	print 'CoinID Motor Driver Comm OPEN:', dc_motor.isOpen()
	print 'Connected to: ', dc_motor.portstr
	pilimg1 = CVtoPIL(CVtoGray(base_frame))
	print "pilimg1 = ", pilimg1
	while not new_coin:
		if new_coin == False: move_motor(dc_motor, "F", 20)
		if new_coin == False: time.sleep(.5)
		motor_stop(dc_motor)
		if new_coin == False: time.sleep(.8)
		frame = snap_shot(1)
		pilimg2 = CVtoPIL(CVtoGray(frame))
		rms_dif = rmsdiff(pilimg1, pilimg2)
		print "RMS Dif:", rms_dif 
		if rms_dif > 20:
			print "New coin...", rms_dif
			sys.stdout.write('\a') #beep
			new_coin = True

		
def move_motor(dc_motor, direction, speed):
	if direction == "F":
		cmd_str = direction + str(speed) + '%\r'
		print cmd_str
		dc_motor.write ('GO\r')
		time.sleep(.01)
		dc_motor.write (cmd_str)
		time.sleep(.01)
		dc_motor.write ('GO\r')
		time.sleep(.01)

def motor_stop(dc_motor):
	dc_motor.write ('X\r\n')

def snap_shot(usb_device):
	print "snapshot called"
	#capture from camera at location 0
	now = time.time()
	webcam1 = None
	frame = None
	#try:	
	while webcam1 == None:
		webcam1 = cv2.VideoCapture(usb_device)
		#webcam1 = cv.CreateCameraCapture(usb_device)
		#time.sleep(.05)
		#cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
		#cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
		time.sleep(.1)
	for i in range(6):
		ret, frame = webcam1.read()
		frame = array2cv(frame)
		#cv.GrabFrame(webcam1)
		#frame = cv.QueryFrame(webcam1)
	#except:
	#	print "******* Could not open WEBCAM *******"
	#	print "Unexpected error:", sys.exc_info()[0]
		#raise		
		#sys.exit(-1)
	print frame
	print webcam1
	#while webcam1 != None:
	cv2.VideoCapture(usb_device).release()
	print webcam1
	#time.sleep(1)
	#print webcam1
	return frame
 

def display_image(img, wait_time):
	global ready_to_display
	while ready_to_display != True:
		time.sleep(.1)
		#print "waiting"
	#time.sleep(wait_time)
	img = CVtoPIL(array2cv(img))
	img = img.transpose(1)
	#img = img.transpose(2)

	#img.save("pil.png")
	pylab.ion()
	#a = imread(img)
	#print "a:", a
	pylab.imshow(img)
	pylab.draw()
	


def houghlines(img, min_lines):
	global ready_to_display
	x = 500
	edges = cv2.Canny(img, (int(x/2)), x , apertureSize=3)
	lines = cv2.HoughLinesP(edges, 1, math.pi/180, 50, None, 50, 10);
	
	while len(lines[0]) < min_lines:
		edges = cv2.Canny(img, (int(x/2)), x , apertureSize=3)
		#cv2.imwrite("canny.png", edges)
		lines = cv2.HoughLinesP(edges, 1, math.pi/180, 50, None, 50, 10);
		print "x: ", x , " Lines: ", len(lines[0])
		x = x -5
		#time.sleep(.2)
	cv2.imwrite("canny.png", edges)
	temp_img = img
	for line in lines[0]:
		pt1 = (line[0],line[1])
		pt2 = (line[2],line[3])
		cv2.line(temp_img, pt1, pt2, (0,0,255), 3)
	#cv2.imwrite("houghlines.png", temp_img)
	print "houghlines:", len(lines[0])
	#ready_to_display = True
	#display =Thread(target=display_image, args=(temp_img,.1,))
	#display.daemon=True
	#display.start()
	ready_to_display = True
 	display_image(temp_img, 1)
	
	return lines

def preprocess_img(img1):
	print "Greying image"
	grey = array2cv(cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY))
	print "Finding Center of Coin"
	coin_center = find_center_of_coin(grey)
	print "Center of Coin:", coin_center
	
	print "Smoothing Image"
	cv.Smooth(grey,grey,cv.CV_GAUSSIAN,3,3)
	#x=120
	#cv.Canny(grey,grey,cv.Round((x/2)),x, 3)
	
	cropped = center_crop(grey, coin_center, 50)
	cv2.imwrite("cropped.png", cv2array(cropped))
	
	#########################################
	#		Display Results
	#######################
	display =Thread(target=display_image, args=(cv2array(cropped),.1,))
	display.daemon=True
	display.start()
	return cv2array(cropped)


def find_features(img):
	features = houghlines(img, 125)

	#print img, type(img)

	#gray scale the image if neccessary
	#if img.shape[2] == 3:
	#	img = img.mean(2)

	#img = mahotas.imread(imname, as_grey=True)
	#features = mahotas.features.haralick(img).mean(0)
	#f2 = features
	#print 'haralick features:', features, len(features), type(features[0])
	
	#features = mahotas.features.lbp(img, 1, 8)
	#f2 = np.concatenate((f2,features))
	#print 'LBP features:', features, len(features), type(features[0])

	#features = mahotas.features.tas(img)
	#f2 = np.concatenate((f2,features))
	#print 'TAS features:', features, len(features), type(features[0])

	#features = mahotas.features.zernike_moments(np.mean(img,2), 2, degree=8)
	#print 'ZERNIKE features:', features, len(features), type(features[0])
	#f2 = np.concatenate((f2,features))
	#print "All Features: ", f2, len(f2)
	#features_surf = surf.surf(np.mean(img,2))
	#print "SURF:", features_surf, " len:", len(features_surf)
	'''
	try:
		import milk

		# spoints includes both the detection information (such as the position
		# and the scale) as well as the descriptor (i.e., what the area around
		# the point looks like). We only want to use the descriptor for
		# clustering. The descriptor starts at position 5:
		descrs = features_surf[:,5:]

		# We use 5 colours just because if it was much larger, then the colours
		# would look too similar in the output.
		k = 5
		surf_pts_to_ID = 50
		values, _  = milk.kmeans(descrs, k)
		colors = np.array([(255-52*i,25+52*i,37**i % 101) for i in xrange(k)])
	except:
		values = np.zeros(100)
		colors = [(255,0,0)]
	surf_img = surf.show_surf(np.mean(img,2), features_surf[:surf_pts_to_ID], values, colors)
	#imshow(surf_img)
	#show()
	'''
	#houghlines opencv
	"""
	Python: cv2.HoughLinesP(image, rho, theta, threshold[, lines[, minLineLength[, maxLineGap]]]) -> lines
	Parameters:	
	image - 8-bit, single-channel binary source image. The image may be modified by the function.
	lines - Output vector of lines. Each line is represented by a 4-element vector, where and are the ending points of each detected line segment.
	rho - Distance resolution of the accumulator in pixels.
	theta - Angle resolution of the accumulator in radians.
	threshold - Accumulator threshold parameter. Only those lines are returned that get enough votes (  ).
	minLineLength - Minimum line length. Line segments shorter than that are rejected.
	maxLineGap - Maximum allowed gap between points on the same line to link them.
	"""
	#try:
	#gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	#gray = CVtoGray(numpy2CV(img))
	#print gray

	#except:
	#	print "no houghlines available"
	#img1 = mahotas.imread('temp.png')
	#T_otsu = mahotas.thresholding.otsu(img1)
	#seeds,_ = mahotas.label(img > T_otsu)
	#labeled = mahotas.cwatershed(img1.max() - img1, seeds)
	#imshow(labeled)
	#show()
	'''

	grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	iplimage = cv.fromarray(grey)
	print type( iplimage)
	hu_moments = []
	hu_moments =  np.array(cv.GetHuMoments(cv.Moments(iplimage)))
	#hu_moments = hu_moments.reshape(1, (hu_moments.shape[0]))
	print "HUMOMENTS: ", hu_moments
	features = hu_moments
	'''
	'''
	for x in hu_moments[0]:
		if x < 0: x = (x * -1)
		print math.log10(x)
	distmin = 0
	degree = 0
	for x in range(359):

		img2 = cv.CloneImage(array2cv(grey))
		#img2 = rotate_image(img2, x)
		#print type(img2)
		img2 = CVtoPIL(img2)
		img2 = img2.rotate(x, expand=1)
		#print type(img2)
		img2 = PILtoCV(img2,1)
		cv.ShowImage("45", img2)
		cv.WaitKey()
		#print type(img2)
		hu_moments2 = []
		hu_moments2 =  np.array(cv.GetHuMoments(cv.Moments(cv.GetMat(img2))))
		hu_moments2 = hu_moments2.reshape(1, (hu_moments2.shape[0]))
		distance_btw_images = scipy.spatial.distance.cdist(hu_moments, hu_moments2,'euclidean')
		if (distance_btw_images < distmin): degree = x
		print x, ": ", log10(distance_btw_images )
		#print "HUMOMENTS2: ", hu_moments2
		#for x in hu_moments2:
		#	print math.log10(x)
	print "degree = ", degree
	'''

	return features

def classify(model, features):
     return model.apply(features)

def grab_frame_from_video(video):
	frame = video.read()
	return frame


def predict_class(img):
	features = find_features(img)
	'''
	from sklearn import svm
	model = pickle.load( open( "coinvision_ai_model_svc.mdl", "rb" ) )
	print model.predict(features)

	from sklearn.neighbors import KNeighborsClassifier
	#neigh = KNeighborsClassifier(n_neighbors=3)
	neigh= pickle.load( open( "coinvision_ai_model_knn.mdl", "rb" ) )
	print neigh.predict(features)
	#print neigh.predict_proba(1)
	'''
	classID = 0
#try:
	model = pickle.load( open( "coinvision_ai_model.mdl", "rb" ) )
	classID = classify(model, features)	
	print "classID: = ", classID
	if classID == 1: answer = "Jefferson HEADS"
	if classID == 2: answer = "Monticello TAILS"
	if classID == 3: answer = "Other HEADS"
	if classID == 4: answer = "Other TAILS"
	print "predicted classID:", answer
	#eg.msgbox("predicted classID:"+answer)
	return classID
#except:
	print "could not predict...bad data"


def save_data(features, classID):
	data_filename = 'coinvision_feature_data.csv'
	###########################
	print 'writing image features to file: ', data_filename
	# delete data file and write header
	#f_handle = open(data_filename, 'w')
	#f_handle.write(str("classid, lbp, i3_histogram, rgb_histogram, sum_I3, sum2_I3, median_I3, avg_I3, var_I3, stddev_I3, rms_I3"))
	#f_handle.write('\n')
	#f_handle.close()

	#write class data to file
	f_handle = open(data_filename, 'a')
	f_handle.write(str(classID))
	f_handle.write(', ')
	f_handle.close()

	f_handle = open(data_filename, 'a')
	for i in range(len(features)):
		f_handle.write(str(features[i]))
		f_handle.write(" ")
	f_handle.write('\n')
	f_handle.close()


def process_all_images():
	path = "../coin_images/"
	#print path+'jheads/*.jpg'

	for name in glob.glob(path+'jheads/*.jpg'):
		classID = "1"
		print name
		img = cv2.imread(name)
		img = preprocess_img(img)
		features = find_features(img)
		save_data(features, classID)

	for name in glob.glob(path+'jtails/*.jpg'):
		classID = "2"
		print name
		img = cv2.imread(name)
		img = preprocess_img(img)
		features = find_features(img)		
		save_data(features, classID)

	for name in glob.glob(path+'oheads/*.jpg'):
		classID = "3"
		print name
		img = cv2.imread(name)
		img = preprocess_img(img)
		features = find_features(img)
		save_data(features, classID)

	for name in glob.glob(path+'otails/*.jpg'):
		classID = "4"
		print name
		img = cv2.imread(name)
		img = preprocess_img(img)
		features = find_features(img)
		save_data(features, classID)

def train_ai():
		data = []
		classID = []
		features = []
		features_temp_array = []
		try: 
			data_filename = 'coinvision_feature_data.csv'
			print 'reading features and classID: ', data_filename
			f_handle = open(data_filename, 'r')
			reader = csv.reader(f_handle)
			#read data from file into arrays
			for row in reader:
				data.append(row)

			for row in range(0, len(data)):
				#print features[row][1]
				classID.append(int(data[row][0]))
				features_temp_array.append(data[row][1].split(" "))

			#removes ending element which is a space
			for x in range(len(features_temp_array)):
				features_temp_array[x].pop()
				features_temp_array[x].pop(0)

			#convert all strings in array to numbers
			temp_array = []
			for x in range(len(features_temp_array)):
				temp_array = [ float(s) for s in features_temp_array[x] ]
				features.append(temp_array)

			#make numpy arrays
			features = np.asarray(features)
			#print classID, features 
			learner = milk.defaultclassifier(mode='really-slow')
			model = learner.train(features, classID)
			pickle.dump( model, open( "coinvision_ai_model.mdl", "wb" ) )

		except:
			print "could not retrain.. bad file"
		'''
		from sklearn import svm
		model = svm.SVC(gamma=0.001, C=100.)
		model.fit(features, classID)
		pickle.dump( model, open( "coinvision_ai_model_svc.mdl", "wb" ) )

		from sklearn.neighbors import KNeighborsClassifier
		neigh = KNeighborsClassifier(n_neighbors=3)
		neigh.fit(features, classID)
		pickle.dump( model, open( "coinvision_ai_model_knn.mdl", "wb" ) )
		'''
		return 

def sift():
	
	#img1=Image("cropped.png")
	#img2=Image("temp.png")
	img1 = cv2.imread("cropped.png")
	img2 = cv2.imread('temp.png')

	'''
	#i.drawSIFTKeyPointMatch(i1,distance=50).show()
	img = cv2.imread("temp.png")
	template = cv2.imread("cropped.png")
	detector = cv2.FeatureDetector_create("SIFT")
	descriptor = cv2.DescriptorExtractor_create("SIFT")

	skp = detector.detect(img)
	skp, sd = descriptor.compute(img, skp)

	tkp = detector.detect(template)
	tkp, td = descriptor.compute(template, tkp)

	flann_params = dict(algorithm=1, trees=4)
	flann = cv2.flann_Index(sd, flann_params)
	idx, dist = flann.knnSearch(td, 1, params={})
	del flann
	
	#print idx, dist
	#sys.exit(-1)
	dist = dist[:,0]/2500.0
	dist = dist.reshape(-1,).tolist()
	idx = idx.reshape(-1).tolist()
	indices = range(len(dist))
	indices.sort(key=lambda i: dist[i])
	dist = [dist[i] for i in indices]
	idx = [idx[i] for i in indices]

	distance = 50
	skp_final = []
	for i, dis in itertools.izip(idx, dist):
		if dis < distance:
		    skp_final.append(skp[i])
		else:
		    break

	print skp_final
	'''
	compare_images_features_points(img1, img2, 'sift')
	#compare_images_features_points(img1, img2, 'surf')
	#compare_images_features_points(img1, img2, 'orb')

	return


def subsection_image(pil_img, sections, visual):
	sections = sections / 4
	#print "sections= ", sections
	fingerprint = []

	# - -----accepts image and  number of sections to divide the image into (resolution of fingerprint)
	# ---------- returns a subsectioned image classified by terrain type
	img_width, img_height = pil_img.size
	#print "image size = img_wdith= ", img_width, "  img_height=", img_height, "  sections=", sections
	#cv.DestroyAllWindows()
	#time.sleep(2)
	if visual == True:
		cv_original_img1 = PILtoCV(pil_img,3)
		#cv.NamedWindow('Original', cv.CV_WINDOW_AUTOSIZE)
		cv.ShowImage("Original",cv_original_img1 )
		#cv_original_img1_ary = np.array(PIL2array(pil_img))
		#print cv_original_img1_ary
		#cv2.imshow("Original",cv_original_img1_ary) 
		cv.MoveWindow("Original", ((img_width)+100),50)
	#pil_img = rgb2I3 (pil_img)
	#cv.WaitKey()
	#cv.DestroyWindow("Original")
	temp_img = pil_img.copy()
	xsegs = img_width  / sections
	ysegs = img_height / sections
	#print "xsegs, ysegs = ", xsegs, ysegs 
	for yy in range(0, img_height-ysegs+1 , ysegs):
		for xx in range(0, img_width-xsegs+1, xsegs):
			#print "Processing section =", xx, yy, xx+xsegs, yy+ysegs
			box = (xx, yy, xx+xsegs, yy+ysegs)
			#print "box = ", box
			cropped_img1 = pil_img.crop(box)
			I3_mean =   ImageStat.Stat(cropped_img1).mean
			I3_mean_rgb = (int(I3_mean[0]), int(I3_mean[1]), int(I3_mean[2]))
			print "I3_mean: ", I3_mean
			sub_ID = predict_class(image2array(cropped_img1))
			print "sub_ID:", sub_ID
			#fingerprint.append(sub_ID)
			if visual == True:
				cv_cropped_img1 = PILtoCV(cropped_img1,3)
				cv.ShowImage("Fingerprint",cv_cropped_img1 )
				cv.MoveWindow("Fingerprint", (img_width+100),50)
				if sub_ID == 1: I3_mean_rgb = (50,150,50)
				if sub_ID == 2: I3_mean_rgb = (150,150,150)
				if sub_ID == 3: I3_mean_rgb = (0,0,200)
				ImageDraw.Draw(pil_img).rectangle(box, (I3_mean_rgb))
				cv_img = PILtoCV(pil_img,3)
				cv.ShowImage("Image",cv_img)
				cv.MoveWindow("Image", 50,50)
				cv.WaitKey(20)
				time.sleep(.1)
				#print xx*yy
				#time.sleep(.05)
	#cv.DestroyAllWindows()
	cv.DestroyWindow("Fingerprint")
	cv.WaitKey(100)
	cv.DestroyWindow("Image")
	cv.WaitKey(100)
	cv.DestroyWindow("Original")
	cv.WaitKey(100)
	cv.DestroyWindow("Image")
	cv.WaitKey()
	time.sleep(2)
	#print "FINGERPRINT: ", fingerprint
	#cv.WaitKey()
	#return fingerprint
	return 9



if __name__=="__main__":
	ready_to_display = False
 	'''
	try:
		dc_motor = serial.Serial(port='/dev/ttyACM2', baudrate=9600, timeout=1)
		time.sleep(1)
		coinid_servo = CoinServoDriver()
		time.sleep(1)
	#dc_motor.close()
	except:
		print "no hardware (WEBCAM) attached"
		sys.exit(-1)
	
	#get_new_coin(coinid_servo, dc_motor)
	#time.sleep(1)
	coinid_servo.arm_up(100)
	time.sleep(.2)
	coinid_servo.arm_down()
	time.sleep(.2)
	#frame = grab_frame(1)
	#img1 = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U, 1)
	#img1 = CVtoGray(frame)	
	#cv.SaveImage("images/head_1.jpg", frame)
	#cv.WaitKey()
	#sys.exit(-1)	
	'''
	print "********************************************************************"
	print "*   must have coinvision hardware attched                          *"
	print "********************************************************************"
	video = None
	webcam1 = None
	img1 = None
	try:
		img1 = cv2.imread('temp.png')
	except:
		pass
	if len(sys.argv) > 1:
		try:
			video = cv2.VideoCapture(sys.argv[1])
			print video, sys.argv[1]
		except:
			print "******* Could not open image/video file *******"
			print "Unexpected error:", sys.exc_info()[0]
			#raise		
			sys.exit(-1)
	reply =""
	#eg.rootWindowPosition = "+100+100"
	while True:
		ready_to_display = False
		#eg.rootWindowPosition = eg.rootWindowPosition
		print 'reply=', reply		

		#if reply == "": reply = "Next Frame"

		if reply == "JHEAD":
			if img1 != None:
				path = "../coin_images/jheads/"
				filename = str(time.time()) + ".jpg"
				image_to_save = array2image(img1)
				image_to_save.save(path+filename)	

		if reply == "JTAIL":
			if img1 != None:
				path = "../coin_images/jtails/"
				filename = str(time.time()) + ".jpg"
				image_to_save = array2image(img1)
				image_to_save.save(path+filename)	

		if reply == "OHEAD":
			if img1 != None:
				path = "../coin_images/oheads/"
				filename = str(time.time()) + ".jpg"
				image_to_save = array2image(img1)
				image_to_save.save(path+filename)


		if reply == "OTAIL":
			if img1 != None:
				path = "../coin_images/otails/"
				filename = str(time.time()) + ".jpg"
				image_to_save = array2image(img1)
				image_to_save.save(path+filename)

		if reply == "Test Img":	
			classID = "2"
			if img1 != None:
				path = "../coin_images/unclassified/"
				filename = str(time.time()) + ".jpg"
				image_to_save = array2image(img1)
				image_to_save.save(path+filename)
		
		if reply == "Quit":
			print "Quitting...."
			sys.exit(-1)

		if reply == "SIFT":
			sift()

		if reply == "Predict":
			print "AI predicting"
			img1 = cv2.imread('temp.png')
			img1 = preprocess_img(img1)
			cv2.imwrite('postprocessed_img.png', img1)
			predict_class(img1)

		if reply == "Subsection":
			img1 = Image.open('temp.png')
			print img1
			xx = subsection_image(img1, 16,True)
			print xx
			#while (xx != 9):
			#	time.sleep(1)

		if reply == "Features":
			#img = mahotas.imread('temp.png', as_grey=True)
			img1 = cv2.imread('temp.png')
			img1 = preprocess_img(img1)
			find_features(img1)
			ready_to_display = True


		if reply == "Retrain AI":
			print "Retraining AI"
			train_ai()

		if reply == "Next Coin":
			print "clearing coin shoot..."
			coinid_servo.arm_up(100)
			time.sleep(.2)
			coinid_servo.arm_down()
			#time.sleep(.2)
			print "Acquiring new image.."
			if video != None: 
				img1 = np.array(grab_frame_from_video(video)[1])
			else:
				get_new_coin(coinid_servo, dc_motor)
				time.sleep(.5)
				img1 = cv2array(snap_shot(1))
			print img1
			#img1 = preprocess_img(img1)
			cv2.imwrite('temp.png', img1)
			#img1 = array2image(img1)
			#print type(img1)
			#img1.save()

		if reply == "Process Imgs":
			print "Processing all training images....."
			process_all_images()
			time.sleep(1)

		if reply == "Del AI File":
			data_filename = 'coinvision_feature_data.csv'
			f_handle = open(data_filename, 'w')
			f_handle.write('')
			f_handle.close()
			data_filename = 'coinvision_ai_model.mdl'
			f_handle = open(data_filename, 'w')
			f_handle.write('')
			f_handle.close()

		try:
			print "trying"
			reply =	eg.buttonbox(msg='Coin Trainer', title='Coin Trainer', choices=('SIFT', 'JHEAD', 'JTAIL', 'OHEAD', 'OTAIL', 'Test Img', 'Next Coin', 'Predict', 'Features','Process Imgs', 'Retrain AI' , 'Del AI File', 'Quit'), image='temp.png', root=None)
		except:
			pass



