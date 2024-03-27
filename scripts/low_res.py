
"""
Title: low_res.py

Date:  March 2nd, 2023

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
#@ int (label = "octave_size", default=800, min=0, max=1500 ) octave_size
#@ String(choices={"translation", "rigid", "similarity", "affine"}, style="list") model_index
#@ boolean (label = "using a windows machine") windows
#@ boolean (label = "script previously run (alignment parameter saved in file)") rerun
#@ boolean (label = "Elastic Alignment") Elastic
#@ boolean (label = "Unorganized input") orgInput

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
#vision group SBEM pattern
#pattern_1 = re.compile("([\d]+).*\.tif")
#pattern_2 = re.compile(".*-([\d]{3})-([\d]+)_.*\.tif")
#alternate patterns
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
filenames_keys_big =[]
filenames_values_big = []
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

# Create an instance of GenericDialog
if Elastic:
	param=GUIElasticParameters()

#get string of folder paths
folder_path = folder.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()
grand_joint_folder=output_dir

#flush image cache every 60 seconds?
exe = Executors.newSingleThreadScheduledExecutor()
exe.scheduleAtFixedRate(releaseAll, 0, 60, TimeUnit.SECONDS)

#main
# --------------------------------------------------------------------------------------
if orgInput:
	list_files = get_stacks(folder_path, resolution = [40,40], match_pattern = 'OV', exceptions=['ISOLATED'])
	print([l[0] for l in list_files])
	# Split list of TIF files into stacks of overlapping files
	OV_folder_list = split_stacks(list_files)
	filenames_keys_big, filenames_values_big, OV_folder_list = list_decoder(OV_folder_list)

else:
	stacks = get_file_paths_folders(folder_path)
	OV_folder_list=folder_find(folder_path,windows) # get OV subdirectories
	OV_folder_list=file_sort(OV_folder_list, -1) #sort
	for num, fold in enumerate(OV_folder_list): #find files and paths and test alignment for each substack
		sub_OV_folders=folder_find(fold, windows) #find tile directories for each substack
		sub_OV_folders=file_sort(sub_OV_folders, -1) #sort
		filenames_keys, filenames_values=file_find(sub_OV_folders, pattern_1, pattern_3)
		filenames_keys_big.append(filenames_keys)
		filenames_values_big.append(filenames_values)

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
			#Creates a TrakEM2 project
			sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num)) #make substack specific project folder
			file_list= os.listdir(sub_dir) # get list of all images in substack
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
			layerset = project.getRootLayerSet() #creates initial collection of layers variable
			temp_filenames_keys,temp_filenames_values,scaling_number = prep_test_align_viggo(filenames_keys, #inverts images for test alignment
														filenames_values, 
														test_dir, windows, 
														temp_proj_name, inverted_image, size=True)	
			layerset=add_patch(temp_filenames_keys,temp_filenames_values, project, 0, 1)#creates layerset and adds images
			if Elastic:
				roi, tiles, transform_XML =align_layers_elastic(param, layerset,True,octave_size)

			if not Elastic:
				roi, tiles, transforms, transform_XML =align_layers(model_index, octave_size, layerset,True,True) #aligns images
			
			layerset.setMinimumDimensions() #readjust canvas to minimum dimensions
			project.saveAs(os.path.join(sub_dir, temp_proj_name+"test"), False)	#save test run						
			gui = GUI.newNonBlockingDialog("Aligned?")
			gui.addMessage("Inspect alignment results. Are tiles aligned properly?\n If not, pressing cancel will increase octave size\n (Maximum Image Size parameter) by 200 px. ")
			gui.showDialog()
			if gui.wasOKed():
				filenames_values, filenames_keys, roi, tiles, transforms, transform_XML =adopt_man_move(layerset,temp_filenames_keys,temp_filenames_values,filenames_keys,filenames_values,True)
				if num > 0:
					project.remove(True) 
				transform_dir=make_dir(transform_dir_big,"substack_"+str(num)) #makes directory for transformation information
				save_xml_files(transform_XML, transform_dir, 1,scaling_number,roi)
				transform_list.append(transform_dir)
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

print("initiall alignment test done")
print(len(OV_folder_list)+1, "amount of processed substacks")

try: #if not running test opens up previous test project file, clunky way deciding between test mode or not
	project_list[0]
except IndexError:
	proj_folds=folder_find(proj_dir,windows) #looks for previous test project file, add function functionality to send gui if you want to make a new folder
	proj_folds=file_sort(proj_folds, -1) 
	projects=Project.getProjects()	
	transform_folds=folder_find(transform_dir_big,windows) #looks for previous test project file, add function functionality to send gui if you want to make a new folder
	transform_folds=file_sort(transform_folds, -1) 
	for proj in proj_folds:
		xml_file=filter(pattern_xml.match, os.listdir(proj))
		xml_filepath = os.path.join(proj,xml_file[0])
		for projected in projects: # finds test project file if open in trakem2
			if (xml_file[0].split("."))[0] in str(projected):
				project = Project.getProject(projected)
				break
		if not project: #finds test project file in directory and opens it
			project=Project.openFSProject(xml_filepath, True)
		project_list.append(project)
		project=''
	#load in scaling factor and roi file	#no longer needed?
	for transformed in transform_folds:#find out why only one scaling_file comes
		scaling_file=filter(re.compile("\d+_scaling.txt").match, os.listdir(transformed))
		transform_list.append(transformed)

#Closes open windows to open cache memory
IJ.run("Close All")

#changed to len(projec_list) since OV_folder_list doesnt accounnt fro the empty substack
for num in range(0,len(project_list)): #this is for adjusting images to be cropped and, if necessary, inverted. 
	temp_proj_name=project_name+"_"+str(num)
	filenames_keys=file_keys_big_list[num] #gets appropriate substack filepaths and images
	filenames_values=file_values_big_list[num]
	if inverted_image:
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
					elif not gui.wasOKed():
						sys.exit()
		filenames_keys, filenames_values = invert_image(filenames_keys, filenames_values, output_inverted, windows, pattern_3, 0) #inverts images
		print(num,"of ",len(OV_folder_list),"substacks processed")
	
	print("files potentially cropped and or inverted")
	file_keys_big_list[num]=filenames_keys #refreshes to correct filepaths and file names
	file_values_big_list[num]=filenames_values
	
counter=0  #counter in place as all substacks added into same project, counter determines where last substack ended off
counter_list=[counter]
temp_proj_name=project_name+"_"+str(0)
project = Project.getProject(project_list[0]) #selects appropriate project for image substack
sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(0)) #makes a directory for this project if not already done
try: #removes images present from the test trakem2 project
	remove_tiles(tiles_list[0])
except IndexError:
	layerset = project.getRootLayerSet()
	for layer in layerset.getLayers():
	  	tiles = layer.getDisplayables(Patch)
		remove_tiles(tiles)
for num in range(0,len(OV_folder_list)): #this is where the actually alignment takes place
	print(num+1, len(OV_folder_list))
	temp_proj_name=project_name+"_"+str(num)
	transform =  transform_list[num]
	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))  #makes a directory for this project if not already done								
	filenames_keys=file_keys_big_list[num]#gets correct filepaths and file names
	filenames_values=file_values_big_list[num]
	layerset=add_patch_v2(filenames_keys,filenames_values
	, project, counter, counter+len(filenames_values[0]),transform)
	counter+=len(filenames_values[0])
	counter_list.append(counter)
	print("prepared tile order for best overlay")
	project.saveAs(os.path.join(sub_dir, temp_proj_name+"layer_filled_to_"+str(counter)), False) #save project file before z alignment 	
	layerset.setMinimumDimensions()  #readjust canvas 

AlignLayersTask.alignLayersLinearlyJob(layerset,0,len(layerset.getLayers())-1,False,None,None) #z alignment
project.saveAs(os.path.join(sub_dir, temp_proj_name+"aligned"), False) #save project file after z alignment

layerset.setMinimumDimensions()

# 	#exports images
mini_dir= make_dir(output_dir,  "export_unprocessed_"+str(num))
exportProject(project, mini_dir,canvas_roi=True)#,blend=True)
mini_dir= make_dir(output_dir,  "export_processed_"+str(num))
exportProject(project, mini_dir,canvas_roi=True, processed=True) #,blend=True)
	  
optionalClosingAndDeleting(project,output_dir,project_name) #asks user if they want to close  trackem2 project and delete intermediate files.

print("Done!")

'''
known error(new):
	1. line 129 grand_joint_folder change to output
	2. line 220 project_list.append(temp_proj_name+"test.xml") #fix for windows 
	3.line 215 #adjust roi to the appropriate scaling number, this can be put under functions
	4. line 254-267 #load in scaling factor 	#no longer needed? check 380, file should be present with previous  rescaling factor and roi and check with user (if roi is different) to make sure can move forward.shouldn\t need scaling facotr size if transform has all info    
	5. line 265 #changed to len(projec_list) since OV_folder_list doesnt accounnt fro the empty substack #not sure about this

'''