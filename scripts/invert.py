
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
#@ int (label = "file_start", default=800, min=0 ) file_start
#@ boolean (label = "using a windows machine") windows


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
#added for script
inverted_image=True
#additional processing variables (gaussian blur, CLAHE )
sigmaPixels=0.7
blocksize = 300
histogram_bins = 256
maximum_slope = 1.5
#export image variables (MakeFlatImage)
export_type=0 #GRAY8
scale = 1.0
backgroundColor = Color(0,0,0,0)

#get string of folder paths
folder_path = folder.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()
#grand_joint_folder=mut_fold(folder_path,output_dir,windows) #make parent directory #TODO figure out why not just use output_dir??
grand_joint_folder=output_dir


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

if inverted_image: 
	large_OV_interim= make_dir(grand_joint_folder, "invert_interim_1"+project_name) #make inverted image directory


for num in range(0,len(OV_folder_list)): #find files and paths and test alignment for each substack
	filenames_keys=filenames_keys_big[num]
	filenames_values=filenames_values_big[num]
	print("folder and its content registered")
	if len(filenames_keys)==0:
		print("error-empty list of keys given")
		break
	print(filenames_keys, filenames_values)
	file_keys_big_list.append(filenames_keys)
	file_values_big_list.append(filenames_values)
print("hey")
print(file_keys_big_list)
print(file_values_big_list)

print(len(project_list)+1, "amount of started projects")
print(len(OV_folder_list)+1, "amount of processed substacks")

#Closes open windows to open cache memory
IJ.run("Close All")

#changed to len(projec_list) since OV_folder_list doesnt accounnt fro the empty substack
for num in range(0,len(OV_folder_list)): #this is for adjusting images to be cropped and, if necessary, inverted. 
	temp_proj_name=project_name+"_"+str(num)

	filenames_keys=file_keys_big_list[num] #gets appropriate substack filepaths and images
	filenames_values=file_values_big_list[num]
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
					elif not gui.wasOKed():
						sys.exit()
		print(len(filenames_values[0:][0]))
		print(len(filenames_values[0:][0][file_start:]))
		print((filenames_values[0:][0][file_start:]))
#		sys.exit()
		for n, fold in enumerate(filenames_keys[0:]):
			for m, filename in enumerate(filenames_values[0:][n][file_start:]):
		
#				if m >= file_start:
#					print(joint_folder)
					filepath = os.path.join(fold, filename)
					print(filepath)
					imp = IJ.openImage(filepath)
					IJ.run(imp, "Invert", "")
					print(imp)					
					sub_dir = make_dir(output_inverted, "_"+str(n),
									   imp, "/"+str(n)+"_"+str(m+file_start), windows, True)


		print(num,"of ",len(OV_folder_list),"substacks processed")

print("Done!")
