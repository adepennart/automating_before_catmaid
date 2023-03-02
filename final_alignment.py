
"""
Title: final_alignment.py

Date: March 2nd, 2023

Author: Auguste de Pennart

Description:
	aligns the images from seperate substacks together

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
    No known errors
   	 
based off of Albert Cardona 2011-06-05 script
"""

#@ File (label = "directory", style = "directory") folder
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ int (label = "octave_size", default=800, min=0, max=1500 ) octave_size
#@ String(choices={"translation", "rigid", "similarity", "affine"}, style="list") model_index
#@ boolean (label = "using a windows machine") windows


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

#redefine model_index variables
if model_index == "translation":
	model_index=0
elif model_index == "rigid":
	model_index=1
elif model_index == "similarity":
	model_index=2
elif model_index == "affine":
	model_index=3

#func: get string of folder paths
folder = folder.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()


#main
# --------------------------------------------------------------------------------------
#make folders
grand_joint_folder=mut_fold(folder,output_dir,windows)
OV_folder_list=folder_find(folder,windows)
OV_folder_list=file_sort(OV_folder_list,-1)
test_dir= make_dir(grand_joint_folder,  "test_"+project_name)
proj_dir= make_dir(grand_joint_folder,  "trakem2_files_"+project_name)

#find files and paths and test alignment for each substack
big_names_keys=[]
big_names_values=[]
for num in range(0,len(OV_folder_list)):
	temp_proj_name=project_name+"_"+str(num)
	sub_OV_folders=folder_find(OV_folder_list[num], windows) #find tile directories for each substack
	filenames_keys, filenames_values=file_find(sub_OV_folders, pattern_1, pattern_3)
	print(filenames_keys, filenames_values)
	big_names_keys.append(filenames_keys[0])
	big_names_values.append(filenames_values[0])

file_list= os.listdir(proj_dir)
if temp_proj_name+"test.xml" in file_list:  #checks whether project already exists
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
project = Project.newFSProject("blank", None, proj_dir) #Creates a TrakEM2 project
#Project.getProjects().get(0)
project.adjustProperties() #adjust properties window
layerset = project.getRootLayerSet() #creates initial collection of layers variable
print(big_names_keys, big_names_values)


#could be interesting for integration into OV_overall to specify first item, here it does not matter
counter=0
counter_list=[counter]
for i in range(0,len(big_names_keys)): #set up counter to determine how many files per substack and populates trakem2 layers
	print(counter)
	layerset=add_patch_v2([big_names_keys[i]],[big_names_values[i]]
	, project, counter, counter+len(big_names_values[i]))
	counter+=len(big_names_values[i])
	counter_list.append(counter)
layer_list=[]
roi_list=[]
new_roi_list=[]
#might be useful to get the layset in a list
for layer in layerset.getLayers():
	layer_list.append(layer)
	
#roi shindig won't work with more than 1 tile
for i in range(0, len(big_names_keys)-1): #aligns layers
	for j in range(i+1, i+2):
		print(big_names_values[i][-1], big_names_values[j][0])
		print(counter_list[i]+len(big_names_values[i]),counter_list[j]+1)
		print(counter_list[i]+len(big_names_values[i])-1,counter_list[j])
		print(layer_list[counter_list[i]+len(big_names_values[i])-1],layer_list[counter_list[j]])
		#getting all patches
		tiles = layer_list[counter_list[i]+len(big_names_values[i])-1].getDisplayables(Patch) #get list of tiles
		for tile in tiles[0:]:
			r = tile.getBoundingBox() #needed in OV alignment
			roi_list.append(r)
		tiles = layer_list[counter_list[j]].getDisplayables(Patch) #get list of tiles
		for tile in tiles[0:]:
			roi = tile.getBoundingBox() #needed in OV alignment
			roi_list.append(roi)
		AlignLayersTask.alignLayersLinearlyJob(layerset,counter_list[i]+len(big_names_values[i])-1,counter_list[j],False,None,None)	
		tiles = layer_list[counter_list[i]+len(big_names_values[i])-1].getDisplayables(Patch) #get list of tiles
		for tile in tiles[0:]:
			r = tile.getBoundingBox() #needed in OV alignment
			new_roi_list.append(r)
		tiles = layer_list[counter_list[j]].getDisplayables(Patch) #get list of tiles
		for tile in tiles[0:]:
			new_roi = tile.getBoundingBox() #needed in OV alignment
			new_roi_list.append(new_roi)
		x_dif = new_roi.x-roi.x	
		y_dif =  new_roi.y-roi.y
		#super inneficient
		for k in range(counter_list[j]+1, counter_list[j]+len(big_names_values[j])):
			print(k)
			tiles=layer_list[k].getDisplayables(Patch)
			for tile in tiles[0:]:
				tile.translate(x_dif,y_dif)
			
project.saveAs(os.path.join(proj_dir, temp_proj_name+"aligned"), False) #save project file, after z alignment
layerset.setMinimumDimensions() #readjust canvas to only NO tiles)
#exports images
mini_dir= make_dir(output_dir,  "export_unprocessed")
export_image(layerset, mini_dir, canvas_roi=True)
mini_dir= make_dir(output_dir,  "export_processed")
export_image(layerset, mini_dir, canvas_roi=True, processed=True)
print("Done!")