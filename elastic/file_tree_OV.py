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
	1. would love to have an actual tree looking thing
	2. org function not working
    
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
#@ File (label = "output direcory", style = "directory") output_dir
#@ String (label = "output file name") project_name
#@ boolean (label = "using a windows machine") windows
#@ boolean (label = "Unorganized input") orgInput

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
#folder_path_2 = folder_2.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()
if windows:  # finds all the parent directories of the input folders
   f = open(output_dir+"\\"+project_name+"treefile.txt","w")
   f_2 = open(output_dir+"\\"+project_name+"treefile_condensed.txt","w")
elif not windows:
    f = open(output_dir+"/"+project_name+"treefile.txt","w")
    f_2 = open(output_dir+"/"+project_name+"treefile_condensed.txt","w")

#flush image cache every 60 seconds?
exe = Executors.newSingleThreadScheduledExecutor()
exe.scheduleAtFixedRate(releaseAll, 0, 60, TimeUnit.SECONDS)

#main
# --------------------------------------------------------------------------------------
# grand_joint_folder=mut_fold(folder,folder_2,windows)
#grand_joint_folder=output_dir

if orgInput:
    list_files = get_stacks(folder_path, resolution = [10,10], match_pattern = 'PB',get_info=False)
#    list_files = get_stacks(folder_path, resolution = [40,40], match_pattern = 'OV')

    
    # Split list of TIF files into stacks of overlapping files
    OV_folder_list = split_stacks(list_files)
    print(OV_folder_list)
    #filenames_keys_big, filenames_values_big, OV_folder_list= list_sampleMaker(OV_folder_list)
    filenames_keys_big, filenames_values_big, OV_folder_list=list_decoder(OV_folder_list)

else:
    OV_folder_list=folder_find(folder_path,windows)
#    NO_folder_list=folder_find(folder_path_2,windows)
    for num in range(0,len(OV_folder_list)):
        print(num)
        # temp_proj_name=project_name+"_"+str(num)
        # joint_folder=mut_fold(OV_folder_list[num],NO_folder_list[num],windows)  #find tile directories for each substack
        sub_OV_folders=folder_find(OV_folder_list[num], windows) #find tile directories for each substack
        sub_OV_folders=file_sort(sub_OV_folders, -1) #sort
#        all_folder_list=folder_find(NO_folder_list[num],  windows, sub_OV_folders)
        # all_folder_list=folder_find(NO_folder_list[num],  windows, OV_folder_list[num])
        filenames_keys, filenames_values=file_find(sub_OV_folders, pattern_1, pattern_3)
        for n, name in enumerate(filenames_keys):
            if windows:  # finds all the parent directories of the input folders
                match_1 = re.findall(".[^\\\\]+", filenames_keys[n])
            elif not windows:
                match_1 = re.findall("\/.[^\/]+", filenames_keys[n])   
#		    print(match_1)
            tab_count=""
            for  match in match_1:
                if n == len(filenames_keys)-1:
			        match=match.replace("\\","")
			        #print(tab_count+match)
			        f.write(tab_count+"+------"+match+"\n")
			        f_2.write(tab_count+"+------"+match+"\n")
			        tab_count+="\t"
                else:
			        match=match.replace("\\","")
			        #print(tab_count+match)
			        f.write("+"+tab_count+"+------"+match+"\n")
			        f_2.write("+"+tab_count+"+------"+match+"\n")
			        tab_count+="\t"			    
            for m, filename in enumerate(filenames_values[n]):
		       # print(tab_count+filename)
                f.write(tab_count+"+------"+filename+"\n")    
                if m == 0:
                    f_2.write(tab_count+"+------"+filename+"\n"+tab_count+"+------"+"[...]"+"\n")
                elif m == len(filenames_values[n])-1:
        	        f_2.write(tab_count+"+------"+filename+"\n")
        f.write("++++++++++++++++++++++++++++++++++++++++++++++++++\n")
        f_2.write("++++++++++++++++++++++++++++++++++++++++++++++++++\n")
#        while 1:
#           gui = GUI.newNonBlockingDialog("good to cont?")
#           gui.addMessage("good to cont? ")
#           gui.showDialog()
#           if gui.wasOKed():
#               break
#           if not gui.wasOKed():
#               sys.exit()    
        print("folder and its content registered")
        # print(filenames_keys, filenames_values)
    #print(filenames_keys_big, filenames_values_big)
f.close()
f_2.close()
print("Done!")