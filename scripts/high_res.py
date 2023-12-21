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
#@ boolean (label = "Invert high resolution images") inverted_image
#@ int (label = "low resolution image rescale factor", default=4, min=0, max=10 ) size
#@ int (label = "octave_size", default=800, min=0, max=1500 ) octave_size
#@ String(choices={"translation", "rigid", "similarity", "affine"}, style="list") model_index
#@ boolean (label = "using a windows machine") windows
#@ boolean (label = "script previously run (alignment parameter saved in file)") rerun
##@ boolean (label = "run test(if your low resolution has not been rescaled)") test
#@ boolean (label = "Elastic Alignment") Elastic
#@ boolean (label = "Unorganized input") orgInput

# import modules
# ----------------------------------------------------------------------------------------
#might not need all these modules
import os, re, sys

#script_path=os.path.abspath(__file__)
script_path = os.path.dirname(sys.argv[0]) 
sys.path.append(script_path)
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
tiles_list=[]
project_list=[]
filenames_keys_big =[]
filenames_values_big = []
file_keys_big_list=[]
file_values_big_list=[]
scaling_number_list=[]
proj_folds=[]
project=''
octave_increase=0
transform_list=[]
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

#func: get string of folder paths
folder_path = folder.getAbsolutePath()
folder_path_2 = folder_2.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()

#flush image cache every 60 seconds?
exe = Executors.newSingleThreadScheduledExecutor()
exe.scheduleAtFixedRate(releaseAll, 0, 60, TimeUnit.SECONDS)

#main
# --------------------------------------------------------------------------------------
# grand_joint_folder=mut_fold(folder,folder_2,windows)
grand_joint_folder=output_dir

if orgInput:
    list_files = get_stacks(folder_path, resolution = [10,10], match_pattern = 'PB',get_info=False)
#    list_files = get_stacks(folder_path, resolution = [40,40], match_pattern = 'OV')

    
    # Split list of TIF files into stacks of overlapping files
    OV_folder_list = split_stacks(list_files)
#    print(OV_folder_list)
    #filenames_keys_big, filenames_values_big, OV_folder_list= list_sampleMaker(OV_folder_list)
    filenames_keys_big, filenames_values_big, OV_folder_list=list_decoder(OV_folder_list)
    
else:
    OV_folder_list=folder_find(folder_path,windows)
    OV_folder_list=file_sort(OV_folder_list, -1) #sort
    NO_folder_list=folder_find(folder_path_2,windows)
    NO_folder_list=file_sort(NO_folder_list, -1) #sort
#    print(OV_folder_list,NO_folder_list)
    for num in range(0,len(OV_folder_list)):
        # temp_proj_name=project_name+"_"+str(num)
        # joint_folder=mut_fold(OV_folder_list[num],NO_folder_list[num],windows)  #find tile directories for each substack
        sub_OV_folders=folder_find(OV_folder_list[num], windows) #find tile directories for each substack
        sub_OV_folders=file_sort(sub_OV_folders, -1) #sort
        all_folder_list=folder_find(NO_folder_list[num],  windows, sub_OV_folders)
        # all_folder_list=folder_find(NO_folder_list[num],  windows, OV_folder_list[num])
#        print(all_folder_list)
        filenames_keys, filenames_values=file_find(all_folder_list, pattern_1, pattern_3)
        filenames_keys_big.append(filenames_keys)
        filenames_values_big.append(filenames_values)
        print("folder "+str(num)+" and its content registered")
        # print(filenames_keys, filenames_values)
#    print(filenames_keys_big, filenames_values_big)

if not rerun:
	test_dir= make_dir(grand_joint_folder,  "test_0_"+project_name) #make test directory
	test_dir_2= make_dir(grand_joint_folder,  "test_0_"+project_name+"_2") #make test directory
proj_dir= make_dir(grand_joint_folder,  "trakem2_files_"+project_name) #make project directory
transform_dir_big = make_dir(grand_joint_folder,"transform_parameters_"+project_name) #make transform folder
#large_OV_interim= make_dir(grand_joint_folder, "OV_interim")
if inverted_image: 
	large_NO_interim= make_dir(grand_joint_folder, "high_res_interim") #make inverted image directory
	
if len(OV_folder_list) != len(NO_folder_list):
	sys.exit("need same folder number for low and high res" ) #find files and paths and test alignment for each substack
	
for num in range(0,len(OV_folder_list)):
	# temp_proj_name=project_name+"_"+str(num)
	# joint_folder=mut_fold(OV_folder_list[num],NO_folder_list[num],windows)  #find tile directories for each substack
	# sub_OV_folders=folder_find(OV_folder_list[num], windows) #find tile directories for each substack
	# sub_OV_folders=file_sort(sub_OV_folders, -1) #sort
	# all_folder_list=folder_find(NO_folder_list[num],  windows, sub_OV_folders)
	# all_folder_list=folder_find(NO_folder_list[num],  windows, OV_folder_list[num])
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
#        print(filenames_keys, filenames_values)
	# filenames_keys, filenames_values=file_find(all_folder_list, pattern_1, pattern_3)
	# print(filenames_keys, filenames_values)
        if not rerun:
            dup_find(filenames_keys,filenames_values)
            #Creates a TrakEM2 project
            sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))  #make substack specific project folder
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
            #creates initial collection of layers variable
            layerset = project.getRootLayerSet() #creates initial collection of layers variable
            #create cropped area and invert high res files
            temp_filenames_keys,temp_filenames_values = prep_test_align(filenames_keys[1:], 
                                                             filenames_values[1:], 
                                                             test_dir, windows, 
                                                             temp_proj_name,inverted_image,size,empty=True)                                                      
#                                                             temp_proj_name,inverted_image,size,empty=True)
            temp_filenames_keys = [filenames_keys[0]]+temp_filenames_keys
            temp_filenames_values =	[filenames_values[0]]+temp_filenames_values	
            #this is for resizing to facilitate operations,redundatly saves file twice
#            print(temp_filenames_keys)
            temp_filenames_keys,temp_filenames_values, scaling_number = prep_test_align_viggo(temp_filenames_keys, #inverts images for test alignment
														temp_filenames_values, 
														test_dir_2, windows, #output_dir --> test_dir this is just a test
														temp_proj_name, invert_image=False, size=True)	
#            temp_filenames_keys_2,temp_filenames_values_2 = prep_test_align_viggo(temp_filenames_keys[1:], 
#                                                        temp_filenames_values[1:], 
#														test_dir_2, windows, #output_dir --> test_dir this is just a test
#														temp_proj_name, invert_image=True, size=True)	
#            temp_filenames_keys_2 = [temp_filenames_keys[0]]+temp_filenames_keys_2
#            temp_filenames_values_2 =	[temp_filenames_values[0]]+temp_filenames_values_2																													
#            print(temp_filenames_keys_2, temp_filenames_values_2)
#            print(temp_filenames_keys, temp_filenames_values)
            layerset=add_patch(temp_filenames_keys,temp_filenames_values, project, 0, 1) #creates layerset and adds images
#            scaling_number_list.append(scaling_number)
            if Elastic:
				#layerset_lowRes, scaling_factors=scale_image(layerset) #lowering the resolution for elastic alignment #TODO add scaling factor that increases i not alligned properly
				#print(type(layerset),type(layerset_lowRes))
#                roi, tiles, transforms, transform_XML =align_layers_elastic(param,model_index,layerset,True,octave_size)
#                roi, tiles, transform_XML, transform_XML2 =align_layers_elastic(param,model_index,layerset,False,octave_size)
                roi, tiles, transform_XML =align_layers_elastic(param,model_index,layerset,False,octave_size)
				#Save XML files
#                transform_dir=make_dir(transform_dir_big,"substack_"+str(num))
#                save_xml_files(transform_XML, transform_dir)
#                transform_list.append(transform_dir)
            if not Elastic:
				#Do i need true in align_layers
#                roi, tiles =align_layers(model_index, octave_size, layerset,True) #aligns images
                roi, tiles, transforms, transform_XML =align_layers(model_index, octave_size, layerset,None,True) #aligns images
                #transforms not needed
#                transform_dir=make_dir(transform_dir_big,"substack_"+str(num))
#                save_xml_files(transform_XML, transform_dir)
#                transform_list.append(transform_dir)
            # roi, tiles =align_layers(model_index, octave_size, layerset)  #aligns images
            project.saveAs(os.path.join(proj_dir, temp_proj_name+"test"), False)
#            scaling_number_file=open(os.path.join(transform_dir, str(num+1)+"_scaling.txt"),"w")
#            scaling_number_file.write(str(scaling_number))
#            scaling_number_file.close()
            layerset.setMinimumDimensions() #readjust canvas to only NO tiles
#            tiles_list.append(tiles)
#            roi_list.append(roi)
            #fix for windows
#            project_list.append(temp_proj_name+"test.xml")
            gui = GUI.newNonBlockingDialog("Aligned?")
            gui.addMessage("Inspect alignment results. Are tiles aligned properly?\n If not pressing cancel will increase octave size\n (Maximum Image Size parameter) by 200 px. ")
    #		gui.addMessage("Inspect alignment results. If there is any jitter (that isn't already present\n in the OV itself), manually fix this by re-running the alignment with updated\n parameters (i.e., try increasing Maximum Image Size parameter by\n 200 px.)\n\n Check image tile overlap and blend if desired.\n (Note: There is no 'Undo' for blending).\n\n If you would like to revert to previous state, use project 'montage_checkpoint.xml'.\n\n When image alignment is satisfactory, select 'Export'. A project .xml file\n will be saved in <dir> with user changes. Images will be exported as .tif to <dir>.")
            gui.showDialog()
            if gui.wasOKed():
                if num > 0:
                   project.remove(True)  
#                project.saveAs(os.path.join(proj_dir, temp_proj_name+"test"), False)
                transform_dir=make_dir(transform_dir_big,"substack_"+str(num))
                save_xml_files(transform_XML, transform_dir)
                transform_list.append(transform_dir)
                scaling_number_list.append(scaling_number)
                scaling_number_file=open(os.path.join(transform_dir, str(num+1)+"_scaling.txt"),"w")
                scaling_number_file.write(str(scaling_number))
                scaling_number_file.close()
                tiles_list.append(tiles)
                roi.x=int(roi.x*(1/scaling_number))
                roi.y=int(roi.y*(1/scaling_number))
                roi.width=int(roi.width*(1/scaling_number))
                roi.height=int(roi.height*(1/scaling_number))
                roi_list.append(roi)
                project_list.append(temp_proj_name+"test.xml")
                break
            if not gui.wasOKed():
                octave_increase+=1
                project.remove(True) 
        if rerun:
           break
    file_keys_big_list.append(filenames_keys)
    file_values_big_list.append(filenames_values)
    IJ.run("Close All")
#print(file_keys_big_list)	
#print(filenames_keys)
print("initiall alignment test done")
print(len(project_list)+1, "amount of started projects")
print(len(OV_folder_list)+1, "amount of processed substacks")


if not rerun:	
 	#find max ROI
	print(roi_list)
#	max_roi=max(roi_list)
#	print(max_roi)
	tot_roi = roi_list[0]  # needed in OV alignment
	for big_tile in roi_list[1:]:
		tot_roi.add(big_tile)
 	print(tot_roi)
# 	#potential gui
# 	while 1: #increases maximum image size parameters by 200 if the images did not align
# 		gui = GUI.newNonBlockingDialog("Aligned?")
# 		gui.addMessage("Inspect alignment results. Are tiles aligned properly?\n If not pressing cancel will increase octave size\n (Maximum Image Size parameter) by 200 px. ")
# 		gui.showDialog()
# 		if gui.wasOKed():
# #			for num in range(0,len(OV_folder_list)):
# #				project = Project.getProject(project_list[num])
# #				project.remove(False)
# #				project.removeProjectThing(layerset,False, True,1)
# 			break
# 		else:
# 			roi_list=[]
# 			octave_size=octave_size+200
# 			for num in range(0,len(OV_folder_list)):
# 				project = Project.getProject(project_list[num]) #assumes that there are no other projects open
# 				roi, tiles =align_layers(model_index, octave_size, layerset)
# 				roi_list.append(roi)
# 				tiles_list.append(tiles)
# 	print(roi_list)
# 	#max_roi=max(roi_list)
# 	#print(max_roi)

try: #if not running test opens up previous test project file, clunky way deciding between test mode or not
	project_list[0]
except IndexError:
	proj_folds=folder_find(proj_dir,windows) #looks for previous test project file, add function functionality to send gui if you want to make a new folder
	proj_folds=file_sort(proj_folds, -1) 
#	print(proj_folds[0])
	projects=Project.getProjects()
	transform_folds=folder_find(transform_dir_big,windows) #looks for previous test project file, add function functionality to send gui if you want to make a new folder
	transform_folds=file_sort(transform_folds, -1) 
#	for proj in proj_folds:
	for proj in [proj_folds[0]]:
		xml_file=filter(pattern_xml.match, os.listdir(proj))
		xml_filepath = os.path.join(proj,xml_file[0])
		for projected in projects: # finds test project file if open in trakem2 
			if (xml_file[0].split("."))[0] in str(projected):
				project = Project.getProject(projected)
	        # if (xml_file[0].split("."))[0] in str(proj):
			# 	project = Project.getProject(proj)
				break
		if not project:
			project=Project.openFSProject(xml_filepath, True)
		project_list.append(project)
		project=''
	# project_list=file_sort(project_list)
	# print(project_list)
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
#        print(scaling_number_list)


	

#Closes open windows to open cache memory
IJ.run("Close All")

#changed to len(projec_list) since OV_folder_list doesnt accounnt fro the empty substack
for num in range(0,len(OV_folder_list)): #this is for adjusting images to be cropped and, if necessary, inverted. 
# for num in range(0,len(OV_folder_list)):
#	temp_proj_name=project_name+"_"+str(num)
#	print(file_keys_big_list)
	# print(type(project_list[num]))
#	project = Project.getProject(project_list[num]) #selects appropriate project for image substack
#	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num)) #makes a directory for this project if not already done
#	# print(project)
#	try: #removes images present from the test trakem2 project
#		remove_tiles(tiles_list[num])
#	except IndexError:
#		# print(project)
#		layerset = project.getRootLayerSet()
#		for layer in layerset.getLayers():
#		  	tiles = layer.getDisplayables(Patch)
#			remove_tiles(tiles)
	filenames_keys=file_keys_big_list[num] #gets appropriate substack filepaths and images
	filenames_values=file_values_big_list[num]
	# print("this is before cropped")
#	if test:
	if inverted_image:
#		#make list of filenammes keys and values for each project
		output_inverted=make_dir(large_NO_interim, "high_res_interim"+str(num))
		if num == 0:
			if folder_find(output_inverted,windows):
				inverted_subfolders=folder_find(output_inverted,windows)
			#checks only first folder, but assuming sufficient
				if filter(pattern_3.match, os.listdir(inverted_subfolders[0])): #checks whether project already exist
					gui = GUI.newNonBlockingDialog("Overwrite?")
					gui.addMessage(" Press ok to overwrite already inverted files in high_res_interim?\n Pressing cancel will exit the script.")#do i need to remove preexisting files
					gui.showDialog()
					if gui.wasOKed():
						pass
					#                    if windows:
					#                        os.remove(sub_dir+"\\"+temp_proj_name+"test.xml")
					#                    if not windows:
					#                        os.remove(sub_dir+"/"+temp_proj_name+"test.xml")
					elif not gui.wasOKed():
						sys.exit()

	if size != 1:
		if not rerun:
			large_OV_interim= make_dir(grand_joint_folder, "low_res_interim")
			output_scaled=make_dir(large_OV_interim, "low_res_interim"+str(num))
			if num == 0:
				if folder_find(output_scaled,windows):
					output_subfolders=folder_find(output_scaled,windows)
				#checks only first folder, but assuming sufficient
					if filter(pattern_3.match, os.listdir(output_subfolders[0])): #checks whether project already exist
						gui = GUI.newNonBlockingDialog("Overwrite?")
						gui.addMessage(" Press ok to overwrite already cropped files in low_res_interim?\n Pressing cancel will exit the script.")#do i need to remove preexisting files
						gui.showDialog()
						if gui.wasOKed():
							pass
						#                    if windows:
						#                        os.remove(sub_dir+"\\"+temp_proj_name+"test.xml")
						#                    if not windows:
						#                        os.remove(sub_dir+"/"+temp_proj_name+"test.xml")
						elif not gui.wasOKed():
							sys.exit()
		if rerun:
			print("sys.exit() currently does not resize if not during test as needs roi of images from test")
			sys.exit()
	if inverted_image:
		filenames_keys, filenames_values = invert_image(filenames_keys, filenames_values, output_inverted, windows, pattern_3)

    #resize image
	if size != 1:
		if not rerun:
#			large_OV_interim= make_dir(grand_joint_folder, "low_res_interim")
#			output_scaled=make_dir(large_OV_interim, "low_res_interim"+str(num))
			filenames_keys, filenames_values = resize_image(filenames_keys, 
															filenames_values, 
															output_scaled, windows, 
#															temp_proj_name, pattern_3, size, roi_list[num])
#															temp_proj_name, pattern_3, size, max_roi)
															temp_proj_name, pattern_3, size, tot_roi)
															
																
	print(num,"of ",len(OV_folder_list),"substacks processed")
	# print(filenames_keys, filenames_values)
	file_keys_big_list[num]=filenames_keys #refreshes to correct filepaths and file names
	file_values_big_list[num]=filenames_values

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
for num in range(0,len(OV_folder_list)): #this is where the actually alignment takes place
#	temp_proj_name=project_name+"_"+str(num)
#	project = Project.getProject(project_list[0]) #selects appropriate project for image substack
#	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(0)) #makes a directory for this project if not already done
#	try: #removes images present from the test trakem2 project
#		remove_tiles(tiles_list[0])
#	except IndexError:
#		# print(project)
#		layerset = project.getRootLayerSet()
#		for layer in layerset.getLayers():
#		  	tiles = layer.getDisplayables(Patch)
#			remove_tiles(tiles)
#	project = Project.getProject(project_list[num]) #selects appropriate project for image substack
#	if Elastic:
#	   transform =  transform_list[num]
	transform =  transform_list[num]
	sub_dir= make_dir(proj_dir,  "substack_trakem2_"+str(num))  #makes a directory for this project if not already done
	filenames_keys=file_keys_big_list[num]#gets correct filepaths and file names
	filenames_values=file_values_big_list[num]
#	print(filenames_keys)
#	print("here")
#	print(filenames_values)
#	print(transform, scaling_number_list[num])
#for i in range(0,len(big_names_keys)): #set up counter to determine how many files per substack and populates trakem2 layers
	#print(counter)
	layerset=add_patch_v2(filenames_keys,filenames_values
	, project, counter, counter+len(filenames_values[0]),transform,scaling_number_list[num],size,tot_roi)
	
	counter+=len(filenames_values[0])
	counter_list.append(counter)
#	if num == 1:
#		sys.exit()
    #add stack to trakem2	
	#fix add_patch	
	print("prepared tile order for best overlay")
	project.saveAs(os.path.join(sub_dir, temp_proj_name+"layer_filled_to_"+str(counter)), False) #save project file before z alignment 	
#	layerset=add_patch(filenames_keys, filenames_values, project, 1, len(filenames_values[0]))												
#	if Elastic:
#		layerset=add_patch_andTransform(filenames_keys[0:], filenames_values[0:], project, 0, len(filenames_values[0]), transform_folder=transform)
#	if not Elastic:
#		layerset=add_patch(filenames_keys, filenames_values, project, 0, len(filenames_values[0]))
	#align high to low res image 
	# align_layers(model_index, octave_size, layerset)
#	align_layers(model_index, octave_size, layerset, True) #could change number of threads
#align_layers(model_index, octave_size, layerset) #could change number of threads
#	Saves the project with OV
project.saveAs(os.path.join(sub_dir, temp_proj_name+"stiched"), False) #save project file before z alignment 	
param = Align.ParamOptimize(desiredModelIndex=model_index, expectedModelIndex=model_index -
                                        1, correspondenceWeight=0.3)  # which extends Align.Param
param.sift.maxOctaveSize = 600
for n, layer in enumerate(layerset.getLayers()):
        tiles = layer.getDisplayables(Patch)  # get all tiles
        AlignTask.alignPatches(
            param,
            tiles,
            [tiles[0]],  # non_move,
            True,
            False,
            False,
            False)
project.saveAs(os.path.join(sub_dir, temp_proj_name+"re_aligned"), False) #save project file before z alignment 	            
# if proj_folds:
# 	project.saveAs(os.path.join(proj_folds[num], temp_proj_name+"with_low_res"), False)
# else:
# 	project.saveAs(os.path.join(sub_dir, temp_proj_name+"with_low_res"), False)
#removes the OV tile
layerset.setMinimumDimensions() #readjust canvas to only high res tiles
#remove OV from layers
remove_OV(layerset,0)
#exports images
mini_dir= make_dir(output_dir,  "export_unprocessed_"+str(num))
exportProject(project, mini_dir,canvas_roi=True)#,blend=True)
mini_dir= make_dir(output_dir,  "export_processed_"+str(num))
exportProject(project, mini_dir,canvas_roi=True, processed=True)#,blend=True)

project.saveAs(os.path.join(sub_dir, temp_proj_name+"without_low_res"), False)

optionalClosingAndDeleting(project,output_dir,project_name)

print("Done!")
