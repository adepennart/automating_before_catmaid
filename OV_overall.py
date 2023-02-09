"""
Title: low_res.py

Date: February 9th, 2023

Author: Auguste de Pennart

Description:
	aligns images in the Z plane and montages them in the x-y plane in trakem2 on imagej(useful for OV image stacks)

List of functions:
    No user defined functions are used in the program.

List of "non standard modules"
	module functions.py used for this script

Procedure:
	1. runs test if specificed to find best balues for montaging
	2. when alignment successful, creates inverted interim folder if inverted specificed 
	3. creates cropped image interim folder for best quality final results
	4. using Trakem2, images aligned and montaged
	5. images are exported
	6. project file is created to access images in trakem2

Usage:
	to be used through Imagej as a script
	Pressing the bottom left Run button in the Script window will present user with prompt window for running script

known error:
    1. only accepts tif files as input
    2. should check if interim folder full (kind of does)
    3. get more threads for resizing step
    4. have time stamps
    5. pattern check
    6. problem with loading projects occasionally
   	7. test whether the trakem2 folders are in the right parent folders
   	8. you need two terabytes to run this script (3-4 times the space it currently takes)
   	9. fix the fact that is calls the files duplicate...
 	10. elastic alignment could be a useful feature
   	11. as well as clahe on the alignemt, supposedly alignment runs better
   	12. montaging should stay as translation, however minor adjustments should be made to increase speed
	13. (after test align)fix project name save for windows?
	14. (during realignment for test) assumes that there are no other projects open
	15. place holder variable assoc_roi made when only one image in layer
	16. (when test is already run and fetching old test trakem2 file)if not running test opens up previous test project file, clunky way deciding between test mode or not
    16.1 if it does not find the test trakem2 file crashes
	17. (right before actual alignment)can optimize code by add all patches at once #don't need this if
	18. (right before actual alignment) issue here where there is a project loaded with the same name
	19. can number of threads be changed durign alignment
	20. don't need if statement when saving project after z alignment


    
based off of Albert Cardona 2011-06-05 script
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
import shutil
script_path = os.path.dirname(sys.argv[0]) #get filepath to functions.py
sys.path.append(script_path)#could accept error and say to place functions.py in same folder as OV_overall
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

#get string of folder paths
folder = folder.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()

#flush image cache every 60 seconds?
exe = Executors.newSingleThreadScheduledExecutor()
exe.scheduleAtFixedRate(releaseAll, 0, 60, TimeUnit.SECONDS)

#main
# --------------------------------------------------------------------------------------
#make folders
grand_joint_folder=mut_fold(folder,output_dir,windows) #make parent directory
OV_folder_list=folder_find(folder,windows) # get OV subdirectories
OV_folder_list=file_sort(OV_folder_list, -1) #sort
if test:
	test_dir= make_dir(grand_joint_folder,  "test_0_"+project_name) #make test directory
proj_dir= make_dir(grand_joint_folder,  "trakem2_files_"+project_name) #make project directory
if inverted_image: 
	large_OV_interim= make_dir(grand_joint_folder, "invert_interim_1"+project_name) #make inverted image directory
for num in range(0,len(OV_folder_list)): #find files and paths and test alignment for each substack
	temp_proj_name=project_name+"_"+str(num)
	sub_OV_folders=folder_find(OV_folder_list[num], windows) #find tile directories for each substack
	sub_OV_folders=file_sort(sub_OV_folders, -1) #sort
	filenames_keys, filenames_values=file_find(sub_OV_folders, pattern_1, pattern_3)
	print("folder and its content registered")
#	print(filenames_keys, filenames_values)
	if test:
		sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num)) #make substack specific project folder
		file_list= os.listdir(sub_dir) # get list of all images in substack
#		print(file_list)
#		print(temp_proj_name+"test")
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
		#project.adjustProperties() #adjust properties window, not needed as we are going to avoid using mipmap to reduce storage space
		layerset = project.getRootLayerSet() #creates initial collection of layers variable
		temp_filenames_keys,temp_filenames_values = prep_test_align(filenames_keys, #inverts images for test alignment
													filenames_values, 
													test_dir, windows, 
													temp_proj_name, inverted_image)
		layerset=add_patch(temp_filenames_keys,temp_filenames_values, project, 0, 1)#creates layerset and adds images
		roi, tiles =align_layers(model_index, octave_size, layerset,True) #aligns images
		layerset.setMinimumDimensions() #readjust canvas to minimum dimensions
		# print(roi, tiles)
		if len(filenames_keys) != 1: #gets the overlap coordinates of aligned images 
			new_roi, assoc_roi =overlap_area(roi)
			# print(new_roi, assoc_roi, roi)
			crop_roi_list.append(new_roi)
			assoc_roi_list.append(assoc_roi)
		else:
			crop_roi_list.append(roi)
			assoc_roi_list.append(roi) #place holder variable
		roi_list.append(roi)
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"test"), False)	#save test run						
		tiles_list.append(tiles)
		project_list.append(temp_proj_name+"test.xml") #fix for windows
#		print(filenames_keys, filenames_values)
	file_keys_big_list.append(filenames_keys)
	file_values_big_list.append(filenames_values)
if test:	
	while 1: #increases maximum image size parameters by 200 if the images did not align
		gui = GUI.newNonBlockingDialog("Aligned?")
		gui.addMessage("Inspect alignment results. Are tiles aligned properly?\n If not pressing cancel will increase octave size\n (Maximum Image Size parameter) by 200 px. ")
#		gui.addMessage("Inspect alignment results. If there is any jitter (that isn't already present\n in the OV itself), manually fix this by re-running the alignment with updated\n parameters (i.e., try increasing Maximum Image Size parameter by\n 200 px.)\n\n Check image tile overlap and blend if desired.\n (Note: There is no 'Undo' for blending).\n\n If you would like to revert to previous state, use project 'montage_checkpoint.xml'.\n\n When image alignment is satisfactory, select 'Export'. A project .xml file\n will be saved in <dir> with user changes. Images will be exported as .tif to <dir>.")
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
					#print(new_roi)
					crop_roi_list.append(new_roi)
					assoc_roi_list.append(assoc_roi)
				else:
					crop_roi_list.append(roi)
					assoc_roi_list.append(roi) #place holder variable
				roi_list.append(roi)
				tiles_list.append(tiles)

try: #if not running test opens up previous test project file, clunky way deciding between test mode or not
	project_list[1]
except IndexError:
	proj_folds=folder_find(proj_dir,windows) #looks for previous test project file, add function functionality to send gui if you want to make a new folder
	proj_folds=file_sort(proj_folds, -1) 
	#print(proj_folds)
	projects=Project.getProjects()
	for proj in proj_folds:
		xml_file=filter(pattern_xml.match, os.listdir(proj))
		xml_filepath = os.path.join(proj,xml_file[0])
#		print(Project.getProjects())
#		print(type(Project.getProjects().get(0)))
#		print((xml_file[0].split("."))[0])
		for projected in projects: # finds test project file if open in trakem2
			if (xml_file[0].split("."))[0] in str(projected):
				project = Project.getProject(projected)
				break
		if not project: #finds test project file in directory and opens it
			project=Project.openFSProject(xml_filepath, True)
		project_list.append(project)
		project=''
#project_list=file_sort(project_list)
#print(project_list)
for num in range(0,len(OV_folder_list)): #this is for adjusting images to be cropped and, if necessary, inverted
	temp_proj_name=project_name+"_"+str(num)
	#print((project_list[num]))
	#print(type(project_list[num]))
#	print(match[0])
	project = Project.getProject(project_list[num]) #selects appropriate project for image substack
	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num)) #makes a directory for this project if not already done
	#print(project)
	try: #removes images present from the test trakem2 project
		remove_tiles(tiles_list[num])
	except IndexError:
		#print(project)
		layerset = project.getRootLayerSet()
		for layer in layerset.getLayers():
			tiles = layer.getDisplayables(Patch)
			remove_tiles(tiles)
	filenames_keys=file_keys_big_list[num] #gets appropriate substack filepaths and images
	filenames_values=file_values_big_list[num]
	print("this is before cropped")
	# print(filenames_keys, filenames_values)
	if test:
		if inverted_image:
			#print(roi_list, crop_roi_list)
 			output_inverted=make_dir(large_OV_interim, "inv_substack"+str(num)) #makes inverted substack folder
			filenames_keys, filenames_values = invert_image(filenames_keys, filenames_values, output_inverted, windows, pattern_3,0) #inverts images
			if len(filenames_keys) != 1: #crops images if more than one image tile per layer
				large_OV_interim_2= make_dir(grand_joint_folder, "crop_interim_2_"+project_name) #makes crop folder
				output_scaled=make_dir(large_OV_interim_2, "crop_substack"+str(num)) #makes crop substack folder
				# print(output_scaled, roi_list[num], crop_roi_list[num],assoc_roi_list[num])
				filenames_keys, filenames_values = remove_area(filenames_keys, #crops overlap area
																filenames_values, 
																output_scaled, windows, 
																temp_proj_name, pattern_3, roi_list[num], crop_roi_list[num], assoc_roi_list[num])
#		#crop image
		elif not inverted_image: #crops overlap area without inverting
			if len(filenames_keys) != 1:
				large_OV_interim_2= make_dir(grand_joint_folder, "crop_interim_1_"+project_name)
				output_scaled=make_dir(large_OV_interim_2, "crop_substack"+str(num))
				filenames_keys, filenames_values = remove_area(filenames_keys, 
																filenames_values, 
																output_scaled, windows, 
																temp_proj_name, pattern_3, roi_list[num], crop_roi_list[num], assoc_roi_list[num])
				
	print("files potentially cropped and or inverted")
#	print(filenames_keys, filenames_values)
	file_keys_big_list[num]=filenames_keys #refreshes to correct filepaths and file names
	file_values_big_list[num]=filenames_values
	
for num in range(0,len(OV_folder_list)): #this is where the actually alignment takes place
	temp_proj_name=project_name+"_"+str(num)
	#print((project_list[num]))
	#print(type(project_list[num]))
#	print(match[0])
	project = Project.getProject(project_list[num]) #selects appropriate project for image substack
	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))  #makes a directory for this project if not already done
	#print(project)
	#print([filenames_keys[0]], filenames_values[0])										
	filenames_keys=file_keys_big_list[num]#gets correct filepaths and file names
	filenames_values=file_values_big_list[num]
	filenames_keys=file_sort(filenames_keys,0,True) #reorders them from right most to left most image
	filenames_values=file_sort(filenames_values,0,True)
	# print(filenames_keys, filenames_values)
	print("prepared tile order for best overlay")
	layerset=add_patch([filenames_keys[0]], [filenames_values[0]], project, 0, len(filenames_values[0])) #makes layers and adds images to them
	if len(filenames_keys) != 1: #don't need this if
		layerset=add_patch(filenames_keys[1:], filenames_values[1:], project, 0, 0) #issue here where there is a project loaded with the same name
		align_layers(model_index, octave_size, layerset) #could change number of threads
	layerset.setMinimumDimensions() 
	project.saveAs(os.path.join(sub_dir, temp_proj_name+"stiched"), False) #save project file before z alignment
	AlignLayersTask.alignLayersLinearlyJob(layerset,0,len(layerset.getLayers())-1,False,None,None) #z alignment
	#print(sub_dir, temp_proj_name+"aligned")
	layerset.setMinimumDimensions() 
	if proj_folds:
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"aligned"), False) #save project file final time, after z alignment
	else:
		project.saveAs(os.path.join(sub_dir, temp_proj_name+"aligned"), False)
	#exports images
	mini_dir= make_dir(output_dir,  "export_"+str(num)) #makes output subdirectory
	export_image(layerset, mini_dir, canvas_roi=True)#, processed=False) #exports images
print("Done!")