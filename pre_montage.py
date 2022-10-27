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
    2. does not invert images,
    3. does not crop images
    4. should open project earlier
    5. should check if interim folder full (kind of does)
    6. get more threads for resizing step
    7. allow for pattern choice, and whether windows machine or not
    8. should open project, if already opened
    9. have time stamps
    10.not cropped currently if not resizing
  
    
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

# import modules
# ----------------------------------------------------------------------------------------
import os, re, sys
from ij import IJ, ImagePlus, plugin
from ini.trakem2 import Project
from ini.trakem2.display import Display, Patch
from ini.trakem2.imaging import Blending
from ij.io import FileSaver
#for aligning/montaging
from mpicbg.trakem2.align import Align, AlignTask
#for exporting
from java.awt import Color
from mpicbg.ij.clahe import Flat
#for gui
#https://mirror.imagej.net/developer/api/ij/gui/
from ij.gui import GenericDialog
from ij.gui import GUI
#could be useful for threads
from java.lang import Runtime
from java.util.concurrent import Executors

#func: finds mutual folder between both input folders
def mut_fold(OV_fold=None,NO_fold=None,is_windows=None):
#	variables
	joint_folder=[]
	if OV_fold == NO_fold:
		print("ERROR: same folder selected for OV and NO" )
		sys.exit("same folder selected for OV and NO" )
	#finds all the parent directories of the input folders
	if is_windows:
		match_1=re.findall(".[^\\\\]+",OV_fold)
		match_2=re.findall(".[^\\\\]+",NO_fold)
	elif not is_windows:
		match_1=re.findall("\/.[^\/]+",OV_fold)
		match_2=re.findall("\/.[^\/]+",NO_fold)
#	print(match_1, match_2)
	#check for the same folder and if dfferent folder finds mutual parent folders
#	if match_1[len(match_1)-1] == match_2[len(match_2)-1]:
#		print("ERROR: same folder selected for OV and NO" )
#		sys.exit("same folder selected for OV and NO" )
#	elif match_1[len(match_1)-1] != match_2[len(match_2)-1]:
	for Folder in reversed(match_1):
		if Folder in match_2:
			joint_folder.insert(0,Folder)
	joint_folder="".join(joint_folder)
#	print(joint_folder)
	return joint_folder


#func:sort_
def file_sort(file_list=None):
#	variables:
	filenames_keys=[]
	filenames_values=[]
	for  n, filename in enumerate(file_list):
		for m, filename_2 in enumerate(file_list[n+1:len(file_list)]):
			match = int(re.findall("(\d+)",filename)[0])
			match_2 = int(re.findall("(\d+)",filename_2)[0])
#			print(filename,filename_2)
			if match > match_2:
				temp_1=filename
				temp_2=filename_2
#				print(filename,filename_2)
				filename=temp_2
				filename_2=temp_1
				file_list[n]=temp_2
				file_list[n+m+1]=temp_1
#				print(filename,filename_2)
	return file_list

def folder_find(fold=None,  is_windows=None, two_fold=None):
#	variables
	all_folder_list=[]
	if two_fold:#if you want both OV and NO in the same list, True (is the case once looking at each substack)
		all_folder_list.append(two_fold)
	filenames =  os.listdir(fold)
	for filename in filenames:
	#	fix if not mac
		if is_windows:
			filename = fold+"\\"+filename
		elif not is_windows:
			filename = fold+"/"+filename
	#	print(filename)
		if os.path.isdir(filename):
	#		print("found folder")
			all_folder_list.append(filename)
	return all_folder_list

#func: find files in input directories
def file_find(OV_fold=None, NO_fold=None, is_windows=None,pattern_1=None, pattern_2=None):
#	variables
#	all_folder_list=[]
#	all_folder_list.append(OV_fold)
#	NO_filenames =  os.listdir(NO_fold)
	filenames_keys=[]
	filenames_values=[]
##	print(NO_filenames)
#	for filename in NO_filenames:
#	#	fix if not mac
#		if is_windows:
#			filename = NO_fold+"\\"+filename
#		elif not is_windows:
#			filename = NO_fold+"/"+filename
#	#	print(filename)
#		if os.path.isdir(filename):
#	#		print("found folder")
#			all_folder_list.append(filename)
	all_folder_list=folder_find(NO_fold, is_windows, OV_fold)
	if  len(all_folder_list)==1:
		all_folder_list.append(NO_fold)
#	else:
#		print("ERROR: no OV folder found" )
#		sys.exit("no OV folder found" )
	for fold in all_folder_list:
		file_list=filter(pattern_2.match, os.listdir(fold))
		#not sure about this line of code
		if not file_list:
	 		file_list=filter(pattern_1.match, os.listdir(fold))
	 	filenames_keys.append(fold)
		filenames_values.append(file_sort(file_list))
	return filenames_keys, filenames_values

	

#func: find duplicates in NO folder, should look in all foldesr
def dup_find(filenames_keys=None, filenames_values=None):
	for i, fold in enumerate(filenames_keys):
		if i ==0:
			length = len(filenames_values[i])
		elif i !=0:
			if length != len(filenames_values[i]):
				print("ERROR: not an equal number of files in each folder")
				sys.exit("not an equal number of files in each folder")
		for n,filename in enumerate(filenames_values[i]):
			for m,filename_2 in enumerate(filenames_values[i][n+1:len(filenames_values[i])]):
				if filename == filename_2:
					print("ERROR: found duplicate", filename, filename_2, "at position", n+1, m+1, "in folder" )
					sys.exit("found duplicate", filename, filename_2, "at position", n+1, m+1, "in folder" )

#makes directory		
def make_dir(path=None, dir_name=None, file_var=None, filename=None, is_windows=None, savefile=False):
	new_dir=os.path.join(path, dir_name)
	try:
		os.mkdir(new_dir)
	except OSError:
		pass
	if savefile:		
		if is_windows:
			if file_var.getDimensions()[3] != 1:
				plugin.StackWriter.save(file_var, new_dir+"\\", "format=tiff");
			#one file
			elif file_var.getDimensions()[3] == 1:
				IJ.saveAs(file_var, "Tiff", new_dir+"\\"+filename)
		elif not is_windows:
			if file_var.getDimensions()[3] != 1:
				plugin.StackWriter.save(file_var, new_dir+"/", "format=tiff");
			#one file
			elif file_var.getDimensions()[3] == 1:
				IJ.saveAs(file_var, "Tiff", new_dir+"/"+filename)
	return new_dir

#func: invert
def invert_image(filenames_keys=None, filenames_values=None, joint_folder=None, windows=None, pattern_3=None):
#	output_inverted=make_dir(joint_folder, "NO_interim")
	for n, fold in enumerate(filenames_keys[1:]):
		for m, filename in enumerate(filenames_values[1:][n]):
			filepath = os.path.join(fold,filename)
			imp=IJ.openImage(filepath);
			IJ.run(imp, "Invert", "");
	#		imp=imp.getProcessor().invert()
			sub_dir=make_dir(joint_folder, "_"+str(n), imp, "/"+str(m),windows, True)
			print(sub_dir)
#			IJ.saveAs(imp, "Tiff", sub_dir+"/"+str(m));
			NO_file=filter(pattern_3.match, os.listdir(sub_dir))
			NO_file=file_sort(NO_file)
			filenames_keys[n+1] = sub_dir
			filenames_values[n+1] = NO_file
	return filenames_keys, filenames_values

def add_patch(filenames_keys=None, filenames_values=None, project=None, start_lay=None, tot_lay=None): #layerset=None,
	layerset = project.getRootLayerSet()
	for i in range(start_lay,tot_lay):
		layerset.getLayer(i, 1, True)
	for i,layer in enumerate(layerset.getLayers()):
			for n, fold in enumerate(filenames_keys):
		#		print(fold)
		#		print(filenames_dict[fold][i])
				filepath = os.path.join(fold, filenames_values[n][i])
				patch = Patch.createPatch(project, filepath)
				layer.add(patch)
		#		print(patch)
			layer.recreateBuckets()
	return layerset

def align_layers(model_index=None, octave_size=None, layerset=None):
	param = Align.ParamOptimize(desiredModelIndex=model_index,expectedModelIndex=model_index)  # which extends Align.Param
	param.sift.maxOctaveSize = octave_size
	for layer in layerset.getLayers():
	  	tiles = layer.getDisplayables(Patch) #get list of tiles
		layerset.setMinimumDimensions() #readjust canvas size
		tiles[0].setLocked(True) #lock the OV stack
		non_move = [tiles[0]] #i believe tihs is what they are looking for
		#montage or align?
		AlignTask.alignPatches(
		param,
		tiles,
		non_move,
		False,
		False,
		False,
		False) 
		roi = tiles[1].getBoundingBox() #needed in OV alignment
	  	for tile in tiles[1:]:
	 		roi.add(tile.getBoundingBox())
	return roi, tiles

def find_crop_area(filenames_keys=None, filenames_values=None, project=None, test_folder=None, proj_folder=None, windows=None, project_name=None, size=None, model_index=None, octave_size=None, invert_image=False): #layerset=None, pattern_3=None
#	layerset = project.getRootLayerSet()
	temp_filenames_keys=[filenames_keys[0]]
	temp_filenames_values=[filenames_values[0]]
	test_interim=make_dir(test_folder, "substack_"+re.findall("\d+",project_name)[-1])
	for num in range(1,len(filenames_keys)):
#		print(filenames_values[num][0])
		path=os.path.join(filenames_keys[num], filenames_values[num][0]) #this (also in invert) could become funciton
		imp=IJ.openImage(path);
		title=imp.getTitle()
		if size != 1:
			old_dim=imp.getDimensions()
			width=int((imp.getDimensions()[0])*(float(1)/float(size)))
			height=int((imp.getDimensions()[1])*(float(1)/float(size)))
			#resize images
			imp = imp.resize(width, height, "none");
#			print("old height is "+str(old_dim.height), "new height is "+str(imp.getDimensions().height))
		#invert
		if invert_image:
			IJ.run(imp, "Invert", "");
		#mac or windows
		sub_dir = make_dir(test_interim, "_"+str(num), imp, title, windows, True)
		temp_filenames_keys.append(sub_dir)
		temp_filenames_values.append([title])
		#sort?
#	print(temp_filenames_keys,temp_filenames_values)
	#populates first layer with OV and NO images
	layerset=add_patch(temp_filenames_keys, temp_filenames_values, project, 0, 1)
	roi, tiles =align_layers(model_index, octave_size, layerset)
	project.saveAs(os.path.join(proj_folder, project_name+"test"), False)	
	return roi, tiles

def remove_tiles(tiles=None):
	for tile in tiles:
		tile.remove(False)

#roi
def resize_image(filenames_keys=None, filenames_values=None, joint_folder=None, windows=None, project_name=None, pattern_3=None, size=None, roi=None): #layerset=None, project=None
	imp = plugin.FolderOpener.open(filenames_keys[0], "virtual");
	title=imp.getTitle()
	ROI=imp.setRoi(roi.x-10,roi.y-10,roi.width+10,roi.height+10);
	print(imp.getDimensions())
	imp=imp.crop("stack")
	old_dim=imp.getDimensions()
	width=imp.getDimensions()[0]*size
	height=imp.getDimensions()[1]*size
	#resize images
	imp = imp.resize(width, height, "none");
	print(old_dim, imp.getDimensions())
	#multiple files
	#mac or windows
	Title=imp.setTitle("")
	output_scaled=make_dir(joint_folder, "OV_interim"+_,imp, title, windows, True)
	OV_file=filter(pattern_3.match, os.listdir(output_scaled))
	OV_file=file_sort(OV_file)
	filenames_keys[0] = output_scaled
	filenames_values[0] = OV_file
	return filenames_keys, filenames_values
	
#removes the OV tile
def remove_OV(layerset=None,image_rem_num=None):
	for i, layer in enumerate(layerset.getLayers()):
		tiles = layer.getDisplayables(Patch)
		tiles[image_rem_num].remove(False)

#exports images
def export_image(layerset=None, output_dir=None, canvas_roi=False, processed=False, blocksize=None, histogram_bins=None,maximum_slope=None):
	#export variables
	export_type=0 #GRAY8
	backgroundColor = Color(0,0,0,0)
	scale = 1.0
	#process variables
	mask = "*None*"
	fast = True
	process_as_composite = False
	composite = False
	mask = None
	for i, layer in enumerate(layerset.getLayers()):
		#  print(layer)
		tiles = layer.getDisplayables(Patch)
		#  print(tiles)
		if canvas_roi:
			roi=layerset.get2DBounds() # was useful for saving NO in 2D space
		elif not canvas_roi:
			roi = tiles[0].getBoundingBox() #needed in OV alignment
			for tile in tiles[1:]:
				roi.add(tile.getBoundingBox())
		  	#image paramaters, i believe
		ip = Patch.makeFlatImage(
		       export_type,
		       layer,
		       roi,
		       scale,
		       tiles, # only getting NO patch
		       backgroundColor,
		       True)  # use the min and max of each tile
		imp = ImagePlus("Flat montage", ip) #creates image
		if processed:
			imp.getProcessor().blurGaussian(sigmaPixels)
#			pretty sure 3 refers to median_filter
#			https://imagej.nih.gov/ij/developer/api/ij/ij/process/ImageProcessor.html#filter(int)
#			imp.getProcessor().filter(3)
			FastFlat.getFastInstance().run( imp, 
			                    blocksize,
			                    histogram_bins,
			                    maximum_slope,
			                    composite,
			                    mask)
		FileSaver(imp).saveAsTiff(output_dir + "/" + str(i + 1) + ".tif") #saves file to output directory
