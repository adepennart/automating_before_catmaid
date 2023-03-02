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
#@ File (label = "high resolution directory", style = "directory") folder_2
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ boolean (label = "Invert HR images") inverted_image
#@ int (label = "low resolution image rescale factor", default=4, min=0, max=10 ) size
#@ int (label = "octave_size", default=800, min=0, max=1500 ) octave_size
#@ String(choices={"translation", "rigid", "similarity", "affine"}, style="list") model_index
#@ boolean (label = "using a windows machine") windows
#@ boolean (label = "run test(if your low resolution has not been rescaled)") test

# import modules
# ----------------------------------------------------------------------------------------
#might not need all these modules
import os, re, sys

#script_path=os.path.abspath(__file__)
script_path = os.path.dirname(sys.argv[0]) 
sys.path.append(script_path)
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
tiles_list=[]
project_list=[]
file_keys_big_list=[]
file_values_big_list=[]
proj_folds=[]
project=''
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
folder_2 = folder_2.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()

#flush image cache every 60 seconds?
exe = Executors.newSingleThreadScheduledExecutor()
exe.scheduleAtFixedRate(releaseAll, 0, 60, TimeUnit.SECONDS)

#main
# --------------------------------------------------------------------------------------
grand_joint_folder=mut_fold(folder,folder_2,windows)
OV_folder_list=folder_find(folder,windows)
NO_folder_list=folder_find(folder_2,windows)
if test:
	test_dir= make_dir(grand_joint_folder,  "test_0_"+project_name) #make test directory
proj_dir= make_dir(grand_joint_folder,  "trakem2_files_"+project_name) #make project directory
#large_OV_interim= make_dir(grand_joint_folder, "OV_interim")
if inverted_image: 
	large_NO_interim= make_dir(grand_joint_folder, "high_res_interim") #make inverted image directory
if len(OV_folder_list) != len(NO_folder_list):
	sys.exit("need same folder number for low and high res" ) #find files and paths and test alignment for each substack
for num in range(0,len(OV_folder_list)):
	temp_proj_name=project_name+"_"+str(num)
	joint_folder=mut_fold(OV_folder_list[num],NO_folder_list[num],windows)  #find tile directories for each substack
	sub_OV_folders=folder_find(OV_folder_list[num], windows) #find tile directories for each substack
	sub_OV_folders=file_sort(sub_OV_folders, -1) #sort
	all_folder_list=folder_find(NO_folder_list[num],  windows, sub_OV_folders)
	# all_folder_list=folder_find(NO_folder_list[num],  windows, OV_folder_list[num])
	filenames_keys, filenames_values=file_find(all_folder_list, pattern_1, pattern_3)
	print("folder and its content registered")
	# print(filenames_keys, filenames_values)
	if test:
		dup_find(filenames_keys,filenames_values)
		#Creates a TrakEM2 project
		sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))  #make substack specific project folder
		file_list= os.listdir(sub_dir) # get list of all images in substack
		if temp_proj_name+"test.xml" in file_list: #checks whether project already exists
			gui = GUI.newNonBlockingDialog("Overwrite?")
			gui.addMessage(" Press ok to overwrite project file?")
			gui.showDialog()
			if gui.wasOKed():
				if windows:
					os.remove(sub_dir+"\\"+temp_proj_name+"test.xml")
				if not windows:
					os.remove(sub_dir+"/"+temp_proj_name+"test.xml")
			elif not gui.wasOKed():
				sys.exit()
		project = Project.newFSProject("blank", None, sub_dir) #Creates a TrakEM2 project
		#creates initial collection of layers variable
		layerset = project.getRootLayerSet() #creates initial collection of layers variable
		#create cropped area 
		temp_filenames_keys,temp_filenames_values = prep_test_align(filenames_keys[1:], 
																	filenames_values[1:], 
																	test_dir, windows, 
																	temp_proj_name, invert_image, size)
		temp_filenames_keys = [filenames_keys[0]]+temp_filenames_keys
		temp_filenames_values =	[filenames_values[0]]+temp_filenames_values									
		# print(temp_filenames_keys, temp_filenames_values)
		layerset=add_patch(temp_filenames_keys,temp_filenames_values, project, 0, 1) #creates layerset and adds images
		roi, tiles =align_layers(model_index, octave_size, layerset)  #aligns images
		project.saveAs(os.path.join(proj_dir, temp_proj_name+"test"), False)
		layerset.setMinimumDimensions() #readjust canvas to only NO tiles
		tiles_list.append(tiles)
		roi_list.append(roi)
		#fix for windows
		project_list.append(temp_proj_name+"test.xml")
	file_keys_big_list.append(filenames_keys)
	file_values_big_list.append(filenames_values)
# print(file_keys_big_list)	
if test:	
	#find max ROI
	#potential gui
	while 1: #increases maximum image size parameters by 200 if the images did not align
		gui = GUI.newNonBlockingDialog("Aligned?")
		gui.addMessage("Inspect alignment results. Are tiles aligned properly?\n If not pressing cancel will increase octave size\n (Maximum Image Size parameter) by 200 px. ")
		gui.showDialog()
		if gui.wasOKed():
#			for num in range(0,len(OV_folder_list)):
#				project = Project.getProject(project_list[num])
#				project.remove(False)
#				project.removeProjectThing(layerset,False, True,1)
			break
		else:
			roi_list=[]
			octave_size=octave_size+200
			for num in range(0,len(OV_folder_list)):
				project = Project.getProject(project_list[num]) #assumes that there are no other projects open
				roi, tiles =align_layers(model_index, octave_size, layerset)
				roi_list.append(roi)
				tiles_list.append(tiles)
	print(roi_list)
	max_roi=max(roi_list)
	print(max_roi)

try: #if not running test opens up previous test project file, clunky way deciding between test mode or not
	project_list[1]
except IndexError:
	proj_folds=folder_find(proj_dir,windows) #looks for previous test project file, add function functionality to send gui if you want to make a new folder
	print(proj_folds)
	for proj in proj_folds:
		xml_file=filter(pattern_xml.match, os.listdir(proj))
		xml_filepath = os.path.join(proj,xml_file[0])
		for proj in Project.getProjects():
			if (xml_file[0].split("."))[0] in str(proj):
				project = Project.getProject(proj)
				break
		if not project:
			project=Project.openFSProject(xml_filepath, True)
		project_list.append(project)
		project=''
project_list=file_sort(project_list)
print(project_list)
#inverts image
for num in range(0,len(OV_folder_list)):
	temp_proj_name=project_name+"_"+str(num)
	print((project_list[num]))
	print(type(project_list[num]))
	project = Project.getProject(project_list[num])
	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))
	print(project)
	try:
		remove_tiles(tiles_list[num])
	except IndexError:
		print(project)
		layerset = project.getRootLayerSet()
		for layer in layerset.getLayers():
		  	tiles = layer.getDisplayables(Patch)
		  	remove_tiles(tiles)
	filenames_keys=file_keys_big_list[num]
	filenames_values=file_values_big_list[num]
	print("this is before cropped")
	if test:
		if inverted_image:
			#make list of filenammes keys and values for each project
			output_inverted=make_dir(large_NO_interim, "high_res_interim"+str(num))
			filenames_keys, filenames_values = invert_image(filenames_keys, filenames_values, output_inverted, windows, pattern_3)
		#crop image
		if size != 1:
			large_OV_interim= make_dir(grand_joint_folder, "low_res_interim")
			output_scaled=make_dir(large_OV_interim, "low_res_interim"+str(num))
			filenames_keys, filenames_values = resize_image(filenames_keys, 
															filenames_values, 
															output_scaled, windows, 
															temp_proj_name, pattern_3, size, max_roi)
	print("files potentially cropped and or inverted")
	# print(filenames_keys, filenames_values)
	file_keys_big_list[num]=filenames_keys #refreshes to correct filepaths and file names
	file_values_big_list[num]=filenames_values

for num in range(0,len(OV_folder_list)): #this is where the actually alignment takes place
	temp_proj_name=project_name+"_"+str(num)
	project = Project.getProject(project_list[num]) #selects appropriate project for image substack
	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))  #makes a directory for this project if not already done
	filenames_keys=file_keys_big_list[num]#gets correct filepaths and file names
	filenames_values=file_values_big_list[num]
	#add stack to trakem2	
	#fix add_patch	
	print("prepared tile order for best overlay")
#	layerset=add_patch(filenames_keys, filenames_values, project, 1, len(filenames_values[0]))												
	layerset=add_patch(filenames_keys, filenames_values, project, 0, len(filenames_values[0]))
	#align high to low res image 
	align_layers(model_index, octave_size, layerset)
	#	Saves the project with OV
	if proj_folds:
		project.saveAs(os.path.join(proj_folds[num], temp_proj_name+"with_low_res"), False)
	else:
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"with_low_res"), False)
	#removes the OV tile
	layerset.setMinimumDimensions() #readjust canvas to only high res tiles
	#remove OV from layers
	remove_OV(layerset,0)
	#exports images
	mini_dir= make_dir(output_dir,  "export_"+str(num))
	export_image(layerset, mini_dir, canvas_roi=True)#, processed=False)
	#	Saves the project without OV
	if proj_folds:
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"without_low_res"), False)
	else:
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"without_low_res"), False)
print("Done!")