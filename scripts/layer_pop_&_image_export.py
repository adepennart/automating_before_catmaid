"""
Title: catmaid.py
Date: March 15th, 2023
Author: Auguste de Pennart
Description:
	can add images to a (new/old )trakem2 project
List of functions:
	No user defined functions are used in the program.
List of "non standard modules"
	module functions.py used for this script
Procedure:
	1. pulls from seperate substacks to one trakem2 project
	2. aligns images in the z plane
	3. exports both processed and unproccesed images
Usage:
	to be used through Imagej as a script
	Pressing the bottom left Run button in the Script window will present user with prompt window for running script
known error:
	selecting "add images.." and "is project..." will add tiles from layer 1 to end even if this is not what you want.
   	 
based off of Albert Cardona 2011-06-05 script
"""

#@ File (label = "Input directory", style = "directory") folder
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ boolean (label = "using a windows machine") windows
#@ boolean (label = "add images to layers in trackem2") yes_image_add
#@ boolean (label = "export images as unprocessed and processed") yes_export
#@ boolean (label = "is project already loaded in trakem2 as only loaded project?") already_loaded


# import modules
# ----------------------------------------------------------------------------------------
#might not need all these modules
import os, re, sys

#fix this so that it works anywhere
#sys.path.append("/Users/lamarcki/Desktop/automating_before_catmaid/import_module_test")
script_path = os.path.dirname(sys.argv[0]) 
sys.path.append(script_path)


#import pre_montage
#from pre_montage import *
from functions import *
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
crop_roi_list=[]
assoc_roi_list=[]
tiles_list=[]
project_list=[]
file_keys_big_list=[]
file_values_big_list=[]
proj_folds=[]
numThreads=1
project=""
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
folder = folder.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()


#main
# --------------------------------------------------------------------------------------
#make folders
grand_joint_folder=mut_fold(folder,output_dir,windows)
OV_folder_list=folder_find(folder,windows)
OV_folder_list=file_sort(OV_folder_list,-1)
proj_dir= make_dir(grand_joint_folder,  "trakem2_files_"+project_name)

#find files and paths and test alignment for each substack
big_names_keys=[]
big_names_values=[]
for num in range(0,len(OV_folder_list)):
	sub_OV_folders=folder_find(OV_folder_list[num], windows) #find tile directories for each substack
	if sub_OV_folders != OV_folder_list:
		print(" ERROR: No subfolders should be included in input directory")
		sys.exit("No subfolders should be included in input directory")

filenames_keys, filenames_values=file_find(OV_folder_list, pattern_1, pattern_3)
print(filenames_keys, filenames_values)
big_names_keys.append(filenames_keys[0])
big_names_values.append(filenames_values[0])

file_list= os.listdir(proj_dir)
if project_name+"test.xml" in file_list:  #checks whether project already exists
			gui = GUI.newNonBlockingDialog("Overwrite?")
			gui.addMessage(" Press ok to overwrite project file?")
			gui.showDialog()
			if gui.wasOKed():
				if windows:
					os.remove(sub_dir+"\\"+temp_proj_name+"test")
				if not windows:
					os.remove(sub_dir+"/"+temp_proj_name+"test.xml")
			elif not gui.wasOKed():
				sys.exit()
if not already_loaded:
	project = Project.newFSProject("blank", None, proj_dir) #Creates a TrakEM2 project
else:
	project = Project.getProjects().get(0)
layerset = project.getRootLayerSet() #creates initial collection of layers variable
print(big_names_keys, big_names_values)

if yes_image_add:
	#could be interesting for integration into OV_overall to specify first item, here it does not matter
	for i in range(0,len(big_names_keys)): #set up counter to determine how many files per substack and populates trakem2 layers
		layerset=add_patch_v2([big_names_keys[i]],[big_names_values[i]],project, 0, len(filenames_values)+1)

project.saveAs(os.path.join(proj_dir, project_name+"aligned"), False) #save project file, after z alignment
layerset.setMinimumDimensions() #readjust canvas to only NO tiles)

if yes_export:
	#exports images
	mini_dir= make_dir(output_dir,  "export_unprocessed")
	exportProject(project, mini_dir,canvas_roi=True,blend=True)
	mini_dir= make_dir(output_dir,  "export_processed")
	exportProject(project, mini_dir,canvas_roi=True, processed=True)#,blend=True)
print("Done!")
