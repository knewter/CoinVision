#!/usr/bin/python
# This is a standalone program. Pass an image name as a first parameter of the program.

import sys
from math import sin, cos, sqrt, pi
import cv
import urllib2
from coin_tools import *
import time
import scipy.spatial
# toggle between CV_HOUGH_STANDARD and CV_HOUGH_PROBILISTIC
USE_STANDARD = False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        src = cv.LoadImage(filename, cv.CV_LOAD_IMAGE_GRAYSCALE)
    else:
        url = 'https://code.ros.org/svn/opencv/trunk/opencv/doc/pics/building.jpg'
        filedata = urllib2.urlopen(url).read()
        imagefiledata = cv.CreateMatHeader(1, len(filedata), cv.CV_8UC1)
        cv.SetData(imagefiledata, filedata, len(filedata))
        src = cv.DecodeImageM(imagefiledata, cv.CV_LOAD_IMAGE_GRAYSCALE)


    cv.NamedWindow("Source", 1)
    cv.NamedWindow("Hough", 1)
    x = 1000
    r = 0
    while True:
	if r > 360: r = 0
        dst = cv.CreateImage(cv.GetSize(src), 8, 1)
	rt = cv.CreateImage(cv.GetSize(src), 8, 1)
	rt = rotate_image(src, r)
        color_dst = cv.CreateImage(cv.GetSize(src), 8, 3)
        storage = cv.CreateMemStorage(0)
        lines = 0
        cv.Canny(rt, dst, x/2, x, 3)
        cv.CvtColor(dst, color_dst, cv.CV_GRAY2BGR)

        if USE_STANDARD:
            lines = cv.HoughLines2(dst, storage, cv.CV_HOUGH_STANDARD, 1, pi / 180, 100, 0, 0)
            for (rho, theta) in lines[:100]:
                a = cos(theta)
                b = sin(theta)
                x0 = a * rho 
                y0 = b * rho
                pt1 = (cv.Round(x0 + 1000*(-b)), cv.Round(y0 + 1000*(a)))
                pt2 = (cv.Round(x0 - 1000*(-b)), cv.Round(y0 - 1000*(a)))
                cv.Line(color_dst, pt1, pt2, cv.RGB(255, 0, 0), 3, 8)
        else:
            lines = cv.HoughLines2(dst, storage, cv.CV_HOUGH_PROBABILISTIC, 1, pi / 180, 50, 50, 10)
            for line in lines:
                cv.Line(color_dst, line[0], line[1], cv.CV_RGB(255, 0, 0), 3, 8)
	if r == 0:
		org_lines = lines
	if USE_STANDARD: print "STANDARD"
	else: print "Probalistic"
	print "canny:", x,  "  degrees:", r
	print "lines:", len(lines)
	print "dist: ", scipy.spatial.distance.cdist(lines, org_lines,'euclidean')
        cv.ShowImage("Source", src)
        cv.ShowImage("Hough", color_dst)
	if len(lines) < 150:
		k = ord("s")
		time.sleep(.2)
		cv.WaitKey(10)
	if len(lines) > 150:
		#print "wait"
        	k = cv.WaitKey(0)
	print k
        if k == ord(' '):
            USE_STANDARD = not USE_STANDARD
	if k == ord('w'):
		x = x +10
	if k == ord('s'):
		x = x  - 10	
	if k == ord('r'):
		r = r + 5
        if k == 27:
            break
	
