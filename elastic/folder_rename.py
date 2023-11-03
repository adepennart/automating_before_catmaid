"""
Title: high_res.py

Date: March 2nd, 2023

Author: Auguste de Pennart

Description:
	aligns high resolution, neuropil, images to the overview low resolution images 

List of functions:
    No user defined functions are used in the program.

List of "non standard modules"
	module functions.py used for this script

Procedure:
    1. multiple checks to ensure proper file and file structure
    2. scales low resolution stack (ie. 4x magnification)
    3. creates trakem2 project
    4. creates layers and populates with one image from low resolution and from high resolution folders
    5. aligns them/montages them
    6. exports high resolution images

Usage:
	to be used through Imagej as a script
	Pressing the bottom left Run button in the Script window will present user with prompt window for running script

known error:
    1. only accepts tif files as input
    5. should check if interim folder full (kind of does)
    6. get more threads for resizing step
    8. should open project, if already opened
    9. have time stamps
    11. if folder name is the same but different folders , returns error
    12. whe nrunning without test, if trackem2 project already open will not run, needs to be opened to work
    13. low-res interim is not full if not scaled
    14. pattern change if you are using high_res_interim
    15. save test project after Gui oked
    
loosely based off of Albert Cardona 2011-06-05 script

#useful links
#upload to catmaid
#https://github.com/benmulcahy406/script_collection/blob/main/TrakEM2_export_selected_arealists_to_obj.pys

#could be useful for setting threads
#example code
#https://gist.github.com/clbarnes/b6e51ab4a52700158b6585ee7e74ca39
#java.lang.Thread
#https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/class-use/Thread.html
#java.util.Executors
#https://docs.oracle.com/en/java/javase/11/docs/api/java.base/java/util/concurrent/package-summary.html
#from java.lang import Runnable, System, Thread
#from java.util.concurrent import Executors, TimeUnit
#
#exporter_threads = Executors.newFixedThreadPool(THREADS)
#log("started exporter threads")
#purger_thread = Executors.newScheduledThreadPool(1)
#log("started purger thread")
#purger_thread.scheduleWithFixedDelay(free, 0, RELEASE_EVERY, TimeUnit.SECONDS)
#log("scheduled purge")

"""

#@ File (label = "low resolution directory", style = "directory") folder
#@ int (label = "change by this number", default=0 ) change_num
#@ boolean (label = "using a windows machine") windows


# import modules
# ----------------------------------------------------------------------------------------
#might not need all these modules
import os, re, sys

#script_path=os.path.abspath(__file__)
script_path = os.path.dirname(sys.argv[0]) 
sys.path.append(script_path)
from functions import *
from ij.gui import GenericDialog

# variables
# --------------------------------------------------------------------------------------
#vision group SBEM pattern
#pattern_1 = re.compile("([\d]+).*\.tif")
#pattern_2 = re.compile(".*-([\d]{3})-([\d]+)_.*\.tif")
#alternate patterns, but why not make more general pattern, just find tif
pattern_1 = re.compile(".*_z[\d]_.*\.tif")
pattern_2 = re.compile(".*_z[\d]_.*\.tif")
pattern_3 = re.compile(".*[\d]*.tif")
pattern_xml = re.compile(".*test\.xml")
roi_list=[]
tiles_list=[]
project_list=[]
filenames_keys_big =[]
filenames_values_big = []
file_keys_big_list=[]
file_values_big_list=[]
proj_folds=[]
project=''
octave_increase=0
transform_list=[]
#additional processing variables (gaussian blur, CLAHE )
sigmaPixels=0.7
blocksize = 300
histogram_bins = 256
maximum_slope = 1.5
#export image variables (MakeFlatImage)
export_type=0 #GRAY8
scale = 1.0
backgroundColor = Color(0,0,0,0)

#func: get string of folder paths
folder_path = folder.getAbsolutePath()
#output_dir = output_dir.getAbsolutePath()

#flush image cache every 60 seconds?
exe = Executors.newSingleThreadScheduledExecutor()
exe.scheduleAtFixedRate(releaseAll, 0, 60, TimeUnit.SECONDS)

#main
# --------------------------------------------------------------------------------------
# grand_joint_folder=mut_fold(folder,folder_2,windows)
#grand_joint_folder=output_dir


OV_folder_list=folder_find(folder_path,windows)
print(OV_folder_list)
filenames = os.listdir(folder_path)
print(filenames)
#change_num=300
filenames=file_sort(filenames,-1)
print(filenames)
if change_num < 0:
	pass
else:
	filenames=file_sort(filenames,-1,True)
print(filenames)

for num in range(0,len(filenames)):
	print(num)
	if windows:
	#   filename = loop_fold+"\\"+filename
	    os.rename(folder_path+"\\"+filenames[num], folder_path+"\\"+str(int(filenames[num])+change_num))
	elif not windows: 
	    os.rename(folder_path+"/"+filenames[num], folder_path+"\\"+str(int(filenames[num])+change_num))

filenames = os.listdir(folder_path)
print(filenames)
print("Done!")