
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
	21. haven't found option to not display "want to save/delete from database"
	22. option to remove test files could be interesting
	23. resize should be an option after test


    
based off of Albert Cardona 2011-06-05 script
"""
#@ File (label = "Input directory", style = "directory") folder
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ boolean (label = "Invert images") inverted_image
#@ float (label = "octave_size", default=800, min=0, max=1500 ) octave_size
#@ String(choices={"translation", "rigid", "similarity", "affine"}, style="list") model_index
#@ boolean (label = "using a windows machine") windows
#@ boolean (label = "script previously run (alignment parameter saved in file)") rerun
##@ boolean (label = "run test(if OV has not been inverted)") test
#@ boolean (label = "Elastic Alignment") Elastic
#@ boolean (label = "Unorganized input") orgInput
##@ boolean (label = "Crop") Crop

# import modules
# ----------------------------------------------------------------------------------------
#might not need all these modules
import os, re, sys
import shutil
script_path = os.path.dirname(sys.argv[0]) #get filepath to functions.py
sys.path.append(script_path)#could accept error and say to place functions.py in same folder as OV_overall
from functions import *
from ij.gui import GenericDialog
# variables
# --------------------------------------------------------------------------------------
# Create an instance of GenericDialog
if Elastic:
    param=GUIElasticParameters()
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
scaling_number_list=[]
proj_folds=[]
transform_list=[]
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
folder_path = folder.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()
#grand_joint_folder=mut_fold(folder_path,output_dir,windows) #make parent directory #TODO figure out why not just use output_dir??
grand_joint_folder=output_dir

if orgInput:
    list_files = get_stacks(folder_path, resolution = [10,10], match_pattern = 'PB',get_info=False)
#    list_files = get_stacks(folder_path, resolution = [40,40], match_pattern = 'OV')

    
    # Split list of TIF files into stacks of overlapping files
    OV_folder_list = split_stacks(list_files)
    print(OV_folder_list)
    #filenames_keys_big, filenames_values_big, OV_folder_list= list_sampleMaker(OV_folder_list)
    filenames_keys_big, filenames_values_big, OV_folder_list=list_decoder(OV_folder_list)
    
else:
	stacks = get_file_paths_folders(folder_path)
	OV_folder_list=folder_find(folder_path,windows) # get OV subdirectories
	OV_folder_list=file_sort(OV_folder_list, -1) #sort
#	OV_folder_list=[OV_folder_list]
	print(OV_folder_list)
	
	filenames_keys_big =[]
	filenames_values_big = []
	for num, fold in enumerate(OV_folder_list): #find files and paths and test alignment for each substack
#	for num in range(0,len(OV_folder_list)): #find files and paths and test alignment for each substack
#		for num2, image in enumerate(OV_folder_list[num]):
			sub_OV_folders=folder_find(fold, windows) #find tile directories for each substack
#			sub_OV_folders=folder_find(image, windows) #find tile directories for each substack
			sub_OV_folders=file_sort(sub_OV_folders, -1) #sort
			filenames_keys, filenames_values=file_find(sub_OV_folders, pattern_1, pattern_3)
			filenames_keys_big.append(filenames_keys)
			filenames_values_big.append(filenames_values)
	print(filenames_keys_big, filenames_values_big)
#flush image cache every 60 seconds?
exe = Executors.newSingleThreadScheduledExecutor()
exe.scheduleAtFixedRate(releaseAll, 0, 60, TimeUnit.SECONDS)

#main
# --------------------------------------------------------------------------------------
if not rerun:
	test_dir= make_dir(grand_joint_folder,  "test_0_"+project_name) #make test directory
proj_dir= make_dir(grand_joint_folder,  "trakem2_files_"+project_name) #make project directory
transform_dir_big = make_dir(grand_joint_folder,"transform_parameters_"+project_name) #make transform folder
if inverted_image: 
	large_OV_interim= make_dir(grand_joint_folder, "invert_interim_1"+project_name) #make inverted image directory




for num in range(0,len(OV_folder_list)): #find files and paths and test alignment for each substack
	octave_increase = 0
	while 1:
		octave_size=(octave_size+200*octave_increase)
		temp_proj_name=project_name+"_"+str(num)
		filenames_keys=filenames_keys_big[num]
		filenames_values=filenames_values_big[num]
		print("folder and its content registered")
		if len(filenames_keys)==0:
			print("error-empty list of keys given")
			break
		print(filenames_keys, filenames_values)
		if not rerun:
			sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num)) #make substack specific project folder
			file_list= os.listdir(sub_dir) # get list of all images in substack
#			print(file_list)
#			print(temp_proj_name+"test")
			if temp_proj_name+"test.xml" in file_list: #checks whether project already exists
				gui = GUI.newNonBlockingDialog("Overwrite?")
				gui.addMessage(" Press ok to overwrite project file "+temp_proj_name+"test.xml in trakem2_files_"+project_name+"?\n Pressing cancel will exit the script.")
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
			temp_filenames_keys,temp_filenames_values,scaling_number = prep_test_align_viggo(filenames_keys, #inverts images for test alignment
														filenames_values, 
														test_dir, windows, #output_dir --> test_dir this is just a test
														temp_proj_name, inverted_image, size=True)	
			layerset=add_patch(temp_filenames_keys,temp_filenames_values, project, 0, 1)#creates layerset and adds images
#			scaling_number_list.append(scaling_number)
			if Elastic:
				#layerset_lowRes, scaling_factors=scale_image(layerset) #lowering the resolution for elastic alignment #TODO add scaling factor that increases i not alligned properly
				#print(type(layerset),type(layerset_lowRes))
				roi, tiles, transform_XML =align_layers_elastic(param, layerset,True,octave_size)
				
				#Save XML files
#				transform_dir=make_dir(transform_dir_big,"substack_"+str(num))	
#				save_xml_files(transform_XML, transform_dir)
#				transform_list.append(transform_dir)
			if not Elastic:
#				roi, tiles =align_layers(model_index, octave_size, layerset,True) #aligns images
				roi, tiles, transforms, transform_XML =align_layers(model_index, octave_size, layerset,True,True) #aligns images
#				transform_dir=make_dir(transform_dir_big,"substack_"+str(num))
#				save_xml_files(transform_XML, transform_dir)
#				transform_list.append(transform_dir)
			layerset.setMinimumDimensions() #readjust canvas to minimum dimensions
			# print(roi, tiles)
		
            
# 			This is removed since the blending doesn't use the cropping and enables more then two images two be aligned
# 			if len(filenames_keys) != 1: #gets the overlap coordinates of aligned images 
# 				new_roi, assoc_roi =overlap_area(roi)
# 				# print(new_roi, assoc_roi, roi)
# 				crop_roi_list.append(new_roi)
# 				assoc_roi_list.append(assoc_roi)
# 			else:
# 				crop_roi_list.append(roi)
# 				assoc_roi_list.append(roi) #place holder variable
# 			roi_list.append(roi)
			project.saveAs(os.path.join(sub_dir, temp_proj_name+"test"), False)	#save test run						
#			scaling_number_file=open(os.path.join(transform_dir, str(num+1)+"_scaling.txt"),"w")
#			scaling_number_file.write(str(scaling_number))
#			scaling_number_file.close()
#			tiles_list.append(tiles)
#			project_list.append(temp_proj_name+"test.xml") #fix for windows
#			print(filenames_keys, filenames_values)
			gui = GUI.newNonBlockingDialog("Aligned?")
			gui.addMessage("Inspect alignment results. Are tiles aligned properly?\n If not, pressing cancel will increase octave size\n (Maximum Image Size parameter) by 200 px. ")
    #		gui.addMessage("Inspect alignment results. If there is any jitter (that isn't already present\n in the OV itself), manually fix this by re-running the alignment with updated\n parameters (i.e., try increasing Maximum Image Size parameter by\n 200 px.)\n\n Check image tile overlap and blend if desired.\n (Note: There is no 'Undo' for blending).\n\n If you would like to revert to previous state, use project 'montage_checkpoint.xml'.\n\n When image alignment is satisfactory, select 'Export'. A project .xml file\n will be saved in <dir> with user changes. Images will be exported as .tif to <dir>.")
			gui.showDialog()
			if gui.wasOKed():
				if num > 0:
					print("hey boi")
					project.remove(True) 
				scaling_number_list.append(scaling_number)
				transform_dir=make_dir(transform_dir_big,"substack_"+str(num))
				save_xml_files(transform_XML, transform_dir)
				transform_list.append(transform_dir)
				scaling_number_file=open(os.path.join(transform_dir, str(num+1)+"_scaling.txt"),"w")
				scaling_number_file.write(str(scaling_number))
				scaling_number_file.close()
				tiles_list.append(tiles)
				project_list.append(temp_proj_name+"test.xml") #fix for windows 
				break
			if not gui.wasOKed():
				octave_increase+=1
				project.remove(True) 

		if rerun:
			break
	file_keys_big_list.append(filenames_keys)
	file_values_big_list.append(filenames_values)

print(file_keys_big_list)
print(file_values_big_list)
print(scaling_number_list)

print("initiall alignment test done")
print(len(project_list)+1, "amount of started projects")
print(len(OV_folder_list)+1, "amount of processed substacks")

try: #if not running test opens up previous test project file, clunky way deciding between test mode or not
	project_list[0]
except IndexError:
	proj_folds=folder_find(proj_dir,windows) #looks for previous test project file, add function functionality to send gui if you want to make a new folder
	proj_folds=file_sort(proj_folds, -1) 
	#print(proj_folds)
	projects=Project.getProjects()	
	transform_folds=folder_find(transform_dir_big,windows) #looks for previous test project file, add function functionality to send gui if you want to make a new folder
	transform_folds=file_sort(transform_folds, -1) 
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
	for transformed in transform_folds:#find out why only one scaling_file comes
#		print(transformed)
		scaling_file=filter(re.compile("\d+_scaling.txt").match, os.listdir(transformed))
#		transform_files=filter(re.compile("image_stack_\d+.xml").match, os.listdir(transformed))
#		print(scaling_file, transformed)
		transform_list.append(transformed)
#		transform_list.append(transform_files)
		path=os.path.join(transformed,scaling_file[0])
#		print(os.path.isfile(path))
		with open(path, 'r+') as f:
		   for line in f :
#		       print(line)
		       scaling_number_list.append(float(line))
#project_list=file_sort(project_list)
#print(project_list)

#Closes open windows to open cache memory
IJ.run("Close All")

#changed to len(projec_list) since OV_folder_list doesnt accounnt fro the empty substack
for num in range(0,len(project_list)): #this is for adjusting images to be cropped and, if necessary, inverted. 
	temp_proj_name=project_name+"_"+str(num)
	#print((project_list[num]))
	#print(type(project_list[num]))
#	print(match[0])
#	project = Project.getProject(project_list[num]) #selects appropriate project for image substack
#	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num)) #makes a directory for this project if not already done
#	#print(project)
#	try: #removes images present from the test trakem2 project
#		remove_tiles(tiles_list[num]) 
#	except IndexError:
#		#print(project)
#		layerset = project.getRootLayerSet()
#		for layer in layerset.getLayers():
#			tiles = layer.getDisplayables(Patch)
#			remove_tiles(tiles)
	filenames_keys=file_keys_big_list[num] #gets appropriate substack filepaths and images
	filenames_values=file_values_big_list[num]
	# print(filenames_keys, filenames_values)
#	if test:
	if inverted_image:
		#print(roi_list, crop_roi_list)
		output_inverted=make_dir(large_OV_interim, "inv_substack"+str(num)) #makes inverted substack folder			
		if num == 0:
			if folder_find(output_inverted,windows):
				inverted_subfolders=folder_find(output_inverted,windows)
			#checks only first folder, but assuming sufficient
				if filter(pattern_3.match, os.listdir(inverted_subfolders[0])): #checks whether project already exist
					gui = GUI.newNonBlockingDialog("Overwrite?")
					gui.addMessage(" Press ok to overwrite already inverted file in invert_interim_1"+project_name+"?\n Pressing cancel will exit the script.")#do i need to remove preexisting files
					gui.showDialog()
					if gui.wasOKed():
						pass
					#                    if windows:
					#                        os.remove(sub_dir+"\\"+temp_proj_name+"test.xml")
					#                    if not windows:
					#                        os.remove(sub_dir+"/"+temp_proj_name+"test.xml")
					elif not gui.wasOKed():
						sys.exit()
		filenames_keys, filenames_values = invert_image(filenames_keys, filenames_values, output_inverted, windows, pattern_3, 0) #inverts images
		print(num,"of ",len(OV_folder_list),"substacks processed")
#			if len(filenames_keys) != 1 and Crop: #crops images if more than one image tile per layer if crop is choosen
#				large_OV_interim_2= make_dir(grand_joint_folder, "crop_interim_2_"+project_name) #makes crop folder
#				output_scaled=make_dir(large_OV_interim_2, "crop_substack"+str(num)) #makes crop substack folder
#				# print(output_scaled, roi_list[num], crop_roi_list[num],assoc_roi_list[num])
#				filenames_keys, filenames_values = remove_area(filenames_keys, #crops overlap area
#																filenames_values, 
#																output_scaled, windows, 
#																temp_proj_name, pattern_3, roi_list[num], crop_roi_list[num], assoc_roi_list[num])
#
##		#crop image
#		elif not inverted_image and Crop: #crops overlap area without inverting
#			if len(filenames_keys) != 1:
#				large_OV_interim_2= make_dir(grand_joint_folder, "crop_interim_1_"+project_name)
#				output_scaled=make_dir(large_OV_interim_2, "crop_substack"+str(num))
#				filenames_keys, filenames_values = remove_area(filenames_keys, 
#																filenames_values, 
#																output_scaled, windows, 
#																temp_proj_name, pattern_3, roi_list[num], crop_roi_list[num], assoc_roi_list[num])
#
#				
	print("files potentially cropped and or inverted")
#	print(filenames_keys, filenames_values)
	file_keys_big_list[num]=filenames_keys #refreshes to correct filepaths and file names
	file_values_big_list[num]=filenames_values
    


#file_values_big_list = apply_transform(transform_dir_big, file_keys_big_list, file_values_big_list, Windows=False)
    


counter=0
counter_list=[counter]
temp_proj_name=project_name+"_"+str(0)
project = Project.getProject(project_list[0]) #selects appropriate project for image substack
sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(0)) #makes a directory for this project if not already done
try: #removes images present from the test trakem2 project
	remove_tiles(tiles_list[0])
except IndexError:
	# print(project)
	layerset = project.getRootLayerSet()
	for layer in layerset.getLayers():
	  	tiles = layer.getDisplayables(Patch)
		remove_tiles(tiles)
#why plus one
for num in range(0,len(OV_folder_list)): #this is where the actually alignment takes place
	print(num+1, len(OV_folder_list))
	temp_proj_name=project_name+"_"+str(num)
 	#print((project_list[num]))
 	#print(type(project_list[num]))
#	print(match[0])
#	project = Project.getProject(project_list[num]) #selects appropriate project for image substack
#	if Elastic:
	transform =  transform_list[num]
	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))  #makes a directory for this project if not already done
 	#print(project)
 	#print([filenames_keys[0]], filenames_values[0])										
	filenames_keys=file_keys_big_list[num]#gets correct filepaths and file names
	filenames_values=file_values_big_list[num]
#	filenames_keys=file_sort(filenames_keys,0,True) #reorders them from right most to left most image
#	print(filenames_keys)
#	print(filenames_values)
	print(transform)
	layerset=add_patch_v2(filenames_keys,filenames_values
	, project, counter, counter+len(filenames_values[0]),transform,scaling_number_list[num])
	counter+=len(filenames_values[0])
	counter_list.append(counter)
	print("prepared tile order for best overlay")
	project.saveAs(os.path.join(sub_dir, temp_proj_name+"layer_filled_to_"+str(counter)), False) #save project file before z alignment 	
	#layerset=add_patch_andTransform([filenames_keys[0]], [filenames_values[0]], project, 0, len(filenames_values[0]), transform_folder=transform) #makes layers and adds images to them
	#if len(filenames_keys) != 1: #don't need this if
#	if Elastic:
#		layerset=add_patch_andTransform(filenames_keys[0:], filenames_values[0:], project, 0, len(filenames_values[0]), transform_folder=transform)
#	if not Elastic:
#		print(filenames_keys[1:],filenames_values[1:], project, 0, 0)
#		layerset=add_patch([filenames_keys[0]], [filenames_values[0]], project, 0, len(filenames_values[0])) #makes layers and adds images to them
#		if len(filenames_keys) != 1: #don't need this if
#			layerset=add_patch(filenames_keys[1:], filenames_values[1:], project, 0, 0) #issue here where there is a project loaded with the same name
#	align_layers(model_index, octave_size, layerset, True) #could change number of threads
	layerset.setMinimumDimensions() 
 	
project.saveAs(os.path.join(sub_dir, temp_proj_name+"stiched"), False) #save project file before z alignment
#align_layers(model_index, octave_size, layerset, True) #could change number of threads
AlignLayersTask.alignLayersLinearlyJob(layerset,0,len(layerset.getLayers())-1,False,None,None) #z alignment

	#print(sub_dir, temp_proj_name+"aligned")
layerset.setMinimumDimensions()

 	# if proj_folds:
 	# 	project.saveAs(os.path.join(sub_dir, temp_proj_name+"aligned"), False) #save project file final time, after z alignment
 	# else:
 	# 	project.saveAs(os.path.join(sub_dir, temp_proj_name+"aligned"), False)
# 	#exports images
#	mini_dir= make_dir(output_dir,  "export_"+str(num)) #makes output subdirectory
# 	#export_image(layerset, mini_dir, canvas_roi=True)#, processed=False) #exports image
#	exportProject(project, mini_dir)
mini_dir= make_dir(output_dir,  "export_unprocessed_"+str(num))
exportProject(project, mini_dir,canvas_roi=True)#,blend=True)
mini_dir= make_dir(output_dir,  "export_processed_"+str(num))
exportProject(project, mini_dir,canvas_roi=True, processed=True) #,blend=True)
      
optionalClosingAndDeleting(project,output_dir,project_name)

print("Done!")
