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
	1. multiple checks to ensure proper file and file structurer
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
	16. (new) always remove all projects open trakem2
	17. (new) if different image layout, seperate images into different substacks
	18. (new) assumes OV stack same throughout image stack
	19. no errors from elastic, but ensure if transforms applied to full stack
	20. problem with script whne only one image in substack
loosely based off of Albert Cardona 2011-06-05 script
"""

#@ File (label = "low resolution directory", style = "directory") folder
#@ File (label = "high resolution directory", style = "directory") folder_2
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ boolean (label = "Invert high resolution images") inverted_image
#@ int (label = "low resolution image rescale factor", default=4, min=0, max=10 ) size
#@ int (label = "octave_size", default=800, min=0, max=1500 ) octave_size
#@ String(choices={"translation", "rigid", "similarity", "affine"}, style="list") model_index
#@ boolean (label = "using a windows machine") windows
#@ boolean (label = "script previously run (alignment parameter saved in file)") rerun
#@ boolean (label = "Elastic Alignment") Elastic
#@ boolean (label = "Unorganized input") orgInput

# import modules
# ----------------------------------------------------------------------------------------
import os, re, sys

script_path = os.path.dirname(sys.argv[0])  #get filepath to functions.py
sys.path.append(script_path)
from functions import *
from java.awt import Rectangle


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
tiles_list=[]
filenames_keys_big =[]
filenames_values_big = []
file_keys_big_list=[]
file_values_big_list=[]
scaling_number_list=[]
proj_folds=[]
project=''
octave_increase=0
transform_list=[]
transform_xml_list=[]
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
folder_path_2 = folder_2.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()

#flush image cache every 60 seconds?
exe = Executors.newSingleThreadScheduledExecutor()
exe.scheduleAtFixedRate(releaseAll, 0, 60, TimeUnit.SECONDS)

#main
# --------------------------------------------------------------------------------------

if orgInput:
	list_files = get_stacks(folder_path, resolution = [10,10], match_pattern = 'PB', exceptions=['ISOLATED'])

	# Split list of TIF files into stacks of overlapping files
	OV_folder_list = split_stacks(list_files)
	filenames_keys_big, filenames_values_big, OV_folder_list=list_decoder(OV_folder_list)
	
else:
	OV_folder_list=folder_find(folder_path,windows)
	OV_folder_list=file_sort(OV_folder_list, -1) #sort
	HR_folder_list=folder_find(folder_path_2,windows)
	HR_folder_list=file_sort(HR_folder_list, -1) #sort

	for num in range(0,len(OV_folder_list)):
		sub_OV_folders=folder_find(OV_folder_list[num], windows) #find tile directories for each substack
		sub_OV_folders=file_sort(sub_OV_folders, -1) #sort
		all_folder_list=folder_find(HR_folder_list[num],  windows, sub_OV_folders)	
		filenames_keys, filenames_values=file_find(all_folder_list, pattern_1, pattern_3) #finds images for OV and high_res folders
		filenames_keys_big.append(filenames_keys)
		filenames_values_big.append(filenames_values)
		print("folder "+str(num)+" and its content registered")

proj_dir= make_dir(output_dir,  "trakem2_files_"+project_name) #make project directory
transform_dir_big = make_dir(output_dir,"transform_parameters_"+project_name) #make transform folder
if not rerun:
	test_proj_dir= make_dir(proj_dir,  "test_trakem2")  #make substack specific project folder
	test_dir= make_dir(output_dir,  "test_0_"+project_name) #make test directory
	test_dir_2= make_dir(output_dir,  "test_0_"+project_name+"_2") #make test directory 2


if inverted_image: 
	large_HR_interim= make_dir(output_dir, "high_res_interim_"+project_name) #make inverted image directory
	
if len(OV_folder_list) != len(HR_folder_list):
	sys.exit("need same folder number for low and high res" ) #find files and paths and test alignment for each substack

for num in range(0,len(OV_folder_list)):#find duplicates
	print("checking correct number of files for folder "+str(num))
	filenames_keys=filenames_keys_big[num]
	filenames_values=filenames_values_big[num]
	dup_find(filenames_keys,filenames_values)

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
		if not rerun:
			#Creates a TrakEM2 project
			sub_dir= make_dir(test_proj_dir,  "substack_trakem2_"+str(num))  #make substack specific project folder
			file_list= os.listdir(sub_dir) # get list of all files including potential previous project files in substack
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
			#resize and invert high res files
			temp_filenames_keys,temp_filenames_values = prep_test_align(filenames_keys[1:], 
															 filenames_values[1:], 
															 test_dir, windows, 
															 temp_proj_name,inverted_image,size,empty=True)                                                      
			temp_filenames_keys = [filenames_keys[0]]+temp_filenames_keys
			temp_filenames_values =	[filenames_values[0]]+temp_filenames_values	
			#this is for rescaling to facilitate operations,redundantly saves file twice
			temp_filenames_keys,temp_filenames_values, scaling_number = prep_test_align_viggo(temp_filenames_keys, 
														temp_filenames_values, 
														test_dir_2, windows, 
														temp_proj_name, invert_image=False, size=True)	
			#creates layerset and adds images																								
			layerset=add_patch(temp_filenames_keys,temp_filenames_values, project, 0, 1) 

			if Elastic: #aligns images elastically
				roi, tiles, transform_XML =align_layers_elastic(param,model_index,layerset,False,octave_size) 
			if not Elastic: #aligns images non-elastically
				roi, tiles, transforms, transform_XML =align_layers(model_index, octave_size, layerset,None,True) 
			
			layerset.setMinimumDimensions() #readjust canvas 
			project.saveAs(os.path.join(proj_dir, temp_proj_name+"test"), False) #save trakem2 project

			gui = GUI.newNonBlockingDialog("Aligned?")
			gui.addMessage("Inspect alignment results. Are tiles aligned properly?\n If not pressing cancel will increase octave size\n (Maximum Image Size parameter) by 200 px. ")
			gui.showDialog()
			if gui.wasOKed():
				filenames_values, filenames_keys, roi, tiles, transforms, transform_XML =adopt_man_move(layerset,temp_filenames_keys,temp_filenames_values,filenames_keys,filenames_values,True)
				project.remove(True)  
				transform_dir=make_dir(transform_dir_big,"substack_"+str(num))#makes directory for transformation information
				transform_xml_list.append(transform_XML)
				transform_list.append(transform_dir)
				scaling_number_list.append(scaling_number)#make file with scaling factor info
				tiles_list.append(tiles)
				roi_list.append(adjust_roi(roi,scaling_number))
				break
			if not gui.wasOKed():
				octave_increase+=1
				project.remove(True) # in place to try and reduce cache memory
		if rerun:
		   break
	file_keys_big_list.append(filenames_keys)
	file_values_big_list.append(filenames_values)
	IJ.run("Close All")
print("initial alignment test done")
print(len(OV_folder_list)+1, "amount of processed substacks")

if not rerun:	
	tot_roi = roi_list[0]  # roi of all the roi from each substack
	for big_tile in roi_list[1:]:
		tot_roi.add(big_tile)
	for num in range(0,len(OV_folder_list)): #save all transformation information to perform on other images
		save_xml_files(transform_xml_list[num], transform_list[num],size,scaling_number_list[num],tot_roi)
	save_roi(roi, transform_list[0]) #saves tot_roi to first transformation folder

if rerun:
	#if not running test opens up previous test project file
	transform_folds=folder_find(transform_dir_big,windows) #looks for previous test transform file, add function functionality to send gui if you want to make a new folder
	transform_folds=file_sort(transform_folds, -1) 
	for n, transformed in enumerate(transform_folds):#find out why only one scaling_file comes
		transform_list.append(transformed)
		if n == 0 :
			roi_file=filter(re.compile("1_roi.xml").match, os.listdir(transformed))#only one roi, as it is total roi
			path=os.path.join(transformed,roi_file[0])
			with open(path, 'r+') as f:
				for line in f :
					file_roi=line
			tot_roi=Rectangle()
			roi_values=re.findall("(\d+)", file_roi)
			tot_roi.x=int(roi_values[0])#with roi object fill in right values
			tot_roi.y=int(roi_values[1])
			tot_roi.width=int(roi_values[2])
			tot_roi.height=int(roi_values[3])


#Closes open windows to open cache memory
IJ.run("Close All")

 #this is for adjusting images to be cropped and, if necessary, inverted.
for num in range(0,len(OV_folder_list)): #check if inverted files exist already 
	filenames_keys=file_keys_big_list[num] #gets appropriate substack filepaths and images
	filenames_values=file_values_big_list[num]
	if inverted_image: #check if inverted files exist already 
		output_inverted=delete_interim(large_HR_interim,project_name,pattern_3,"high_res_interim",windows,num)

	if size != 1:  #check if cropped files exist already 
		large_OV_interim= make_dir(output_dir, "low_res_interim_"+project_name)
		output_scaled=delete_interim(large_OV_interim,project_name,pattern_3,"low_res_interim",windows,num)

	if inverted_image: #invert images
		filenames_keys, filenames_values = invert_image(filenames_keys, filenames_values, output_inverted, windows, pattern_3)

	if size != 1: 	#resize image
		filenames_keys, filenames_values = resize_image(filenames_keys, 
															filenames_values, 
															output_scaled, windows, 
															temp_proj_name, pattern_3, size, tot_roi)
															
																
	print(num,"of ",len(OV_folder_list),"substacks processed")
	file_keys_big_list[num]=filenames_keys #refreshes to correct filepaths and file names
	file_values_big_list[num]=filenames_values

counter=0 #counter in place as all substacks added into same project, counter determines where last substack ended off
counter_list=[counter]
main_proj_dir= make_dir(proj_dir,  "main_trakem2")  #make substack specific project folder
project = Project.newFSProject("blank", None, main_proj_dir) #Creates a TrakEM2 project
for num in range(0,len(OV_folder_list)): #this is where the actually alignment takes place
	transform =  transform_list[num]
	filenames_keys=file_keys_big_list[num]#gets correct filepaths and file names
	filenames_values=file_values_big_list[num]
	layerset=add_patch_v2(filenames_keys,filenames_values, project, counter, counter+len(filenames_values[0]),transform) 
	counter+=len(filenames_values[0])
	counter_list.append(counter)
	print("prepared tile order for best overlay")
	layerset.setMinimumDimensions() #readjust canvas 
	project.saveAs(os.path.join(main_proj_dir, project_name+"_layer_filled_to_"+str(counter)), False) #save project file before re alignment 	
#projects only saved in first trackem2 folder
project.saveAs(os.path.join(main_proj_dir, project_name+"_aligned"), False) #save project file before re alignment 	
layerset.setMinimumDimensions() #readjust canvas 
align_layers(model_index, 600, layerset, None,False) #following allows for little corrections in alignment
project.saveAs(os.path.join(main_proj_dir, project_name+"_re_aligned"), False) #save project file after readjusting alignment	            
#remove OV from layers
remove_OV(layerset,0)
layerset.setMinimumDimensions() #readjust canvas to only high res tiles
project.saveAs(os.path.join(main_proj_dir, project_name+"_only_high_res"), False) #save project file with only high res	

#exports images
#mini_dir= make_dir(output_dir,  "export_unprocessed_"+str(num)) #uncomment if you want unprocessed images as well
#exportProject(project, mini_dir,canvas_roi=True)#,blend=True)  #uncomment if you want unprocessed images as well
mini_dir= make_dir(output_dir,  "export_processed_"+str(num))
exportProject(project, mini_dir,canvas_roi=True, processed=True)#,blend=True)

optionalClosingAndDeleting(project,output_dir,project_name) #asks user if they want to close  trackem2 project and delete intermediate files.

print("Done!")

