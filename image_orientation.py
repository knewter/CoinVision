#!/usr/bin/env python

#This program will return the angle at which the second is in relation to the first. 
#params: arg1 = base or original image, arg2= image that is mis-oriented


import cv
#from opencv import cv2
from SimpleCV import *
import sys
import numpy as np
import Image 
import math, operator
import time
import scipy.spatial
import ImageChops
import ImageOps
from math import pi
from opencv import adaptors
import ImageFilter
from coin_tools import *
#from common import anorm
#from functools import partial


##Globals
sample_size = 72


def surf_dif(img1, img2):
	#only features with a keypoint.hessian > 600 will be extracted
	#using extended descriptors (1) -> 128 elements each
	#surfParams = cvSURFParams(600, 1)
	#gray images for detecting
	object1 = cv.CreateImage((img1.width,img1.height), 8, 1)
	cv.CvtColor(img1, object1, cv.CV_BGR2GRAY)
	object2 = cv.CreateImage((img2.width,img2.height), 8, 1)
	cv.CvtColor(img2, object2, cv.CV_BGR2GRAY)

	keypoints1, descriptors1 = cv.ExtractSURF(object1, None, (0, 400, 3, 4))
	keypoints2, descriptors2 = cv.ExtractSURF(object2, None, (0, 400, 3, 4))

	print "found %d keypoints for img1"%keypoints1.rows
	print "found %d keypoints for img2"%keypoints2.rows

	#feature matching
	ft = cv.CreateKDTree(descriptors1)
	indices, distances = cv.FindFeatures(ft, descriptors2, 1, 250)
	cv.cvReleaseFeatureTree(ft)

	#the C max value for a long (no limit in python)
	DBL_MAX = 1.7976931348623158e+308
	reverseLookup = [-1]*keypoints1.rows
	reverseLookupDist = [DBL_MAX]*keypoints1.rows

	matchCount = 0
	for j in xrange(keypoints2.rows):
	  i = indices[j]
	  d = distances[j]
	  if d < reverseLookupDist[i]:
		   if reverseLookupDist[i] == DBL_MAX:
		       matchCount+=1
		   reverseLookup[i] = j
		   reverseLookupDist[i] = d
		  
	print "found %d putative correspondences"%matchCount

	points1 = cv.CreateMat(1,matchCount,cv.CV_32FC2)
	points2 = cv.CreateMat(1,matchCount,cv.CV_32FC2)
	m=0
	for j in xrange(keypoints2.rows):
	  i = indices[j]
	  if j == reverseLookup[i]:
		   pt1 = keypoints1[i][0], keypoints1[i][1]
		   pt2 = keypoints2[j][0], keypoints2[j][1]
		   points1[m]=cv.cvScalar(pt1[0], pt1[1])
		   points2[m]=cv.cvScalar(pt2[0], pt2[1])
		   m+=1

	#remove outliers with fundamental matrix:
	status = cv.CreateMat(points1.rows, points1.cols, cv.CV_8UC1)
	fund = cv.CreateMat(3, 3, CV_32FC1)
	cv.FindFundamentalMat(points1, points2, fund, cv.CV_FM_LMEDS, 1.0, 0.99, status)
	print "fundamental matrix:"
	print fund

	print "number of outliers detected using the fundamental matrix: ", len([stat for stat in status if not stat])

	#updating the points without the outliers
	points1 = [pt for i, pt in enumerate(points1) if status[i]]
	points2 = [pt for i, pt in enumerate(points2) if status[i]]

	print "final number of correspondences:",len(points1) 





def flatten(x):
    """flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, MyVector(8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    result = []
    for el in x:
        #if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def dist(x,y):   
    return np.sqrt(np.sum((x-y)**2))

def get_SURF_points(img):
	temp_img = cv.CloneMat(img)
	keypoints = []
	try:
		storage = cv.CreateMemStorage() 
		(keypoints, descriptors) = cv.ExtractSURF(temp_img , None, storage , (0, 400, 3, 4))
		for ((xx, yy), laplacian, size, dir, hessian) in keypoints:
			print "count= %d x=%d y=%d laplacian=%d size=%d dir=%f hessian=%f" % (len(keypoints), xx, yy, laplacian, size, dir, hessian)
			cv.Circle(temp_img, (xx,yy), size, (255,0,0),1, cv.CV_AA , 0)
	except Exception, e:
    		print e

	cv.ShowImage('SURF', temp_img )
	cv.WaitKey()
	cv.DestroyWindow('SURF')
	if len(keypoints) > 0: 
		return keypoints
	else:
		return -1



def resize_img(original_img, scale_percentage):
		print original_img.height, original_img.width, original_img.nChannels
		#resized_img = cv.CreateMat(original_img.rows * scale_percentage , original.cols * scale_percenta, cv.CV_8UC3)
		resized_img = cv.CreateImage((cv.Round(original_img.width * scale_percentage) , cv.Round(original_img.height * scale_percentage)), original_img.depth, original_img.nChannels)
		cv.Resize(original_img, resized_img)
		return resized_img
		#cv.ShowImage("original_img", original_img)
		#cv.ShowImage("resized_img", resized_img)
		#cv.WaitKey()

def PILtoCV(PIL_img):
	cv_img = cv.CreateImageHeader(PIL_img.size, cv.IPL_DEPTH_8U, 1)
	cv.SetData(cv_img, PIL_img.tostring())
	return cv_img

def CVtoPIL(img):
	"""converts CV image to PIL image"""
	pil_img = Image.fromstring("L", cv.GetSize(img), img.tostring())
	cv_img = cv.CreateMatHeader(cv.GetSize(img)[1], cv.GetSize(img)[0], cv.CV_8UC1)
	cv.SetData(cv_img, pil_img.tostring())
	return pil_img

def center_crop(img, center, crop_size):
	#crop out center of coin based on found center
	x,y = center[0][0], center[0][1]
	#radius = center[1]
	radius = (crop_size * 4)
	center_crop_topleft = (x-(radius-crop_size), y-(radius-crop_size))
	center_crop_bottomright = (x+(radius-crop_size), y+(radius-crop_size))
	#print "crop top left:     ", center_crop_topleft
	#print "crop bottom right: ", center_crop_bottomright
	center_crop = cv.GetSubRect(img, (center_crop_topleft[0], center_crop_topleft[1] , (center_crop_bottomright[0] - center_crop_topleft[0]), (center_crop_bottomright[1] - center_crop_topleft[1])  ))
	#cv.ShowImage("Crop Center of Coin", center_crop)
	#cv.WaitKey()
	return center_crop




def rmsdiff(img1, img2):
    "Calculate the root-mean-square difference between two images"
    diff = ImageChops.difference(img1, img2)
    h = diff.histogram()
    sq = (value*(idx**2) for idx, value in enumerate(h))
    sum_of_squares = sum(sq)
    rms = math.sqrt(sum_of_squares/float(img1.size[0] * img1.size[1]))
    return rms

def get_orientation_canny(img1, img2):
	#x=190 
	subtracted_image = cv.CreateImage(cv.GetSize(img1), 8, 1)
	temp_img = cv.CreateImage(cv.GetSize(img1), 8, 1)	
	best_sub = 999999999
	best_orientation = 0
	print 'Starting to find best orientation'
	best_canny  = 0
	best_dif = 9999999
	#for x in range(20, 200, 10):
	x = 160
	img1_copy = cv.CloneMat(img1)
	cv.Smooth(img1_copy , img1_copy, cv.CV_MEDIAN,3, 3)
	cv.Canny(img1_copy , img1_copy  ,cv.Round((x/2)),x, 3)
	cv.Smooth(img1_copy , img1_copy, cv.CV_GAUSSIAN,3, 3)
	cv.Canny(img1_copy , img1_copy  ,cv.Round((x/2)),x, 3)
	cv.ShowImage  ("Canny Coin 1", img1_copy )
	cv.MoveWindow ('Canny Coin 1', (101 + (1 * (cv.GetSize(img1)[0]))) , 100)
	for i in range(1, 360):
		img2_copy = cv.CloneMat(img2)
		img2_copy = rotate_image(img2_copy, i)
		cv.Smooth(img2_copy , img2_copy, cv.CV_MEDIAN,3, 3)
		cv.Canny(img2_copy , img2_copy  ,cv.Round((x/2)),x, 3)
		cv.Smooth(img2_copy , img2_copy, cv.CV_GAUSSIAN,3, 3)
		cv.Canny(img2_copy , img2_copy  ,x/2, x, 3)
		cv.AbsDiff(img1_copy, img2_copy , subtracted_image)
		cv.ShowImage  ("Canny Coin 2", img2_copy )
		cv.MoveWindow ('Canny Coin 2', (101 + (1 * (cv.GetSize(img1)[0]))) , (125 + (cv.GetSize(img1)[0])) )
		cv.ShowImage("Subtracted_Image", subtracted_image)
		cv.MoveWindow ("Subtracted_Image", (100 + 2*cv.GetSize(img1)[0]), (125 + cv.GetSize(img1)[1]) )
		result = cv.Sum(subtracted_image)	
		#print i, "result = ", result
		if result[0] < best_sub: 
			best_sub = result[0]
			best_orientation = i
			print i, "result = ", result[0], "  best_orientation =", best_orientation
			#dif = math.fabs(265-best_orientation)
			#if dif < best_dif: 
			#	best_dif = dif
			#	best_canny = x
		key = cv.WaitKey(5)
		if key == 27 or key == ord('q') or key == 1048688 or key == 1048603:
			break 
		#time.sleep(.01)
	print x, "   best canny: ", best_canny, "  best dif= ", best_dif
	print 'Finished finding best orientation'
	return (best_orientation)


def get_orientation_sobel(img1, img2): 
	subtracted_image = cv.CreateImage(cv.GetSize(img1), 8, 1)
	img1_copy = cv.CloneMat(img1)
	temp_img = cv.CreateImage(cv.GetSize(img1), 8, 1)	
	cv.Smooth(img1_copy , img1_copy, cv.CV_GAUSSIAN,3, 3)
	sobel_img1_copy = cv.CreateImage(cv.GetSize(img1_copy), cv.IPL_DEPTH_16S,1)
	cv.Sobel(img1_copy, sobel_img1_copy, 1 , 1 )
	cv.ConvertScaleAbs(sobel_img1_copy, img1_copy, 1, 1)
	best_sub = 9999999999
	#best_sub = 0
	best_orientation = 0
	print 'Starting to find best orientation'
	for i in range(0, 360, 1):
		img2_copy = cv.CloneMat(img2)
		img2_copy = rotate_image(img2_copy, i)
		cv.Smooth(img2_copy , img2_copy, cv.CV_GAUSSIAN,3, 3)
		sobel_img2_copy = cv.CreateImage(cv.GetSize(img2_copy), cv.IPL_DEPTH_16S,1)
		cv.Sobel(img2_copy, sobel_img2_copy, 1 , 1 )
		cv.ConvertScaleAbs(sobel_img2_copy, img2_copy, 1, 1)
		cv.AbsDiff(img1_copy, img2_copy , subtracted_image)
		#cv.And(img1_copy, img2_copy , subtracted_image)
		#cv.Sub(img1_copy, img2_copy , subtracted_image)
		cv.ShowImage("Image 2 being processed", img2_copy )
		cv.MoveWindow ("Image 2 being processed", (100 + 1*cv.GetSize(img2_copy)[0]), 100)
		cv.ShowImage("Subtracted_Image", subtracted_image)
		cv.MoveWindow ("Subtracted_Image", (100 + 1*cv.GetSize(img2_copy)[0]), (150 + cv.GetSize(img2_copy)[1]) )
		result = cv.Sum(subtracted_image)	
		#print i, "result = ", result
		if result[0] < best_sub: 
			best_sub = result[0]
			best_orientation = i
			print i, "result = ", result[0], "  best_orientation =", best_orientation
		key = cv.WaitKey(5)
		if key == 27 or key == ord('q') or key == 1048688 or key == 1048603:
			break 
		time.sleep(.01)
	print 'Finished finding best orientation'
	return (best_orientation)


if __name__=="__main__":

	if len(sys.argv) < 3:
		print "******* Requires 2 image files of the same size."
		print "This program will return the angle at which the second is in relation to the first. ***"
		sys.exit(-1)

	try:
		img1 = cv.LoadImage(sys.argv[1],cv.CV_LOAD_IMAGE_GRAYSCALE)
		img2 = cv.LoadImage(sys.argv[2],cv.CV_LOAD_IMAGE_GRAYSCALE)
	except:
		print "******* Could not open image files *******"
		sys.exit(-1)

	img1_size  = cv.GetSize(img1)
	img1_width = img1_size[0]
	img1_height = img1_size[1]
	img2_size  = cv.GetSize(img2)
	img2_width = img2_size[0]
	img2_height = img2_size[1]

	if img1_size <> img2_size:
		print "Images must be of the same size........End Of L ine/"
		sys.exit(-1)

	cv.ShowImage("Image 1", img1)
	cv.MoveWindow ('Image 1',50 ,50 )
	cv.ShowImage("Image 2", img2)
	cv.MoveWindow ('Image 2', (50 + (1 * (cv.GetSize(img1)[0]))) , 50)
	cv.WaitKey()

	img1_copy = cv.CloneImage(img1)
	img2_copy = cv.CloneImage(img2)

	#find center of coins
	print "Finding center of coins image1....."
	coin1_center = find_center_of_coin(img1_copy)
	print "Finding center of coins image2....."
	coin2_center = find_center_of_coin(img2_copy)
	#cv.WaitKey()

	#if first image is smaller than second
	if coin2_center[1] > coin1_center[1]:
		scale = float(coin2_center[1]) / float(coin1_center[1])
		print "Scaling image 1: ", scale,"%"
		img1_copy = resize_img(img1, scale)	
		img2_copy = img2
		print "Finding Center of Scaled Corrected Image 1..."
		coin1_center = find_center_of_coin(img1_copy)
		#temp_img = SimpleCV.Image(sys.argv[1]).toGray()

	#if second image is smaller than first	
	if coin2_center[1] < coin1_center[1]:
		scale = float(coin1_center[1]) / float(coin2_center[1])
		print "Scaling image 2: ", scale, "%"
		img2_copy = resize_img(img2, scale)
		img1_copy = img1
		print "Finding Center of Scaled Corrected Image 2..."
		coin2_center = find_center_of_coin(img2_copy)

	#crop out center of coin based on found center
	print "Cropping center of original and scaled corrected images..."
	coin1_center_crop = center_crop(img1_copy, coin1_center, sample_size)
	cv.ShowImage("Crop Center of Coin1", coin1_center_crop)
	cv.MoveWindow ('Crop Center of Coin1', 100, 100)
	#cv.WaitKey()
	coin2_center_crop = center_crop(img2_copy, coin2_center, sample_size)
	cv.ShowImage("Crop Center of Coin2", coin2_center_crop)
	cv.MoveWindow ('Crop Center of Coin2', 100, (125 + (cv.GetSize(coin1_center_crop)[0])) )
	cv.WaitKey()

	img1_copy = cv.CloneMat(coin1_center_crop) 
	img2_copy = cv.CloneMat(coin2_center_crop)
	print "Press any key to find correct SOBEL orientation"  
	degrees = get_orientation_sobel(img1_copy, img2_copy)
	print "Degrees Re-oriented: ", degrees
	img3 = cv.CloneImage (img2)	
	img3 = rotate_image(img2, degrees)
	#actually need to show scaled image not just image1
	cv.DestroyWindow("Image 1")
	cv.ShowImage("Image 1", img1)
	cv.MoveWindow ('Image 1',50 ,50 )
	cv.ShowImage("SOBEL Orientation Corrected Image2", img3 )
	cv.MoveWindow ("SOBEL Orientation Corrected Image2", 50 , (50 + (1 * (cv.GetSize(img1)[0]))) )
	cv.WaitKey() 


	#Canny orientation
	i=150
	img1_copy = cv.CloneMat(coin1_center_crop) 
	img2_copy = cv.CloneMat(coin2_center_crop)
	#img1_pil = CVtoPIL(img1_copy)
	#img2_pil = CVtoPIL(img2_copy)
	#img1_pil = ImageOps.equalize(img1_pil) 
	#img2_pil = ImageOps.equalize(img2_pil)
	#img1_copy = PILtoCV(img1_pil)
	#img2_copy = PILtoCV(img2_pil)
	#print "Equalizing the histograms..."
	#cv.ShowImage("Equalized Image 1_copy", img1_copy)
	#cv.MoveWindow ('Equalized Image 1_copy', (101 + (1 * (cv.GetSize(coin1_center_crop)[0]))) , 100)
	#cv.ShowImage("Equalized Image 2_copy", img2_copy)
	#cv.MoveWindow ("Equalized Image 2_copy", (101 + (1 * (cv.GetSize(coin1_center_crop)[0]))) , (155 + (cv.GetSize(coin1_center_crop)[0])) )
	#cv.WaitKey()
	#cv.Erode(img1_copy, img1_copy , element=None, iterations=1)
	#cv.Erode(img2_copy, img2_copy , element=None, iterations=1)
	#cv.Smooth(img1_copy , img1_copy, cv.CV_GAUSSIAN,3, 3)
	#cv.Smooth(img2_copy , img2_copy, cv.CV_GAUSSIAN, 3, 3)
	#cv.Smooth(img1_copy , img1_copy, cv.CV_MEDIAN,3, 3)
	#cv.Smooth(img2_copy , img2_copy, cv.CV_MEDIAN, 3, 3)
	#cv.Canny(img1_copy , img1_copy  ,cv.Round((i/2)),i, 3)
	#cv.Canny(img2_copy , img2_copy  ,cv.Round((i/2)),i, 3)
	#maybe canny until pixel count is close???????????????
	cv.ShowImage  ("Canny Coin 1", img1_copy )
	cv.MoveWindow ('Canny Coin 1', (101 + (1 * (cv.GetSize(coin1_center_crop)[0]))) , 100)
	cv.ShowImage  ("Canny Coin 2", img2_copy )
	cv.MoveWindow ('Canny Coin 2', (101 + (1 * (cv.GetSize(coin1_center_crop)[0]))) , (125 + (cv.GetSize(coin1_center_crop)[0])) )
	print "Press any key to find correct CANNY orientation"  
	#cv.WaitKey()
	degrees = get_orientation_canny(img1_copy, img2_copy)
	print "Degrees Re-oriented: ", degrees
	img3 = cv.CloneMat(coin2_center_crop)
	img3 = rotate_image(coin2_center_crop, degrees)
	cv.ShowImage("CANNY Corrected Image2", img3 )
	cv.MoveWindow ("CANNY Corrected Image2", (101 + (1 * (cv.GetSize(img1_copy)[0]))) , 100)
	cv.WaitKey() 



	"""
	### compare using surf
	img1_copy = cv.CloneMat(coin1_center_crop) 
	img2_copy = cv.CloneMat(coin2_center_crop)
	print "Using SURF"
	#cv.WaitKey() 
	#degrees = get_orientation_SURF(img1_copy, img2_copy)
	#print "Degrees Re-oriented: ", degrees
	#cv.WaitKey() 	
    #import sys
    #try: fn1, fn2 = sys.argv[1:3]
    #except:
    #    fn1 = '../c/box.png'
    #    fn2 = '../c/box_in_scene.png'
    #print help_message

    #img1 = cv2.imread(fn1, 0)
    #img2 = cv2.imread(fn2, 0)


	#cv.Smooth(img1_copy , img1_copy, cv.CV_GAUSSIAN,3, 3)
	#cv.Smooth(img2_copy , img2_copy, cv.CV_GAUSSIAN, 3, 3)
	#cv.Canny(img1_copy ,img1_copy  ,cv.Round((i/2)),i, 3)
	#cv.Canny(img2_copy, img2_copy  ,cv.Round((i/2)),i, 3)
	img1_copy = image2array(img1_copy)
	img2_copy = image2array(img2_copy)

	surf = cv2.SURF(1000)
	kp1, desc1 = surf.detect(img1_copy, None, False)
	kp2, desc2 = surf.detect(img2_copy, None, False)
	desc1.shape = (-1, surf.descriptorSize())
	desc2.shape = (-1, surf.descriptorSize())
	print 'img1 - %d features, img2 - %d features' % (len(kp1), len(kp2))
	print 'bruteforce match:',
	#cv.WaitKey() 
	vis_brute = match_and_draw(img1_copy, img2_copy, kp1, kp2, desc1, desc2, match_bruteforce, 0.75 )
	print 'flann match:',
	vis_flann = match_and_draw(img1_copy, img2_copy, kp1, kp2, desc1, desc2, match_flann, 0.6 )
	#cv.ShowImage('find_obj SURF', vis_brute)
	#cv.ShowImage('find_obj SURF flann', vis_flann)
	cv2.imshow('find_obj SURF', vis_brute)
	cv2.imshow('find_obj SURF flann', vis_flann)
	cv.WaitKey() 
	"""




	"""
	print "Using Laplace"
	img1_copy = cv.CloneMat(coin1_center_crop) 
	img2_copy = cv.CloneMat(coin2_center_crop)
	cv.Smooth(img1_copy , img1_copy, cv.CV_GAUSSIAN,3, 3)
	cv.Smooth(img2_copy , img2_copy, cv.CV_GAUSSIAN, 3, 3)
	Laplace_img1_copy = cv.CreateImage(cv.GetSize(img1_copy), cv.IPL_DEPTH_16S,1)
	Laplace_img2_copy = cv.CreateImage(cv.GetSize(img2_copy), cv.IPL_DEPTH_16S,1)
	cv.Laplace(img1_copy, Laplace_img1_copy)
	cv.Laplace(img2_copy, Laplace_img2_copy)
	cv.ConvertScaleAbs(Laplace_img1_copy, img1_copy, 1, 0)
	cv.ConvertScaleAbs(Laplace_img2_copy, img2_copy, 1, 0)
	cv.ShowImage("Laplace Image1", img1_copy )
	cv.ShowImage("Laplace Image2", img2_copy )
	cv.WaitKey()
	img1_pil = CVtoPIL(img1_copy)
	img2_pil = CVtoPIL(img2_copy)
	degrees = get_orientation_PIL1(img1_pil, img2_pil)
	print "Degrees Re-oriented: ", degrees
	img3 = cv.CloneMat(coin2_center_crop)	
	img3 = rotate_image(coin2_center_crop, degrees)
	cv.ShowImage("Laplace Orientation Corrected Image2", img3 )
	cv.MoveWindow ("Laplace Orientation Corrected Image2", 600, 800)
	#print "i=", i
	#cv.WaitKey() 
	#print " RMS: ", rmsdiff(img1_pil, img2_pil)
	cv.WaitKey() 
	"""
	"""
	print "Using Sobel / Binary"
	img1_copy = cv.CloneMat(coin1_center_crop) 
	img2_copy = cv.CloneMat(coin2_center_crop)
	cv.Smooth(img1_copy , img1_copy, cv.CV_GAUSSIAN,3, 3)
	cv.Smooth(img2_copy , img2_copy, cv.CV_GAUSSIAN, 3, 3)
	#sobel_img1_copy = cv.CreateImage(cv.GetSize(img1_copy), cv.IPL_DEPTH_16S,1)
	#sobel_img2_copy = cv.CreateImage(cv.GetSize(img2_copy), cv.IPL_DEPTH_16S,1)
	#cv.Sobel(img1_copy, sobel_img1_copy, 1 , 0 )
	#cv.Sobel(img2_copy, sobel_img2_copy, 1 , 0 )
	#cv.ConvertScaleAbs(sobel_img1_copy, img1_copy, 1, 0)
	#cv.ConvertScaleAbs(sobel_img2_copy, img2_copy, 1, 0)
	img1_copy = image2array(img1_copy)
	img2_copy = image2array(img2_copy)
	(thresh, bw_img1_copy) = cv2.threshold(img1_copy, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	(thresh, bw_img2_copy) = cv2.threshold(img2_copy, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	#thresh = 75
	#bw_img1_copy = cv2.threshold(img1_copy, thresh, 255, cv2.THRESH_BINARY)[1]
	#bw_img2_copy = cv2.threshold(img2_copy, thresh, 255, cv2.THRESH_BINARY)[1]
	img1_pil = array2image(bw_img1_copy)
	img2_pil = array2image(bw_img2_copy)
	img1_CV = PILtoCV(img1_pil)
	img2_CV = PILtoCV(img2_pil)

	cv.ShowImage("bw_img1_copy Image1", img1_CV )
	cv.ShowImage("bw_img2_copy Image2", img2_CV )

	cv.WaitKey()
	img1_pil = CVtoPIL(img1_CV )
	img2_pil = CVtoPIL(img2_CV )
	degrees = get_orientation_PIL1(img1_pil, img2_pil)
	print "Degrees Re-oriented: ", degrees
	img3 = cv.CloneMat(coin2_center_crop)	
	img3 = rotate_image(coin2_center_crop, degrees)
	cv.ShowImage("CornerHarris Orientation Corrected Image2", img3 )
	cv.MoveWindow ("CornerHarris Orientation Corrected Image2", 600, 800)
	#print "i=", i
	#cv.WaitKey() 
	#print " RMS: ", rmsdiff(img1_pil, img2_pil)
	cv.WaitKey() 
	"""




