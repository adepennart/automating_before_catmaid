"""
Title: no_alignment.py

Date: September 7th, 2022

Author: Auguste de Pennart

Description:
	aligns the noduli high resolution images to the overview low resolution images 

List of functions:
    No user defined functions are used in the program.

List of "non standard modules"
	No non standard modules are used in the program.

Procedure:



    1. multiple checks to ensure function
    2. scales OV stack to 4x magnification
    3. creates trakem2 project
    4. creates layers and populates with one image from OV and from NO folders
    5. aligns them/montages them
    6. exports NO images

Usage:
	to be used through Imagej as a script
	Pressing the bottom left Run button in the Script window will begin script

known error:
    1. only accepts tif files as input
    5. should check if interim folder full (kind of does)
    6. get more threads for resizing step
    8. should open project, if already opened
    9. have time stamps
    11. if folder name is the same but different folders , returns error
    12. whe nrunning without test, if trackem2 project already open will not run, needs to be opened to work
    13. OV interim is not full if not scaled
    14. pattern change if you are using NO_interim
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

#@ File (label = "OV directory", style = "directory") folder
#@ File (label = "NO directory or parent directory only containing NO directories", style = "directory") folder_2
##@ File (label = "OV interim directory", style = "directory") output_scaled
#this needs to be silent
##@ File (label = "test interim directory", style = "directory",required=False) test_interim
##@ File (label = "NO interim directory", style = "directory",required=False) output_inverted
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ boolean (label = "Invert HR images") inverted_image
#@ int (label = "rescale OV factor", default=4, min=0, max=10 ) size
#@ int (label = "octave_size", default=800, min=0, max=1500 ) octave_size
#@ String(choices={"translation", "rigid", "similarity", "affine"}, style="list") model_index
#@ boolean (label = "using a windows machine") windows
#@ boolean (label = "run test(if your OV has not been rescaled)") test

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
#joint_folder=[]
pattern_1 = re.compile(".*_z[\d]_.*\.tif")
#pattern_1 = re.compile("([\d]+).*\.tif")
pattern_2 = re.compile(".*_z[\d]_.*\.tif")
#pattern_2 = re.compile(".*-([\d]{3})-([\d]+)_.*\.tif")
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


#main
# --------------------------------------------------------------------------------------
grand_joint_folder=mut_fold(folder,folder_2,windows)
OV_folder_list=folder_find(folder,windows)
NO_folder_list=folder_find(folder_2,windows)
test_dir= make_dir(grand_joint_folder,  "test_"+project_name)
proj_dir= make_dir(grand_joint_folder,  "trakem2_files_"+project_name)
#large_OV_interim= make_dir(grand_joint_folder, "OV_interim")
large_NO_interim= make_dir(grand_joint_folder, "NO_interim")
if len(OV_folder_list) != len(NO_folder_list):
	sys.exit("need same folder number for OV and NO" )
for num in range(0,len(OV_folder_list)):
	temp_proj_name=project_name+"_"+str(num)
	joint_folder=mut_fold(OV_folder_list[num],NO_folder_list[num],windows)
	all_folder_list=folder_find(NO_folder_list[num],  windows, OV_folder_list[num])
#	filenames_keys, filenames_values=file_find(all_folder_list, pattern_1, pattern_2)
	filenames_keys, filenames_values=file_find(all_folder_list, pattern_1, pattern_3)
	print(filenames_keys, filenames_values)
	if test:
		dup_find(filenames_keys,filenames_values)
		#Creates a TrakEM2 project
		sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))
		file_list= os.listdir(sub_dir)
		if temp_proj_name+"test.xml" in file_list:
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
		project = Project.newFSProject("blank", None, sub_dir)
		# OR: get the first open project
		# project = Project.getProjects().get(0)
		#adjust properties window
		project.adjustProperties()
		#creates initial collection of layers variable
		layerset = project.getRootLayerSet()
		#create cropped area 
		#needs to edit
		temp_filenames_keys,temp_filenames_values = prep_test_align(filenames_keys[1:], 
																	filenames_values[1:], 
																	test_dir, windows, 
																	temp_proj_name, invert_image, size)
		temp_filenames_keys = [filenames_keys[0]]+temp_filenames_keys
		temp_filenames_values =	[filenames_values[0]]+temp_filenames_values									
#		roi, tiles = prep_test_align(filenames_keys, 
#							filenames_values, project, 
#							test_dir, sub_dir, windows, 
#							temp_proj_name, model_index,
#							octave_size, invert_image)
		print(temp_filenames_keys, temp_filenames_values)
		layerset=add_patch(temp_filenames_keys,temp_filenames_values, project, 0, 1)
		roi, tiles =align_layers(model_index, octave_size, layerset)
		project.saveAs(os.path.join(proj_dir, temp_proj_name+"test"), False)
		layerset.setMinimumDimensions() #readjust canvas to only NO tiles
		tiles_list.append(tiles)
		roi_list.append(roi)
		#fix for windows
		project_list.append(temp_proj_name+"test.xml")
	file_keys_big_list.append(filenames_keys)
	file_values_big_list.append(filenames_values)
	#	Saves the project without OV
	#not ideal should save differently if windows
#	project.saveAs(os.path.join(sub_dir, project_name+"_test"), False)
	#print(roi_list)
	#not sure how max works here
print(file_keys_big_list)
		
if test:	
	#find max ROI
	#potential gui
	while 1: 
		gui = GUI.newNonBlockingDialog("Aligned?")
		gui.addMessage("Inspect alignment results. If there is any jitter (that isn't already present\n in the OV itself), manually fix this by re-running the alignment with updated\n parameters (i.e., try increasing Maximum Image Size parameter by\n 200 px.)\n\n Check image tile overlap and blend if desired.\n (Note: There is no 'Undo' for blending).\n\n If you would like to revert to previous state, use project 'montage_checkpoint.xml'.\n\n When image alignment is satisfactory, select 'Export'. A project .xml file\n will be saved in <dir> with user changes. Images will be exported as .tif to <dir>.")
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

try:
	project_list[1]
except IndexError:
	proj_folds=folder_find(proj_dir,windows)
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
#	xml_file=filter(pattern_xml.match, os.listdir(proj_folds[num]))
#	xml_filepath = os.path.join(proj_folds[num],xml)
#	project.openFSProject(xml_filepath, True)
#	match=re.search("(.+)\.xml",project_list[num]).group()
#	match=re.findall("(.+)\.xml",project_list[num])
#	print(match[0])
#	project = Project.getProject(str(match[0]))
	project = Project.getProject(project_list[num])
	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))
#	project = Project.newFSProject("blank", None, sub_dir)
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
	if test:
		if inverted_image:
			#make list of filenammes keys and values for each project
			output_inverted=make_dir(large_NO_interim, "NO_interim"+str(num))
			filenames_keys, filenames_values = invert_image(filenames_keys, filenames_values, output_inverted, windows, pattern_3)
		#crop image
		if size != 1:
			large_OV_interim= make_dir(grand_joint_folder, "OV_interim")
			output_scaled=make_dir(large_OV_interim, "OV_interim"+str(num))
			filenames_keys, filenames_values = resize_image(filenames_keys, 
															filenames_values, 
															output_scaled, windows, 
															temp_proj_name, pattern_3, size, max_roi)
	print(filenames_keys, filenames_values)
	#add stack to trakem2	
	#fix add_patch	
#	layerset=add_patch(filenames_keys, filenames_values, project, 1, len(filenames_values[0]))												
	layerset=add_patch(filenames_keys, filenames_values, project, 0, len(filenames_values[0]))
	#align NO to OV
	align_layers(model_index, octave_size, layerset)
	#	Saves the project with OV
	if proj_folds:
		project.saveAs(os.path.join(proj_folds[num], temp_proj_name+"with_OV"), False)
	else:
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"with_OV"), False)
	#removes the OV tile
	layerset.setMinimumDimensions() #readjust canvas to only NO tiles
	#remove OV from layers
	remove_OV(layerset,0)
	#exports images
	mini_dir= make_dir(output_dir,  "export_"+str(num))
	export_image(layerset, mini_dir)#, canvas_roi=False, processed=False)
	#	Saves the project without OV
	if proj_folds:
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"without_OV"), False)
	else:
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"without_OV"), False)
print("Done!")