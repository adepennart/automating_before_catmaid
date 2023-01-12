"""
Title: OV_overall.py

Date: December 22nd, 2022

Author: Auguste de Pennart

Description:
	aligns images in the Z plane and montages them in the x-y plane (useful for OV image stacks)

List of functions:
    No user defined functions are used in the program.

List of "non standard modules"
	module functions.py used for this script

Procedure:

	1. runs test if specificed to find best balues for montaging
	2. when alignment successful, creates interim interim folder if inverted specificed 
	3. creates cropped image interim folder for best quality final results
	4. using Trakem2, images aligned and montaged
	5. images are exported
	6. project file is createdt to access images in trakem2

Usage:
	to be used through Imagej as a script
	Pressing the bottom left Run button in the Script window will present user with prompt window for running script

known error:
    1. only accepts tif files as input
    5. should check if interim folder full (kind of does)
    6. get more threads for resizing step
    9. have time stamps
    12. whe nrunning without test, if trackem2 project already open will not run, needs to be opened to work
    16. pattern check
    17. should be able to fix, inversion, which layer goes where and model used for montage(affine, translation etc.)
   	18. if one tile shouldn't bother aligning
   	19. pulled out aligned porject not test
   	20. test whether the trakem2 folders are in the right parent folders
   	22. you need two terabytes to run this script (3-4 times the space it currently takes)
   	
    
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
#alignMultiLayerMosaicTask(layerset.getLayers(), Patch nail, Align.Param cp, Align.ParamOptimize p, Align.ParamOptimize pcp, False, False, False, False, False) 

"""

#@ File (label = "OV directory", style = "directory") folder
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ boolean (label = "Invert images") inverted_image
#@ int (label = "octave_size", default=800, min=0, max=1500 ) octave_size
#@ String(choices={"translation", "rigid", "similarity", "affine"}, style="list") model_index
#@ boolean (label = "using a windows machine") windows
#@ boolean (label = "run test(if OV has not been inverted)") test

# import modules
# ----------------------------------------------------------------------------------------
#might not need all these modules
import os, re, sys

#print(os.path.realpath(__file__))
#script_path=os.path.realpath(__file__)
#script_path=os.path.abspath(__file__)
script_path = os.path.dirname(sys.argv[0]) 
sys.path.append(script_path)

#could accept error and say to place functions.py in same folder as OV_overall

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
if test:
	test_dir= make_dir(grand_joint_folder,  "test_0_"+project_name)
proj_dir= make_dir(grand_joint_folder,  "trakem2_files_"+project_name)
if inverted_image:
	large_OV_interim= make_dir(grand_joint_folder, "invert_interim_1"+project_name)
#find files and paths and test alignment for each substack
for num in range(0,len(OV_folder_list)):
	temp_proj_name=project_name+"_"+str(num)
	sub_OV_folders=folder_find(OV_folder_list[num], windows)
#	filenames_keys, filenames_values=file_find(sub_OV_folders, pattern_1, pattern_2)
	filenames_keys, filenames_values=file_find(sub_OV_folders, pattern_1, pattern_3)
#	print(filenames_keys, filenames_values)
	if test:
		sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))
		file_list= os.listdir(sub_dir)
#		print(file_list)
#		print(temp_proj_name+"test")
		if temp_proj_name+"test.xml" in file_list:
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
		project.adjustProperties() #adjust properties window
		layerset = project.getRootLayerSet() #creates initial collection of layers variable
		#also should crop too
		temp_filenames_keys,temp_filenames_values = prep_test_align(filenames_keys, 
													filenames_values, 
													test_dir, windows, 
													temp_proj_name, inverted_image)
		layerset=add_patch(temp_filenames_keys,temp_filenames_values, project, 0, 1)
		roi, tiles =align_layers(model_index, octave_size, layerset,True)
		layerset.setMinimumDimensions() #readjust canvas to only NO tiles
		#print(roi)
		if len(filenames_keys) != 1: 
			new_roi, assoc_roi =overlap_area(roi)
		#	print(new_roi)
			crop_roi_list.append(new_roi)
			assoc_roi_list.append(assoc_roi)
		else:
			crop_roi_list.append(roi)
			#not sure if needed
			assoc_roi_list.append(roi)
		roi_list.append(roi)
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"test"), False)							
		tiles_list.append(tiles)
		#fix for windows
		project_list.append(temp_proj_name+"test.xml")
#		print(filenames_keys, filenames_values)
	file_keys_big_list.append(filenames_keys)
	file_values_big_list.append(filenames_values)
	#	Saves the project without OV
	#not ideal should save differently if windows
	#print(roi_list)
#print(file_keys_big_list)
	
if test:	
	while 1: 
		gui = GUI.newNonBlockingDialog("Aligned?")
		gui.addMessage("Inspect alignment results. If there is any jitter (that isn't already present\n in the OV itself), manually fix this by re-running the alignment with updated\n parameters (i.e., try increasing Maximum Image Size parameter by\n 200 px.)\n\n Check image tile overlap and blend if desired.\n (Note: There is no 'Undo' for blending).\n\n If you would like to revert to previous state, use project 'montage_checkpoint.xml'.\n\n When image alignment is satisfactory, select 'Export'. A project .xml file\n will be saved in <dir> with user changes. Images will be exported as .tif to <dir>.")
		gui.showDialog()
		if gui.wasOKed():
			break
		else:
			roi_list=[]
			octave_size=octave_size+200
			for num in range(0,len(OV_folder_list)):
				project = Project.getProject(project_list[num]) #assumes that there are no other projects open
				roi, tiles =align_layers(model_index, octave_size, layerset)
				if len(filenames_keys) != 1: 
					new_roi, assoc_roi =overlap_area(roi)
					print(new_roi)
					crop_roi_list.append(new_roi)
					assoc_roi_list.append(assoc_roi)
				else:
					crop_roi_list.append(roi)
					#not sure if needed
					assoc_roi_list.append(roi)
				roi_list.append(roi)
				tiles_list.append(tiles)

try:
	project_list[1]
except IndexError:
	proj_folds=folder_find(proj_dir,windows) #add function functionality to send gui if you want to make a new folder
	#print(proj_folds)
	projects=Project.getProjects()
	for proj in proj_folds:
		xml_file=filter(pattern_xml.match, os.listdir(proj))
		xml_filepath = os.path.join(proj,xml_file[0])
#		print(Project.getProjects())
#		print(type(Project.getProjects().get(0)))
#		print((xml_file[0].split("."))[0])
		for projected in projects:
			if (xml_file[0].split("."))[0] in str(projected):
				project = Project.getProject(projected)
				break
		if not project:
			project=Project.openFSProject(xml_filepath, True)
		project_list.append(project)
		project=''
project_list=file_sort(project_list)
#print(project_list)
#inverts image
for num in range(0,len(OV_folder_list)):
	temp_proj_name=project_name+"_"+str(num)
	#print((project_list[num]))
	#print(type(project_list[num]))
#	print(match[0])
	project = Project.getProject(project_list[num])
	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))
	#print(project)
	try:
		remove_tiles(tiles_list[num])
	except IndexError:
		#print(project)
		layerset = project.getRootLayerSet()
		for layer in layerset.getLayers():
		  	tiles = layer.getDisplayables(Patch)
			remove_tiles(tiles)
	filenames_keys=file_keys_big_list[num]
	filenames_values=file_values_big_list[num]
	print(filenames_keys, filenames_values)
	if test:
		if inverted_image:
			#make list of filenammes keys and values for each project
			#print(roi_list, crop_roi_list)
			output_inverted=make_dir(large_OV_interim, "inv_substack"+str(num))
			filenames_keys, filenames_values = invert_image(filenames_keys, filenames_values, output_inverted, windows, pattern_3,0)
			if len(filenames_keys) != 1:
				large_OV_interim_2= make_dir(grand_joint_folder, "crop_interim_2_"+project_name)
				output_scaled=make_dir(large_OV_interim_2, "crop_substack"+str(num))
				#print(output_scaled, roi_list[num], crop_roi_list[num])
				filenames_keys, filenames_values = remove_area(filenames_keys, 
																filenames_values, 
																output_scaled, windows, 
																temp_proj_name, pattern_3, roi_list[num], crop_roi_list[num], assoc_roi_list[num])
		#crop image
		elif not inverted_image:
			if len(filenames_keys) != 1:
				large_OV_interim_2= make_dir(grand_joint_folder, "crop_interim_1_"+project_name)
				output_scaled=make_dir(large_OV_interim_2, "crop_substack"+str(num))
				filenames_keys, filenames_values = remove_area(filenames_keys, 
																filenames_values, 
																output_scaled, windows, 
																temp_proj_name, pattern_3, roi_list[num], crop_roi_list[num], assoc_roi_list[num])
	print(filenames_keys, filenames_values)
	#print([filenames_keys[0]], filenames_values[0])										
	filenames_keys=file_sort(filenames_keys,0,True)
	filenames_values=file_sort(filenames_values,0,True)
	print(filenames_keys, filenames_values)
	#add stack to trakem2
	layerset=add_patch([filenames_keys[0]], [filenames_values[0]], project, 0, len(filenames_values[0]))
	AlignLayersTask.alignLayersLinearlyJob(layerset,0,len(layerset.getLayers())-1,False,None,None)
	if len(filenames_keys) != 1:
		layerset=add_patch(filenames_keys[1:], filenames_values[1:], project, 0, 0)
		align_layers(model_index, octave_size, layerset)
	#print(sub_dir, temp_proj_name+"aligned")
	if proj_folds:
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"aligned"), False)
	else:
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"aligned"), False)
	#removes the OV tile
	layerset.setMinimumDimensions() #readjust canvas to only NO tiles
	#exports images
	mini_dir= make_dir(output_dir,  "export_"+str(num))
	export_image(layerset, mini_dir)#, canvas_roi=False, processed=False)
	export_image(layerset, mini_dir, canvas_roi=True)#, canvas_roi=False, processed=False)

print("Done!")