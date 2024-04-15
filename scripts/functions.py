"""
Title: functions.py

Date: March 27th, 2024

Author: Auguste de Pennart

Description:
	functions used in aligning images in the Z plane and montages them in the x-y plane in trakem2 on imagej

List of functions:
	See below for user defined functions.

List of "non standard modules"
	No non standard modules are used in the program.

Procedure:
	NA

Usage:
	As long as the using script is in the same directory as this function script, functions can be used 

known error:
	No known errors
	
based off of Albert Cardona 2011-06-05 script

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

# import modules
# ----------------------------------------------------------------------------------------
import os
import re
import sys
import shutil
from ij import IJ, ImagePlus, plugin, WindowManager, ImageStack
from ini.trakem2 import Project
from ini.trakem2.display import Display, Patch, LayerSet
from ini.trakem2.imaging import Blending
# for aligning/montaging
from mpicbg.trakem2.align import Align, AlignTask, AlignLayersTask, ElasticMontage
#from ini.trakem2.utils import Filter
# for exporting
from ij.io import FileSaver
from java.awt import Color
from mpicbg.ij.clahe import FastFlat, Flat
# for gui
# https://mirror.imagej.net/developer/api/ij/gui/
from ij.gui import GenericDialog
from ij.gui import GUI
# could be useful for threads/ flushing image cache
from java.lang import Runtime
from java.util.concurrent import Executors, TimeUnit
# align 
from ini.trakem2.utils import Filter
#transform
import register_virtual_stack.Transform_Virtual_Stack_MT as Transform_VS

import copy

# func: supposedly releases cache memory

def releaseAll():
	Project.getProjects()[0].getLoader().releaseAll()

# func: finds mutual folder between both input folders
# inputs:
#	folder_1:
#		first folder
#	folder_2:
#		second folder
#	windows:
#		running on windows or not
# #outputs:
#	joint_folder:
#		mutual parent folder
def mut_fold(folder_1=None, folder_2=None, windows=None):
	#	variables
	joint_folder = []
	if folder_1 == folder_2:  # checks that two different folders were given
		print("ERROR: same folder selected for OV and NO")
		sys.exit("same folder selected for OV and NO")
	if windows:  # finds all the parent directories of the input folders
		match_1 = re.findall(".[^\\\\]+", folder_1)
		match_2 = re.findall(".[^\\\\]+", folder_2)
	elif not windows:
		match_1 = re.findall("\/.[^\/]+", folder_1)
		match_2 = re.findall("\/.[^\/]+", folder_2)
	for Folder in reversed(match_1):  # finds that smallest mutual directory
		if Folder in match_2:
			joint_folder.insert(0, Folder)
	joint_folder = "".join(joint_folder)
	return joint_folder


# func:sorts through files
# inputs:
#	file_list:
#		list of files to be sorted
#	sort_by_digit:
#		specified digit to sort by
#	rev:
#		places objects in descending order
# #outputs:
#	file_list:
#		list of sorted files/objects
def file_sort(file_list=None, sort_by_digit=0, rev=False):
	for n, filename in enumerate(file_list):
		for m, filename_2 in enumerate(file_list[n+1:len(file_list)]):
			try:
				match = int(re.findall("(\d+)", str(filename))[sort_by_digit]) #looks for digits
				match_2 = int(re.findall(
					"(\d+)", str(filename_2))[sort_by_digit])
			except IndexError:
				print(" ERROR: Currently only works with filenames containing digits")
				sys.exit("Currently only works with filenames containing digits")
			if not rev:
				if match > match_2:
					temp_1 = filename
					temp_2 = filename_2
					filename = temp_2
					filename_2 = temp_1
					file_list[n] = temp_2
					file_list[n+m+1] = temp_1
			if rev:
				if n < n+1:
					temp_1 = filename
					temp_2 = filename_2
					filename = temp_2
					filename_2 = temp_1
					file_list[n] = temp_2
					file_list[n+m+1] = temp_1
	return file_list

# func: makes filepath list
# inputs:
#	loop_fold:
#		parent folder
#	windows:
#		running on windows or not
#	append_fold:
#		seperate parent folder
# outputs:
#	all_folder_list:
#		list of folders
def folder_find(loop_fold=None,  windows=None, append_fold=None):
	#	variables
	all_folder_list = []
	filenames = os.listdir(loop_fold)
	for filename in filenames:  # creates filepaths for each subdirectory in loop_fold
		if windows:
			filename = loop_fold+"\\"+filename
		elif not windows:
			filename = loop_fold+"/"+filename
		if os.path.isdir(filename):
			all_folder_list.append(filename)
	# if no folders found loop_fold, assumes this is instead the folder to find files
	if len(all_folder_list) == 0:
		all_folder_list.append(loop_fold)
	# appends folders for the beginning of list (folders assumed to contain files of interest)
	if append_fold:
		if type(append_fold) == list:
			all_folder_list = append_fold+all_folder_list
		elif type(append_fold) == unicode:
			all_folder_list = [append_fold]+all_folder_list
		else:
			print(" ERROR: expected list or unicode for append_fold")
			sys.exit("expected list or unicode for append_fold")
	return all_folder_list


# func: finds files in input directories
# inputs:
#	all_folder_list:
#		list of filepaths
#	pattern_1:
#		specified pattern to look for when finding files
#	pattern_2:
#		specified pattern to look for when finding files
# outputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names
def file_find(all_folder_list=None, pattern_1=None, pattern_2=None):
	#	variables
	filenames_keys = []
	filenames_values = []
	for fold in all_folder_list:  # finds files in folders
		file_list = filter(pattern_2.match, os.listdir(fold))
		# not sure about this line of code
		if not file_list:  # checks second pattern
			file_list = filter(pattern_1.match, os.listdir(fold))
		filenames_keys.append(fold)
		filenames_values.append(file_sort(file_list,-1))
	for num in range(0, len(filenames_keys)):  # checks whether any images were found
		if not filenames_keys[num] or not filenames_values[num]:
			print("ERROR: no files found, check folder or pattern")
			sys.exit(" no files found, check folder or pattern")
	return filenames_keys, filenames_values


# func: finds duplicates and checks for same number of files in folder
# inputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names
def dup_find(filenames_keys=None, filenames_values=None):
	# checks for same number of files in each folder
	for i, fold in enumerate(filenames_keys):
		if i == 0:
			length = len(filenames_values[i])
		elif i != 0:
			if length != len(filenames_values[i]):
				print("ERROR: not an equal number of files in each folder")
				sys.exit("not an equal number of files in each folder")
		# checks for duplicates
		for n, filename in enumerate(filenames_values[i]):
			for m, filename_2 in enumerate(filenames_values[i][n+1:len(filenames_values[i])]):
				if filename == filename_2:
					print("ERROR: found duplicate", filename, filename_2,
						  "at position", n+1, m+1, "in folder")
					sys.exit("found duplicate", filename, filename_2,
							 "at position", n+1, m+1, "in folder")

# func: makes directory
# inputs:
#	filepath:
#		file path
#	dir_name:
#		name for new directory
#	file_var:
#		image variable
#	filename:
#		name of image
#	windows:
#		running on windows or not
#	savefile:
#		specify image to be saved as well
# outputs:
#	new_dir:
#		the new directory filepath
def make_dir(filepath=None, dir_name=None, file_var=None, filename=None, windows=None, savefile=False):
	new_dir = os.path.join(filepath, dir_name)  # make new directory
	try:  # if error, directory already exists
		os.mkdir(new_dir)
	except OSError:
		pass
	if savefile:  # save image as tiff, accounting for if on a windows machine and the amout of files to be saved
		if windows:
			if file_var.getDimensions()[3] != 1:
				plugin.StackWriter.save(file_var, new_dir+"\\", "format=tiff")
			# one file
			elif file_var.getDimensions()[3] == 1:
				IJ.saveAs(file_var, "Tiff", new_dir+"\\"+filename)
		elif not windows:
			if file_var.getDimensions()[3] != 1:
				plugin.StackWriter.save(file_var, new_dir+"/", "format=tiff")
			# one file
			elif file_var.getDimensions()[3] == 1:
				IJ.saveAs(file_var, "Tiff", new_dir+"/"+filename)
	return new_dir

# func: inverts images
# inputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names
#	joint_folder:
#		parent directory
#	windows:
#		running on windows or not
#	pattern:
#		specified pattern to look for when finding files
#	file_start:
#		from which substack of images in filenames_keys should inversion occur
# outputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names
def invert_image(filenames_keys=None, filenames_values=None, joint_folder=None, windows=None, pattern=None, file_start=1):
	for n, fold in enumerate(filenames_keys[file_start:]):
		for m, filename in enumerate(filenames_values[file_start:][n]):
			filepath = os.path.join(fold, filename)
			imp = IJ.openImage(filepath)
			IJ.run(imp, "Invert", "")
			sub_dir = make_dir(joint_folder, "_"+str(n),
							   imp, "/"+str(n)+"_"+str(m), windows, True)
			NO_file = filter(pattern.match, os.listdir(sub_dir))
			NO_file = file_sort(NO_file)
			filenames_keys[n+file_start] = sub_dir
			filenames_values[n+file_start] = NO_file
	return filenames_keys, filenames_values

# func: adds images to each layer in trakem2
# inputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names
#	project:
#		trakem2 project variable
#	start_lay:
#		start point for first layer (should be zero)
#	tot_lay:
#		how many layers to be made
# outputs:
#	layerset:
#		all layers in trakem2 project
# fix:
#	merge this and following function
def add_patch(filenames_keys=None, filenames_values=None, project=None, start_lay=None, tot_lay=None): 
	layerset = project.getRootLayerSet()#get the layerset
	for i in range(start_lay,tot_lay):#add to the layerset the desired amount of layers 
		layerset.getLayer(i, 1, True)
	for i ,layer in enumerate(layerset.getLayers()): #add images to each layer
		for n, fold in enumerate(filenames_keys):
			filepath = os.path.join(fold, filenames_values[n][i-start_lay])
			patch = Patch.createPatch(project, filepath)
			layer.add(patch)
			layer.setOverlay(None) #unsure what this does
			layer.recreateBuckets() #update layerset?
	return layerset

# func: adds images to each layer in trakem2 with additional feature to specify from which layer to start adding images at
# inputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names
#	project:
#		trakem2 project variable
#	start_lay:
#		start point for first layer (should be zero)
#	tot_lay:
#		how many layers to be made
#	transform_folder:
#		directory of transform coordinates
# outputs:
#	layerset:
#		all layers in trakem2 project
def add_patch_v2(filenames_keys=None, filenames_values=None, project=None, start_lay=None, tot_lay=None,transform_folder=None):
	layerset = project.getRootLayerSet()  # get the layerset
	for i in range(start_lay, tot_lay):  # add to the layerset the desired amount of layers
		layerset.getLayer(i, 1, True)
	for i, layer in enumerate(layerset.getLayers()):  # add images to each layer
		if i >= start_lay:
			for n, fold in enumerate(filenames_keys):
				if transform_folder:
					xml_file= "image_stack_"+str(n+1)+".xml"
					path=os.path.join(transform_folder,xml_file)
					transform = Transform_VS.readCoordinateTransform(path)
				filepath = os.path.join(fold, filenames_values[n][i-start_lay])
				patch = Patch.createPatch(project, filepath)
				if transform_folder:
					patch.setCoordinateTransform(transform)
				layer.add(patch)
			layer.recreateBuckets()  # update layerset?
	return layerset

# func: preps images for a test align to see if parameters chosen work with images
# inputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names
#	test_folder:
#		parent directory
#	windows:
#		running on windows or not
#	project_name:
#		name of project
#	invert_image:
#		whether to invert image or not
#	size:
#		transform factor (ie. make it 4 times as small)
#	empty:
#		for high_res.py adds a directory for test high res images
# outputs:
#	temp_filenames_keys:
#		file paths
#	temp_filenames_values:
#		file names
def prep_test_align(filenames_keys=None, filenames_values=None, test_folder=None, windows=None, project_name=None, invert_image=False, size=None,empty=False):
	temp_filenames_keys = []
	temp_filenames_values = []
	temp_filenames_keys += filenames_keys
	temp_filenames_values += filenames_values
	test_interim = make_dir(
		test_folder, "substack_"+re.findall("\d+", project_name)[-1])  # makes directory
	if empty:
		sub_dir = make_dir(test_interim, "_"+str(0))
	for num in range(0, len(filenames_keys)):  # resizes and inverts images
		# this (also in invert) could become funciton
		path = os.path.join(filenames_keys[num], filenames_values[num][0])
		imp = IJ.openImage(path)
		title = imp.getTitle()
		if size:
			if size != 1:  # resizes image to smaller rather larger
				width = int((imp.getDimensions()[0])*(float(1)/float(size)))
				height = int((imp.getDimensions()[1])*(float(1)/float(size)))
				# resize images
				interpolation_method = "Bicubic" 
				imp = imp.resize(width, height, interpolation_method)
		if invert_image:  # inverts image
			IJ.run(imp, "Invert", "")
		# makes directory and saves file
		if empty:
			sub_dir = make_dir(test_interim, "_"+str(num+1),
							   imp, str(num)+"_"+title, windows, True)
		elif not empty:
			sub_dir = make_dir(test_interim, "_"+str(num),
							   imp, title, windows, True)
		temp_filenames_keys[num] = sub_dir  # reasigns new filepath and image
		temp_filenames_values[num] = [str(num)+"_"+title]
	return temp_filenames_keys, temp_filenames_values

# func: stiches images together
# inputs:
#	model_index:
#		specified aligning metric (ie. translation, rigid, similarity, affine)
#	octave_size:
#		max image size
#	layerset:
#		all the layers in trakem2 project
#	OV_lock:
#		accounts for difference between low res and high res alignments
#	transform:
#		get coordinates of the transformed images
# outputs:
#	roi:
#		this is the roi per image stack in filenames_key
#	tiles:
#		trakem2 images in layer
# to consider for elastic:
#	furture elastic montage parameters:
	# block matching
	# patch scale 0.2
	# search radius 90 pixel
	# block radius default 50
	# correlation filters
	# minimal PMCC r 0.1
	# maximal curvature ratio 1000 i think 10.00
	# maximual second best 0.90
	# local smoothness filters
	# approximate local transformation affine
	# sigma default 25.00 ?
	# absolute maximal loca ldispalcementL 30
	# relative maximal local displacememt 3
	# select tiles are premontaged
	# spring mesh= default
	# sift based proemontage
	# feature descriptin defautl
def align_layers(model_index=None, octave_size=None, layerset=None, OV_lock=None,transform=False):
	# variables
	non_move = []
	roi = None
	roi_list = []
	# various parameters for alignment
	if OV_lock:
		if model_index > 1:
			param = Align.ParamOptimize(desiredModelIndex=model_index,expectedModelIndex=model_index-1,
										maxEpsilon=25, minInlierRatio=0.05, minNumInliers=7)  # which extends Align.Param
		else:
			param = Align.ParamOptimize(desiredModelIndex=model_index,expectedModelIndex=model_index,
										maxEpsilon=25, minInlierRatio=0.05, minNumInliers=7)  # which extends Align.Param
		param.sift.maxOctaveSize = octave_size
		param.sift.minOctaveSize = octave_size/2
		param.sift.steps = 3
		param.sift.fdBins = 8
		param.sift.fdSize = 4
	if not OV_lock:
		if model_index > 1:
			param = Align.ParamOptimize(desiredModelIndex=model_index, expectedModelIndex=model_index -
										1, correspondenceWeight=0.3)  # which extends Align.Param
		else:
			# which extends Align.Param
			param = Align.ParamOptimize(
				desiredModelIndex=model_index, expectedModelIndex=model_index)
		param.sift.maxOctaveSize = octave_size
	for n, layer in enumerate(layerset.getLayers()):
		tiles = layer.getDisplayables(Patch)  # get all tiles
		layerset.setMinimumDimensions()  # readjust canvas size
		tiles[0].setLocked(True)  # lock the OV stack
		non_move.append(tiles[0]) 	# i believe tihs is what they are looking for
	for n, layer in enumerate(layerset.getLayers()):
		tiles = layer.getDisplayables(Patch)  # get  all tiles of layer
		AlignTask.alignPatches(
			param,
			tiles,
			[tiles[0]],  # non_move,
			False,
			False,
			False,
			False)
		if OV_lock:  # could be optimzied here, as repeat,funciton could take in value instead of OV_lock
			for tile in tiles[0:]:  # roi for each stack of images is collected
				roi = tile.getBoundingBox()  # needed in OV alignment
				roi_list.append(roi)
			roi = roi_list
		if not OV_lock:  # roi for each stack of images, except the first, is collected (i.e. only high res images)
			for n, tile in enumerate(tiles[1:]):
				if n == 0:
					roi = tile.getBoundingBox()  # needed in OV alignment	
				else:
					roi.add(tile.getBoundingBox())
		if transform:
			transforms, transform_XML=get_patch_transform_data(layerset)
			return  roi, tiles, transforms, transform_XML
	return roi, tiles

# func: resizes image
# inputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names
#	joint_folder:
#		parent directory
#	windows:
#		running on windows or not
#	project_name:
#		name of project
#	pattern:
#		specified pattern to look for when finding files
#	size:
#		transform factor (ie. make it 4 times as large)
#	roi:
#		this is the roi per image stack in filenames_key
# outputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names
def resize_image(filenames_keys=None, filenames_values=None, joint_folder=None, windows=None, project_name=None, pattern=None, size=None, roi=None): 
	imp = plugin.FolderOpener.open(
		filenames_keys[0], "virtual")  # open image stack
	title = imp.getTitle()  # get image stack name
	ROI = imp.setRoi(roi.x, roi.y, roi.width, roi.height)
	imp = imp.crop("stack")  # crop image to new roi
	old_dim = imp.getDimensions()
	# change image dimensions by specified factor
	width = imp.getDimensions()[0]*size
	height = imp.getDimensions()[1]*size
	# resize image to changed image dimensions
	imp = imp.resize(width, height, "none")
	Title = imp.setTitle("")  # create new image stack name
	# save to specified directory
	output_scaled = make_dir(joint_folder, "_0", imp, title, windows, True)
	OV_file = filter(pattern.match, os.listdir(
		output_scaled))  # find new saved files
	OV_file = file_sort(OV_file)  # sort in ascending order
	# save new filepath and images to filenames_keys and filenames_values
	filenames_keys[0] = output_scaled
	filenames_values[0] = OV_file
	return filenames_keys, filenames_values

# func: removes trakem2 tiles
# #inputs:
#	tiles:
#		trakem2 tiles from a layer
def remove_tiles(tiles=None):
	for tile in tiles:
		tile.remove(False)

# func: removes the OV tile
# #inputs:
#	layerset:
#		the trakem2 layers
#	image_rem_num:
#		tile number to remove
def remove_OV(layerset=None, image_rem_num=None):
	for i, layer in enumerate(layerset.getLayers()):
		tiles = layer.getDisplayables(Patch)
		tiles[image_rem_num].remove(False)

# %% Elastic alignment
"Following is experimental code modified and written to try to implement elastic alignment"
"author: Viggo Troback"

def save_xml_files(xml_data_list, destination_directory,size=1,scaling_factor=1,roi=None): #edited by Auguste
	for idx, xml_data in enumerate(xml_data_list):
		# Specify the filename for the XML file (you can customize this as needed)
		xml_filename = "image_stack_{}.xml".format(idx+1)
		# Create the full path for the destination file
		destination_file_path = os.path.join(destination_directory, xml_filename)
		# Write the XML data to the file
		with open(destination_file_path, "w") as xml_file:
			xml_data_list = list(xml_data.split("\n"))
			for line in xml_data_list:
				if re.findall("AffineModel2D", line): # makes directory
					data_string=re.findall("data=\"[\d.\sE\-]+", line) # makes directory
				   #should only be one line in content
					numbers=data_string[0].replace("data=\"","")
					numbers=re.findall("[\d.\-E]+", numbers)
					if size == 1:
						new_x=str(float(numbers[4])/scaling_factor)
						new_y=str(float(numbers[5])/scaling_factor)
					elif size > 1:
						if idx == 0:
							new_x=str(float(numbers[4])/scaling_factor)
							new_y=str(float(numbers[5])/scaling_factor)
						elif idx == 1:
							new_x=str((int(float(numbers[4]))-int(float(numbers[4])))*size/scaling_factor+int(float(numbers[4]))*size/scaling_factor-roi.x*size)
							new_y=str((int(float(numbers[5]))-int(float(numbers[5])))*size/scaling_factor+int(float(numbers[5]))*size/scaling_factor-roi.y*size)
							first_numbers=numbers
						elif idx > 1:
							#to explain the function below:
							#rescaling the second image and beyond, rescaling isn't to be done with the x or y values, but of the distance 
							#between the first image and the next image of interest.
							#then you need to place it where it should be based off the scaled first image
							#then readjust placement with regards to the cropped ov stack 
							new_x=str((int(float(numbers[4]))-int(float(first_numbers[4])))*size/scaling_factor+int(float(first_numbers[4]))*size/scaling_factor-roi.x*size)
							new_y=str((int(float(numbers[5]))-int(float(first_numbers[5])))*size/scaling_factor+int(float(first_numbers[5]))*size/scaling_factor-roi.y*size)
					new_data_string=data_string[0].replace(numbers[4],new_x)
					new_data_string=new_data_string.replace(numbers[5],new_y)
					new_content=line.replace(data_string[0],new_data_string)
					xml_file.write(new_content)
				else:
					xml_file.write(line)

def optionalClosingAndDeleting(project, output_directory,project_name):
	# Create a dialog box with Yes/No options as checkboxes
	gd = GenericDialog("Close Windows and Remove Interim Files")
	gd.addMessage("Alignment finished. You have used:" + str(IJ.currentMemory) + " of " + str(IJ.maxMemory))
	gd.addCheckbox("Close open project windows", True)
	gd.addCheckbox("Remove all interim files", False)
	gd.showDialog()
	if gd.wasCanceled():
		print("Operation canceled.")
	elif gd.wasOKed():
		close_windows = gd.getNextBoolean()
		remove_interim_files = gd.getNextBoolean()
		if close_windows:
			# Close all open windows and project
			IJ.run("Close All")
			project.remove(True)
		if remove_interim_files:
			# Remove all interim file folders 
			interim_folders=filter(re.compile(".*"+re.escape(project_name)).match, os.listdir(output_directory))
			export_files=filter(re.compile('.*export.*').match,interim_folders)
			for exported in export_files: #removes export images from delete list
				interim_folders.remove(exported)
			str_interim_folders="\n-".join(interim_folders)
			gui = GUI.newNonBlockingDialog("Delete?")
			gui.addMessage(" Press ok to delete following interim files: \n-"+str_interim_folders)
			gui.showDialog()
			if gui.wasOKed():
				for folder_name in interim_folders:
					if not re.findall("export", folder_name):
						folder_path = os.path.join(output_directory, folder_name)
						if os.path.exists(folder_path) and os.path.isdir(folder_path):
							delete_non_empty_folder(folder_path)
			elif not gui.wasOKed():
				pass

					
def delete_non_empty_folder(folder_path):
	try:
		for root, dirs, files in os.walk(folder_path, topdown=False):
			for file in files:
				file_path = os.path.join(root, file)
				os.remove(file_path)
		# After removing all files, delete the folders in reverse order to avoid errors
		for dir_name in dirs:
			dir_path = os.path.join(folder_path, dir_name)
			delete_non_empty_folder(dir_path)
		# Finally, remove the top-level folder
		os.rmdir(folder_path)
		print("Deleted folder:{}".format(folder_path))
	except OSError as e:
		print("Error deleting folder:",folder_path,e)


def get_patch_transform_data(layerset):
	# Create a dictionary to store transformation data for each tile
	transformation_data = {}
	transformation_files =[]
	# Loop through each tile in the layerset
	for layer in layerset.getLayers():
		tiles = layer.getDisplayables(Patch)
		for n, tile in enumerate(tiles):
			# Get the transformation for the tile
			transform = tile.getFullCoordinateTransform()
			# Store the transformation data for the tile
			transformation_data[n] = transform
			transformation_files.append(transform.toXML(""))
	return transformation_data, transformation_files


def prep_test_align_viggo(filenames_keys=None, filenames_values=None,
						  test_folder=None, windows=None, project_name=None,
						  invert_image=False, size=None):
	temp_filenames_keys = []
	temp_filenames_values = []
	temp_filenames_keys += filenames_keys
	temp_filenames_values += filenames_values
	test_interim = make_dir(
		test_folder, "substack_"+re.findall("\d+", project_name)[-1])  # makes directory
	for num in range(0, len(filenames_keys)):  # resizes and inverts images
		# this (also in invert) could become funciton
		path = os.path.join(filenames_keys[num], filenames_values[num][0])
		imp = IJ.openImage(path)
		title = imp.getTitle()
		if size:
			if num == 0:
				scaling_factor=get_scaling_factor(imp)
			width = int((imp.getDimensions()[0])*scaling_factor)
			height = int((imp.getDimensions()[1])*scaling_factor)
			#I am not sure what to use here. "bilinear" is recommended, but gives black outlines in the picture.
			#Maybe a different method can remove this?
			interpolation_method = "Bicubic" 
			# resize images
			imp = imp.resize(width, height, interpolation_method)
		if invert_image:  # inverts image
			IJ.run(imp, "Invert", "")
		# makes directory and saves file
		sub_dir = make_dir(test_interim, "_"+str(num),
						   imp, title, windows, True)
		temp_filenames_keys[num] = sub_dir  # reasigns new filepath and image
		temp_filenames_values[num] = [title]
	return temp_filenames_keys, temp_filenames_values, scaling_factor


def get_scaling_factor(tiles):
	gd = GenericDialog("Image Rescale Factor")
	current_width = tiles.getWidth()
	current_height = tiles.getHeight()
	gd.addMessage("Current size: %d x %d" % (current_width, current_height))
	gd.addNumericField("\tRescaling Factor", 0.2, 2)  # Default rescaling factor of 0.5
	gd.addMessage("*Rescaling image smaller will speed up alignment test.")
	gd.showDialog()
	if gd.wasCanceled():
		return 1  # Return 1 if the user clicked Cancel
	# Get the user input rescaling factor
	scaling_factor = gd.getNextNumber()
	if scaling_factor <= 0:
		IJ.showMessage("Invalid Rescaling Factor",
					   "Please enter a positive value for the rescaling factor.")
		return get_scaling_factor(tiles)  # Call itself recursively to get a valid factor
	return scaling_factor


def GUIElasticParameters():
	gui = GUI.newNonBlockingDialog(
		"Elastic alignment options (for standard, just press ok.)")
	# Add fields for each parameter with appropriate data types
	gui.addNumericField("Block Radius:", 50)
	gui.addNumericField("Local Model Index:", 1)
	gui.addNumericField("Local Region Sigma:", 25)
	gui.addNumericField("Max Curvature R:", 10)
	gui.addNumericField("Max Local Epsilon:", 0.001)
	gui.addNumericField("Max Local Trust:", 0.1)
	gui.addNumericField("Min R:", 0.001)
	gui.addNumericField("Rod R:", 0.005)
	gui.addNumericField("Layer Scale:", 2.0)
	gui.addNumericField("Search Radius:", 90)
	gui.addNumericField("Max Iterations Spring Mesh:", 100)
	gui.addNumericField("Max Plateau Width Spring Mesh:", 0)
	gui.addNumericField("Max Stretch Spring Mesh:", 0.3)
	gui.addNumericField("Stiffness Spring Mesh:", 0.8)
	gui.addNumericField("Damp Spring Mesh:", 0.1)
	gui.addCheckbox("Is Aligned:", False)
	gui.addCheckbox("Use Local Smoothness Filter:", True)
	gui.addCheckbox("Use Legacy Optimizer:", False)
	gui.addCheckbox("Visualize:", True)
	# Show the dialog
	gui.showDialog()
	# Check if the user clicked "OK"
	if gui.wasOKed():
		# Create an instance of ElasticMontage.Param
		param = ElasticMontage.Param()
		# Set the values obtained from the GUI to the corresponding fields of ElasticLayerAlignment.Param
		param.bmBlockRadius = int(gui.getNextNumber())  # int
		param.bmLocalModelIndex = int(gui.getNextNumber())  # int
		param.bmLocalRegionSigma = float(gui.getNextNumber())  # float
		param.bmMaxCurvatureR = float(gui.getNextNumber())  # float
		param.bmMaxLocalEpsilon = float(gui.getNextNumber())  # float
		param.bmMaxLocalTrust = float(gui.getNextNumber())  # float
		param.bmMinR = float(gui.getNextNumber())  # float
		param.bmRodR = float(gui.getNextNumber())  # float
		param.bmScale = float(gui.getNextNumber())  # double
		param.bmSearchRadius = int(gui.getNextNumber())  # int
		param.maxIterationsSpringMesh = int(gui.getNextNumber())  # int
		param.maxPlateauwidthSpringMesh = int(gui.getNextNumber())  # int
		param.maxStretchSpringMesh = float(gui.getNextNumber())  # double
		param.stiffnessSpringMesh = float(gui.getNextNumber())  # double
		param.dampSpringMesh = float(gui.getNextNumber())  # double
		param.isAligned = gui.getNextBoolean()  # boolean
		param.bmUseLocalSmoothnessFilter = gui.getNextBoolean()  # boolean
		param.useLegacyOptimizer = gui.getNextBoolean()  # boolean
		param.visualize = gui.getNextBoolean()  # boolean
		# Now you can use the param object as needed
		return param
	else:
		return None  # Dialog was canceled or closed, return None


def joinTilesLinear(tiles,model_index,octave_size):
	if model_index > 1:
			param = Align.ParamOptimize(desiredModelIndex=model_index, expectedModelIndex=model_index-1,
										correspondenceWeight=0.3)  # which extends Align.Param
	else:
			param = Align.ParamOptimize(desiredModelIndex=model_index,expectedModelIndex=model_index,correspondenceWeight=0.3)  # which extends Align.Param
	param.sift.maxOctaveSize = octave_size
	AlignTask.alignPatches(
		param,
		tiles,
		[tiles[0]],  # non_move,
		False,
		False,
		False,
		False)

		

def joinTilesElastic(param, tiles):
	# Create an instance of ElasticMontage
	elasticMontage = ElasticMontage()
	elasticParam = elasticMontage.Param()
	# Set the parameters for the ElasticMontage instance using the provided param object
	elasticParam.bmBlockRadius = param.bmBlockRadius
	elasticParam.bmLocalModelIndex = param.bmLocalModelIndex
	elasticParam.bmLocalRegionSigma = param.bmLocalRegionSigma
	elasticParam.bmMaxCurvatureR = param.bmMaxCurvatureR
	elasticParam.bmMaxLocalEpsilon = param.bmMaxLocalEpsilon
	elasticParam.bmMaxLocalTrust = param.bmMaxLocalTrust
	elasticParam.bmMinR = param.bmMinR
	elasticParam.bmRodR = param.bmRodR
	elasticParam.bmScale = param.bmScale
	elasticParam.bmSearchRadius = param.bmSearchRadius
	elasticParam.maxIterationsSpringMesh = param.maxIterationsSpringMesh
	elasticParam.maxPlateauwidthSpringMesh = param.maxPlateauwidthSpringMesh
	elasticParam.maxStretchSpringMesh = param.maxStretchSpringMesh
	elasticParam.stiffnessSpringMesh = param.stiffnessSpringMesh
	elasticParam.dampSpringMesh = param.dampSpringMesh
	elasticParam.isAligned = param.isAligned
	elasticParam.bmUseLocalSmoothnessFilter = param.bmUseLocalSmoothnessFilter
	elasticParam.useLegacyOptimizer = param.useLegacyOptimizer
	elasticParam.visualize = param.visualize
	fixed=set(copy.copy([tiles[0:]])) 
	elasticMontage.exec(elasticParam, tiles, fixed)
	


def align_layers_elastic(parameters, model_index, layerset=None, OV_lock=None,
						 octave_size=None):

  
	# variables
	roi = None
	roi_list = []
	# various parameters for alignment
	param = parameters
	for n, layer in enumerate(layerset.getLayers()):
		tiles = layer.getDisplayables(Patch)  # get  all tiles of layer
		joinTilesLinear(tiles,model_index, octave_size)
	transforms, transform_XML=get_patch_transform_data(layerset)
	for n, layer in enumerate(layerset.getLayers()):
		tiles = layer.getDisplayables(Patch)  # get  all tiles of layer
		joinTilesElastic(param, tiles)
		if OV_lock:  # could be optimzied here, as repeat,funciton could take in value instead of OV_lock
			for tile in tiles[0:]:  # roi for each stack of images is collected
				roi = tile.getBoundingBox()  # needed in OV alignment
				roi_list.append(roi)
			roi = roi_list
		if not OV_lock:  # roi for each stack of images is collected
			roi = tiles[1].getBoundingBox()  # needed in OV alignment
			for tile in tiles[1:]:
				roi.add(tile.getBoundingBox())
	transforms2, transform_XML2=get_patch_transform_data(layerset)
	new_lines=""
	transform_XML3=[]
	for n,xml in enumerate(transform_XML2):
		lines = xml.split('\n')
		for line in lines:
			if re.findall("AffineModel2D", line): # makes directory
			   new_line=transform_XML[n]
			   new_lines+="\t"+new_line+"\n"
			else:
			   new_lines+=line+"\n"
		transform_XML3.append(new_lines)
		new_lines=""
	return roi, tiles, transform_XML3

def exportProject(project=None, output_dir=None, canvas_roi=False, processed=False, blend=False):
	# export variables
	export_type = 0  # GRAY8
	backgroundColor = Color(0, 0, 0, 0)
	scale = 1.0
	# additional processing variables (gaussian blur, CLAHE )
	sigmaPixels = 0.7
	blocksize = 300
	histogram_bins = 256
	maximum_slope = 1.5
	mask = "*None*"
	fast = True
	process_as_composite = False
	composite = False
	mask = None
	layerset = project.getRootLayerSet()
	for i, layer in enumerate(layerset.getLayers()):  # loop through each layer
		tiles = layer.getDisplayables(Patch)
		if canvas_roi:  # save image with whole canvas
			roi = layerset.get2DBounds()
		elif not canvas_roi:  # save image without whole canvas
			roi = tiles[0].getBoundingBox()
			for tile in tiles[1:]:
				roi.add(tile.getBoundingBox())
		if blend:  # processes image if desired
			Blending.blend(set(tiles), 0)
		ip = Patch.makeFlatImage(  # image paramaters
			export_type,
			layer,
			roi,
			scale,
			tiles,
			backgroundColor,
			True)  # use the min and max of each tile
			
		img = ImagePlus("Flat montage", ip)  # creates image
		if processed:  # processes image if desired
			img.getProcessor().blurGaussian(sigmaPixels)
#			pretty sure 3 refers to median_filter
#			https://imagej.nih.gov/ij/developer/api/ij/ij/process/ImageProcessor.html#filter(int)
#			imp.getProcessor().filter(3)
			FastFlat.getFastInstance().run(img,
										   blocksize,
										   histogram_bins,
										   maximum_slope,
										   mask,
										   composite)
		FileSaver(img).saveAsTiff(output_dir + "/" + str(i + 1) +
								  ".tif")  # saves file to output directory

# %%
"Reorganising output-files"
"Author: Valentin Gillet"

def get_files_info(directory_path, only_first=True):
	'''
	Return info about tif files based on .info files.
	
	Args:
	
		directory_path (`str`):
		
			Absolute path to a directory containing TIF files and their .info files.
			
		only_first (`bool`):
			
			If True (default), only return info for first file in the directory.
	'''
	
	info_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if '.info' in f]
	if only_first:
		with open(info_files[0], 'r') as f:
			txt = f.read()

		lines = txt.split('\n')

		keys = []
		info = []
		for line in lines:
			if 'pixelsize' in line or 'offset' in line:
				k, x, y = line.split(' ')
				keys.append(k)
				info.append([int(x),int(y)])
			if '.tif' in line:
				tif_name = line.split('"')[1]
				keys.append('tif_name')
				info.append(tif_name)

				keys.append('slice')
				info.append(int(tif_name.split('.')[-2].split('s')[1].split('_')[0]))
		return keys, info
	else:
		files_keys = []
		files_info = []
		for path in info_files:
			with open(path, 'r') as f:
				txt = f.read()
			lines = txt.split('\n')

			keys = []
			info = []
			for line in lines:
				if 'pixelsize' in line or 'offset' in line:
					k, x, y = line.split(' ')
					keys.append(k)
					info.append([int(x),int(y)])
				if '.tif' in line:
					tif_name = line.split('"')[1]
					keys.append('tif_name')
					info.append(tif_name)

					keys.append('slice')
					info.append(int(tif_name.split('.')[-2].split('s')[1].split('_')[0]))
					
			files_keys.append(keys)
			files_info.append(info)
		return files_keys, files_info


def get_stacks(master_dir, resolution, match_pattern='', exceptions=None,get_info=True):		
	'''
	Get alls TIF stacks within the master_dir. Different tiles within a directory will be split.
	Only returns stacks which have a matching resolution according to info files.
	
	Args:
		
		master_dir (`str`):
			
			Absolute path to the directory containing subdirectories with TIF files.
			
		resolution ([2] list of `int`):
		
			Resolution of the TIF files to fetch.
			
		match_pattern (`str`):
		
			Pattern to match in the directory names. Empty string by default.
            			
		exceptions (list of 'str'):
		
			List of string to look for and exclude folders that contain it. None by default
	
	'''
	# List subdirectories
	master_dir = os.path.abspath(master_dir)
	directories = [os.path.join(master_dir, d) for d in os.listdir(master_dir) if match_pattern in d]
	if exceptions is not None:
		for exception in exceptions:
			directories = [d for d in directories if exception not in d]
	directories.sort()
	# Iterate over each subdirectory to find correct TIF files
	list_files = []

	for directory in directories:
		#get_files_info only works if there are info files in the folder
	 	if get_info:
			# If resolution does not correspond, skip directory
			k_info, v_info = get_files_info(directory)
			if resolution != v_info[k_info.index('pixelsize')]:
				continue
		
		all_tifs = [os.path.join(directory, f) for f in os.listdir(directory) if '.tif' in f]
		files = [f for f in all_tifs if 'Tile_001-001' in f]
		files.sort()

		# If there are more than one tile in this stack, iterate over the possible matches, split them into different stacks
		div = int(len(all_tifs)/len(files))
		if div > 1:
			for i in range(1, div+1):
				for j in range(1, div+1):
					match='Tile_{:03d}-{:03d}'.format(i, j)
					files = [os.path.join(directory, f) for f in all_tifs if match in f]
					files.sort()
					
					if len(files):
						list_files.append(files)
		else:
			list_files.append(files)
			
	return list_files

def split_stacks(stacks_list):
	'''
	Return list of lists of absolute TIF file paths.
	Split stacks into lists of strictly overlapping stacks of images:
	
		Z|__A__|  B  |  C  | 
		0|  x  |     |     |
		1|__x__|     |_____|_ SPLIT
		2|  x  |     |  x  |
		3|__x__|_____|__x__|_ SPLIT
		4|  x  |  x  |  x  |
		5|__x__|__x__|__x__|_ SPLIT
		6|     |  x  |     |
		7|     |  x  |     |
		8|     |  x  |     |
		9|     |__x__|     |
	
	Args:
		
		stacks_list ([n] list of `str`):
		
			List of absolute file paths for each stack to consider.
	'''
	# Extract slice index for each file
	stacks_z_list = []
	for files in stacks_list:
		stacks_z_list.append([int(f.split('.')[-2].split('s')[1].split('_')[0]) for f in files])
	
	# Extract the bounds which divide existing stacks
	bounds_z = [max(max(stacks_z_list))]
	for values in stacks_z_list:
		start = min(values)

		if start not in bounds_z:
			bounds_z.append(start)
	bounds_z.sort()
	
	# Iterate over every bound and the following one to find overlapping stacks
	new_stacks = []
	while len(bounds_z) > 1:
		start = int(bounds_z.pop(0))
		end = int(bounds_z[0])-1

		tif_paths = []
		diff = 0
		for i,stack in enumerate(stacks_z_list): 
			if start in stack and end in stack:
				index_a = stack.index(start)
				index_b = stack.index(end)
				tif_paths.append(stacks_list[i][index_a:index_b+1])
			if start not in stack and end not in stack:
				continue
			elif start in stack and end not in stack:
				# If there is a discrepancy between the lenght of a stack and the expected end bound, there could be missing files.
				index_a = stack.index(start)
				index_b = len(stack)
				diff = end - max(stack)
				print('WARNING: missing {} slices.'.format(diff))
				
				tif_paths.append(stacks_list[i][index_a:index_b+1])
		new_stacks.append(tif_paths)
			
	return new_stacks

#additional functions for incorperating the organizer
def get_file_paths_folders(folder_path):
	file_paths = []

	subfolder_names = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]
	for subfolder_name in subfolder_names:
		subfolder_path = os.path.join(folder_path, subfolder_name)
		for file_name in os.listdir(subfolder_path):
			file_path = os.path.join(subfolder_path, file_name)
			if os.path.isfile(file_path):
				file_paths.append(file_path)

	return file_paths


def list_decoder(file_list):
	folder_paths=[]
	file_names=[]
	for a in (file_list):
		folder_paths_temp=[]
		file_names_temp=[]
		for nested_index,directory_set in enumerate(a):
			file_names_temp2=[]
			if len(directory_set)>0:
				for index, value in enumerate(directory_set):
					folder, name = os.path.split(value)
					if index == 0:
						folder_paths_temp.append(folder)
				
					file_names_temp2.append(name)
			
			file_names_temp.append(file_names_temp2)
		file_names.append(file_names_temp)
		folder_paths.append(folder_paths_temp)
	
	return folder_paths, file_names, file_list

# Allow for user to reset tile order
#author: Auguste
#function to get new patch organization after moving them manually	  
def adopt_man_move(layerset,temp_filenames_keys,temp_filenames_values,filenames_keys,filenames_values,roi=None):
	man_moved_tiles=[0]*len(temp_filenames_keys)
	man_moved_paths=[0]*len(temp_filenames_keys)
	# Create a dictionary to store transformation data for each tile
	transformation_data = {}
	transformation_files =[]
	for layer in layerset.getLayers():
		tiles = layer.getDisplayables(Patch)
		for n, tile in enumerate(tiles):
			for m, filename in enumerate(temp_filenames_values):
				if str(tile.title) == str(filename[0]):
					man_moved_tiles[n]=filenames_values[m]
					man_moved_paths[n] = filenames_keys[m]
					# Get the transformation for the tile
					transform = tile.getFullCoordinateTransform()
			# Store the transformation data for the tile
					transformation_data[n] = transform
					transformation_files.append(transform.toXML(""))
			if roi: #i.e., for high_res.py
				if n > 0:
					if n == 1:
						roi = tile.getBoundingBox()  # needed in OV alignment	
					else:
						roi.add(tile.getBoundingBox())
	if roi: #assumes currently one directory for tiles, otherwise will return last set of tiles, not an roi list 
		return man_moved_tiles, man_moved_paths, roi, tiles, transformation_data, transformation_files
	return man_moved_tiles, man_moved_paths, transformation_data, transformation_files


def adjust_roi(roi,scaling_number):
	'''
	reset to actual roi of unmodified image
	
	Args:
		
		roi ('trackem2 roi object'):
			
			region of interest
			
		scaling_number ('int'):
		
			number by which image was scaled
	
	'''
	roi.x=int(roi.x*(1/scaling_number))#adjust roi to the appropriate scaling number, this can be put under functions
	roi.y=int(roi.y*(1/scaling_number))
	roi.width=int(roi.width*(1/scaling_number))
	roi.height=int(roi.height*(1/scaling_number))
	return roi

#simple function for saving tot_roi
def save_roi(roi, destination_directory):
	'''
	saves roi to file
	
	Args:
		
		roi ('trackem2 roi object'):
			
			region of interest
			
		destination_directory ('str'):
		
			file path to where roi file to be saved

	'''
 	roi_number_file=open(os.path.join(destination_directory, str(1)+"_roi.xml"),"w") #makes a file with roi, add to function 
 	roi_number_file.write(str(roi))
 	roi_number_file.close()


def delete_interim(parent_dir,project_name,pattern_tif,pattern_dir,windows,num):
	'''
	function for removing interim folders (inverted or scaled)
	
	Args:
		
		parent_dir (`str`):
			
			Absolute path to the directory containing subdirectories with TIF files to be removed.
			
		project_name(`str`):
		
			name of project
			
		pattern_tif (`str`):
		
			Pattern to match image names. 

		pattern_dir (`str`):
		
			Pattern to match in the directory names. 
            			
		exceptions (list of 'str'):
		
			List of string to look for and exclude folders that contain it. None by default
	
	'''
	output_fold=make_dir(parent_dir, pattern_dir+str(num))
	if num == 0:
		if folder_find(output_fold,windows):
			inverted_subfolders=folder_find(output_fold,windows)
		#checks only first folder, but assuming sufficient
			if filter(pattern_tif.match, os.listdir(inverted_subfolders[0])): #checks whether images already exist
				gui = GUI.newNonBlockingDialog("Delete and rewrite?")
				gui.addMessage(" Press ok to delete and rewrite already inverted files in "+pattern_dir+project_name+"?\n Pressing cancel will exit the script.")#do i need to remove preexisting files
				gui.showDialog()
				if gui.wasOKed():
					interim_folders=filter(re.compile(".*"+re.escape(pattern_dir)).match, os.listdir(parent_dir))
					str_interim_folders="\n-".join(interim_folders)
					gui = GUI.newNonBlockingDialog("Delete?")
					gui.addMessage(" Press ok to delete following interim files: \n-"+str_interim_folders)
					gui.showDialog()
					if gui.wasOKed():
						for folder_name in interim_folders:
							folder_path = os.path.join(parent_dir, folder_name)
							if os.path.exists(folder_path) and os.path.isdir(folder_path):
								delete_non_empty_folder(folder_path)
						for n, folder_name in enumerate(interim_folders):
							make_dir(parent_dir, pattern_dir+str(n))
				elif not gui.wasOKed():
					sys.exit()
	return output_fold
					