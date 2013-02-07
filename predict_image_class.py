#!/usr/bin/env python

import os
from img_processing_tools import *
import Image 
import time
import csv
import numpy as np
import milk
from mvpa.clfs.knn import kNN
from mvpa.datasets import Dataset
import mlpy
import matplotlib.pyplot as plt # required for plotting

ifile  = open('sample_image_data.csv', "rb")
reader = csv.reader(ifile)

classID = []
features = []
lbp= []
lbp_temp_array = []
i3_histo_temp_array = []
i3_histo = []
rgb_histo_temp_array = []
rgb_histo = []

#read data from file into arrays
for row in reader:
    features.append(row)
'''
I3_sum =    ImageStat.Stat(image).sum
		I3_sum2 =   ImageStat.Stat(image).sum2
		I3_median = ImageStat.Stat(image).median
		I3_mean =   ImageStat.Stat(image).mean
		I3_var =    ImageStat.Stat(image).var
		I3_stddev = ImageStat.Stat(image).stddev
		I3_rms =    ImageStat.Stat(image).rms
'''

for row in range(1, len(features)):
	#print features[row][1]
	classID.append(int(features[row][0]))
	lbp_temp_array.append(features[row][1].split(" "))
	i3_histo_temp_array.append(features[row][2].split(" "))
	rgb_histo_temp_array.append(features[row][3].split(" "))


#removes ending element which is a space
for x in range(len(lbp_temp_array)):
		lbp_temp_array[x].pop()
		lbp_temp_array[x].pop(0)
		i3_histo_temp_array[x].pop()
		i3_histo_temp_array[x].pop(0)
		rgb_histo_temp_array[x].pop()
		rgb_histo_temp_array[x].pop(0)

#print lbp_temp_array
#convert all strings in array to numbers
temp_array = []
for x in range(len(lbp_temp_array)):
	temp_array = [ float(s) for s in lbp_temp_array[x] ]
	lbp.append(temp_array)
	temp_array = [ float(s) for s in i3_histo_temp_array[x] ]
	i3_histo.append(temp_array)
	temp_array = [ float(s) for s in rgb_histo_temp_array[x] ]
	rgb_histo.append(temp_array)

#make numpy arrays
lbp = np.asarray(lbp)
i3_histo = np.asarray(i3_histo)
rgb_histo = np.asarray(rgb_histo)

id_index = 0
lbp_predictdata = lbp[[id_index]]
i3_histo_predictdata = lbp[[id_index]]
xts = np.array([lbp_predictdata[0]])   # test point
print "np.shape(xts), xts.ndim, xts.dtype:", np.shape(xts), xts.ndim, xts.dtype

from sklearn.externals import joblib
model = joblib.load('lbp_knn_clf.pkl') 
from sklearn.neighbors import KNeighborsClassifier
print "knn sclearn: ", model.predict(xts)

