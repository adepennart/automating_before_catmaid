"""
Title: functions.py

Date: February 9th, 2023

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
import os, re, sys
import shutil
from ij import IJ, ImagePlus, plugin
from ini.trakem2 import Project
from ini.trakem2.display import Display, Patch
from ini.trakem2.imaging import Blending
from ij.io import FileSaver
#for aligning/montaging
from mpicbg.trakem2.align import Align, AlignTask, AlignLayersTask
#from ini.trakem2.utils import Filter
#for exporting
from java.awt import Color
from mpicbg.ij.clahe import FastFlat, Flat
#for gui
#https://mirror.imagej.net/developer/api/ij/gui/
from ij.gui import GenericDialog
from ij.gui import GUI
#could be useful for threads/ flushing image cache
from java.lang import Runtime
from java.util.concurrent import Executors, TimeUnit

#align
from ini.trakem2.utils import Filter

# func: flushes image cache
def releaseAll():
	Project.getProjects()[0].getLoader().releaseAll()

#func: finds mutual folder between both input folders
#inputs:
#	folder_1:
#		first folder
#	folder_2:
#		second folder
#	windows:
#		running on windows or not
# #outputs:
#	joint_folder:
#		mutual parent folder
def mut_fold(folder_1=None,folder_2=None,windows=None):
#	variables
	joint_folder=[]
	if folder_1 == folder_2: #checks that two different folders were given
		print("ERROR: same folder selected for OV and NO" )
		sys.exit("same folder selected for OV and NO" )
	if windows: #finds all the parent directories of the input folders
		match_1=re.findall(".[^\\\\]+",folder_1)
		match_2=re.findall(".[^\\\\]+",folder_2)
	elif not windows:
		match_1=re.findall("\/.[^\/]+",folder_1)
		match_2=re.findall("\/.[^\/]+",folder_2)
#	print(match_1, match_2)
	for Folder in reversed(match_1): #finds that smallest mutual directory
		if Folder in match_2:
			joint_folder.insert(0,Folder)
	joint_folder="".join(joint_folder)
#	print(joint_folder)
	return joint_folder


#func:sorts through files
#inputs:
#	file_list:
#		list of files to be sorted
#	sort_by_digit:
#		specified digit to sort by	
#	rev:
#		places objects in descending order
# #outputs:
#	file_list:
#		list of sorted files/objects
def file_sort(file_list=None,sort_by_digit=0, rev=False):
	for  n, filename in enumerate(file_list):
		for m, filename_2 in enumerate(file_list[n+1:len(file_list)]):
			try:
				match = int(re.findall("(\d+)",str(filename))[sort_by_digit])
				match_2 = int(re.findall("(\d+)",str(filename_2))[sort_by_digit])
			except IndexError:
				print(" ERROR: Currently only works with filenames containing digits")
				sys.exit("Currently only works with filenames containing digits")
#			print(filename,filename_2)
			if not rev:
				if match > match_2:
					temp_1=filename
					temp_2=filename_2
	#				print(filename,filename_2)
					filename=temp_2
					filename_2=temp_1
					file_list[n]=temp_2
					file_list[n+m+1]=temp_1
	#				print(filename,filename_2)
			if rev:
				if n < n+1:
#				if match < match_2:
					temp_1=filename
					temp_2=filename_2
#					print(filename,filename_2)
					filename=temp_2
					filename_2=temp_1
					file_list[n]=temp_2
					file_list[n+m+1]=temp_1
	#				print(filename,filename_2)
	return file_list

#func: makes filepath list
#inputs:
#	loop_fold:
#		parent folder
#	windows:
#		running on windows or not	
#	append_fold:
#		seperate parent folder
#outputs:
#	all_folder_list:
#		list of folders
def folder_find(loop_fold=None,  windows=None, append_fold=None):
#	variables
	all_folder_list=[]
	filenames =  os.listdir(loop_fold)
	for filename in filenames: # creates filepaths for each subdirectory in loop_fold
	#	fix if not mac
		if windows:
			filename = loop_fold+"\\"+filename
		elif not windows:
			filename = loop_fold+"/"+filename
#		print(filename)
		if os.path.isdir(filename):
	#		print("found folder")
			all_folder_list.append(filename)	
	if len(all_folder_list)==0: #if no folders found loop_fold, assumes this is instead the folder to find files
			all_folder_list.append(loop_fold)
	if append_fold:#appends folders for the beginning of list (folders assumed to contain files of interest)
		if type(append_fold) == list:
			all_folder_list=append_fold+all_folder_list
		elif type(append_fold) == unicode:
			all_folder_list=[append_fold]+all_folder_list
		else:
			print(" ERROR: expected list or unicode for append_fold")
			sys.exit("expected list or unicode for append_fold")
	return all_folder_list

	
	
#func: finds files in input directories
#inputs:
#	all_folder_list:
#		list of filepaths
#	pattern_1:
#		specified pattern to look for when finding files
#	pattern_2:
#		specified pattern to look for when finding files
#outputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names	
def file_find(all_folder_list=None, pattern_1=None, pattern_2=None):
#	variables
	filenames_keys=[]
	filenames_values=[]
	for fold in all_folder_list:#finds files in folders
		file_list=filter(pattern_2.match, os.listdir(fold))
		#not sure about this line of code
		if not file_list: #checks second pattern
	 		file_list=filter(pattern_1.match, os.listdir(fold))
	 	filenames_keys.append(fold)
		filenames_values.append(file_sort(file_list))
	for num in range(0,len(filenames_keys)): #checks whether any images were found	
		if not filenames_keys[num] or not filenames_values[num]:
			print("ERROR: no files found, check folder or pattern")
			sys.exit(" no files found, check folder or pattern")
	return filenames_keys, filenames_values

	

#func: finds duplicates and checks for same number of files in folder
#inputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names
def dup_find(filenames_keys=None, filenames_values=None):
	for i, fold in enumerate(filenames_keys):#checks for same number of files in each folder
		if i ==0:
			length = len(filenames_values[i])
		elif i !=0:
			if length != len(filenames_values[i]):
				print("ERROR: not an equal number of files in each folder")
				sys.exit("not an equal number of files in each folder")
		for n,filename in enumerate(filenames_values[i]): #checks for duplicates
			for m,filename_2 in enumerate(filenames_values[i][n+1:len(filenames_values[i])]):
				if filename == filename_2:
					print("ERROR: found duplicate", filename, filename_2, "at position", n+1, m+1, "in folder" )
					sys.exit("found duplicate", filename, filename_2, "at position", n+1, m+1, "in folder" )

#func: makes directory
#inputs:
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
#outputs:
#	new_dir:
#		the new directory filepath
#to fix:
#is a one file saver option needed?
def make_dir(filepath=None, dir_name=None, file_var=None, filename=None, windows=None, savefile=False):
	new_dir=os.path.join(filepath, dir_name) #make new directory
	try: #if error, directory already exists
		os.mkdir(new_dir)
	except OSError:
		pass
	if savefile: #save image as tiff, accounting for if on a windows machine and the amout of files to be saved
		if windows:
			if file_var.getDimensions()[3] != 1:
				plugin.StackWriter.save(file_var, new_dir+"\\", "format=tiff");
			#one file
			elif file_var.getDimensions()[3] == 1:
				IJ.saveAs(file_var, "Tiff", new_dir+"\\"+filename)
		elif not windows:
			if file_var.getDimensions()[3] != 1:
				plugin.StackWriter.save(file_var, new_dir+"/", "format=tiff");
			#one file
			elif file_var.getDimensions()[3] == 1:
				IJ.saveAs(file_var, "Tiff", new_dir+"/"+filename)
	return new_dir

#func: inverts images
#inputs:
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
#outputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names	
def invert_image(filenames_keys=None, filenames_values=None, joint_folder=None, windows=None, pattern=None, file_start=1):
	for n, fold in enumerate(filenames_keys[file_start:]):
		for m, filename in enumerate(filenames_values[file_start:][n]):
			filepath = os.path.join(fold,filename)
			imp=IJ.openImage(filepath);
			IJ.run(imp, "Invert", "");
			sub_dir=make_dir(joint_folder, "_"+str(n), imp, "/"+str(m),windows, True)
#			print(sub_dir)
			NO_file=filter(pattern.match, os.listdir(sub_dir))
			NO_file=file_sort(NO_file)
			filenames_keys[n+file_start] = sub_dir
			filenames_values[n+file_start] = NO_file
	return filenames_keys, filenames_values

#func: adds images to each layer in trakem2
#inputs:
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
#outputs:
#	layerset:
#		all layers in trakem2 project
#fix:
#	merge this and following function
def add_patch(filenames_keys=None, filenames_values=None, project=None, start_lay=None, tot_lay=None): #layerset=None,
	layerset = project.getRootLayerSet()#get the layerset
	for i in range(start_lay,tot_lay):#add to the layerset the desired amount of layers 
		layerset.getLayer(i, 1, True)
	for i ,layer in enumerate(layerset.getLayers()): #add images to each layer
			for n, fold in enumerate(filenames_keys):
				#print(fold)
				#print(filenames_values[n][i-start_lay])
				filepath = os.path.join(fold, filenames_values[n][i-start_lay])
				patch = Patch.createPatch(project, filepath)
				layer.add(patch)
		#		print(patch)
			layer.recreateBuckets() #update layerset?
	return layerset

#func: adds images to each layer in trakem2
#inputs:
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
#outputs:
#	layerset:
#		all layers in trakem2 project
def add_patch_v2(filenames_keys=None, filenames_values=None, project=None, start_lay=None, tot_lay=None): #layerset=None,
	layerset = project.getRootLayerSet()#get the layerset
	for i in range(start_lay,tot_lay):#add to the layerset the desired amount of layers 
		layerset.getLayer(i, 1, True)
	for i ,layer in enumerate(layerset.getLayers()): #add images to each layer
		if i >= start_lay:
			for n, fold in enumerate(filenames_keys):
				#print(fold)
				#print(filenames_values[n][i-start_lay])
				#print(i+start_lay)
				filepath = os.path.join(fold, filenames_values[n][i-start_lay])
				patch = Patch.createPatch(project, filepath)
				layer.add(patch)
		#		print(patch)
			layer.recreateBuckets() #update layerset?
	return layerset

#func: preps images for a test align to see if parameters chosen work with images
#inputs:
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
#outputs:
#	temp_filenames_keys:
#		file paths
#	temp_filenames_values:
#		file names	
def prep_test_align(filenames_keys=None, filenames_values=None,test_folder=None, windows=None, project_name=None,invert_image=False,size=None):
	temp_filenames_keys=[]
	temp_filenames_values=[]
	temp_filenames_keys+=filenames_keys
	temp_filenames_values+=filenames_values
	test_interim=make_dir(test_folder, "substack_"+re.findall("\d+",project_name)[-1]) #makes directory
#	for num in range(1,len(filenames_keys)):#do we need this for NO?
	for num in range(0,len(filenames_keys)): #resizes and inverts images
#		print(filenames_values[num][0])
		path=os.path.join(filenames_keys[num], filenames_values[num][0]) #this (also in invert) could become funciton
		imp=IJ.openImage(path);
		title=imp.getTitle()
		if size:
			if size != 1: #resizes image to smaller rather larger
				old_dim=imp.getDimensions()
				width=int((imp.getDimensions()[0])*(float(1)/float(size)))
				height=int((imp.getDimensions()[1])*(float(1)/float(size)))
				#resize images
				imp = imp.resize(width, height, "none");
	#			print("old height is "+str(old_dim.height), "new height is "+str(imp.getDimensions().height))
		if invert_image: #inverts image
			IJ.run(imp, "Invert", "");
		sub_dir = make_dir(test_interim, "_"+str(num), imp, title, windows, True)#makes directory and saves file
		temp_filenames_keys[num]=sub_dir #reasigns new filepath and image
		temp_filenames_values[num]=[title]
	return temp_filenames_keys, temp_filenames_values

#func: stiches images together
#inputs:
#	model_index:
#		specified aligning metric (ie. translation, rigid, similarity, affine)
#	octave_size:
#		max image size
#	layerset:
#		all the layers in trakem2 project
#	OV_lock:
#		accounts for difference between low res and high res alignments
#outputs:
#	roi:
#		this is the roi per image stack in filenames_key
#	tiles:
#		trakem2 images in layer
#to fix:
#	furture elastic montage parameters:
	#block matching
	#patch scale 0.2
	#search radius 90 pixel
	#block radius default 50
	#correlation filters 
	#minimal PMCC r 0.1
	#maximal curvature ratio 1000 i think 10.00
	#maximual second best 0.90
	#local smoothness filters
	#approximate local transformation affine
	#sigma default 25.00 ?
	#absolute maximal loca ldispalcementL 30
	#relative maximal local displacememt 3
	#select tiles are premontaged
	#spring mesh= default
	#sift based proemontage
	#feature descriptin defautl
def align_layers(model_index=None, octave_size=None, layerset=None, OV_lock=None):
	#variables
	non_move=[]
	roi=None
	roi_list=[]
	#various parameters for alignment
	if OV_lock:
		param = Align.ParamOptimize(desiredModelIndex=model_index,expectedModelIndex=model_index, maxEpsilon=25,minInlierRatio=0.05,minNumInliers=7)  # which extends Align.Param
		param.sift.maxOctaveSize = octave_size
		param.sift.minOctaveSize = octave_size/2
		param.sift.steps = 3
		param.sift.fdBins = 8
		param.sift.fdSize = 4
	if not OV_lock:
		param = Align.ParamOptimize(desiredModelIndex=model_index,expectedModelIndex=model_index)  # which extends Align.Param
		param.sift.maxOctaveSize = octave_size
	for n, layer in enumerate(layerset.getLayers()):
	  	tiles = layer.getDisplayables(Patch) #get all tiles
		layerset.setMinimumDimensions() #readjust canvas size
		if OV_lock:	#here we are linking each image to the previous image of the same stack
			if n == 0:
				old_tiles=tiles
			if n > 0:
				for n, old_tile in enumerate(old_tiles):
					for m, tile in enumerate(tiles):
						if n == m:
							old_tile.link(tile)
							break
					old_tiles=tiles
					#print(tile.isLinked())
		tiles[0].setLocked(True) #lock the OV stack
		non_move.append(tiles[0]) #i believe tihs is what they are looking for
	for n, layer in enumerate(layerset.getLayers()):
		  	tiles = layer.getDisplayables(Patch) #get  all tiles of layer
			AlignTask.alignPatches(
			param,
			tiles,
			[tiles[0]],#non_move,
			False,
			False,
			False,
			False)
			if OV_lock: #could be optimzied here, as repeat,funciton could take in value instead of OV_lock
				# for n, tile in enumerate(tiles[:-2]): #all images in a layer are linked
				# 	for m, tile_2 in enumerate(tiles[n:]):
				# 		tile.link(tile_2)	
				for tile in tiles[0:]: #roi for each stack of images is collected
					roi = tile.getBoundingBox() #needed in OV alignment
					roi_list.append(roi)
				roi=roi_list
			if not OV_lock: #roi for each stack of images is collected
				roi = tiles[1].getBoundingBox() #needed in OV alignment
				for tile in tiles[1:]:
					roi.add(tile.getBoundingBox())
	return roi, tiles

#func: this one is a two parter 
#first correct all negative coordinates to positive ones
#second: find the overlap area(s) and creates another list with all the associated inout roi for each overlap
#inputs:
#	roi:
#		this takes a list of rois 
#outputs:
#	overlap_list:
#		list of overlap roi between each montaged image (ie. trakem2 montaged images )
#	assoc_x_list:
#		list which gives the associated overlap roi which each roi from input
# 		ie. both list have the same order			
#to fix:
#	should use copy_roi=roi[:] to increase efficiency
def overlap_area(ROI=None):
	#variables
	x_list=[]
	y_list=[]
	new_x_list=[]
	new_y_list=[]
	width_list=[]
	height_list=[]
	match_x=0
	match_y=0
	new_roi=[] 
	roi_list=[]
	new_roi_list=[] #made to add crop areas after
	big_dif=False
	overlap_list=[]
	temp_overlap_list=[]
	assoc_x_list=[]
	new_x=""
	#this could be more efficient by just copying roi to copy_roi=roi[:]
	for n, r in  enumerate(ROI): #makes new lists for each parameter of an roi
		x_list.append(r.x)
		y_list.append(r.y)
		width_list.append(r.width)
		height_list.append(r.height)
	# print(x_list,y_list,width_list, height_list)
	for x in x_list: #finds x coordinates that are negative (less than match_x=0)
		if x < match_x:
			match_x = 0 + x
	if match_x: #if a negative value found, converts all x values to positive my adding the largest negative x value to all the other values
		for x in x_list:
			#print("found -", x-match_x)
			new_x=x - match_x
			new_x_list.append(new_x)
	else:
		new_x_list=x_list
	for y in y_list: #the same above is repeated for y coordinates
		if y < match_y:
			match_y = 0 + y
	if match_y:
		for y in y_list:
			new_y= y - match_y
			new_y_list.append(new_y)
	else:
		new_y_list=y_list	
	# for n, x in enumerate(new_x_list): #resorts 
	# 	for x2 in new_x_list[n+1:]: 
	# 		print("here i am")
	# 		print(x,x2)
	# 		if x2 < x:
	# 			print("this is unusual")
	# 			new_x_list=file_sort(new_x_list, -1) #needed
	#with a simple copy of roi the file_sort function could be used
	for  n, x in enumerate(new_x_list):# a sort function, like the file_sort function, that works on x coordinates however also changes y,width,height
		for m, x2 in enumerate(new_x_list[n+1:len(new_x_list)]):
			try: # finds correct order via digit size
				match = int(re.findall("(\d+)",str(x))[0])
				match_2 = int(re.findall("(\d+)",str(x2))[0])
			except IndexError:
				print(" ERROR: Currently only works with filenames containing digits")
				sys.exit("Currently only works with filenames containing digits")
#			print(filename,filename_2)
			if match > match_2:
				temp_1=x
				temp_2=x2
#				print(filename,filename_2)
				x=temp_2
				x2=temp_1
				new_x_list[n]=temp_2
				new_x_list[n+m+1]=temp_1
				y_temp=new_y_list[n]
				new_y_list[n]=new_y_list[n+m+1]
				new_y_list[n+m+1]=y_temp
				width_temp=width_list[n]
				width_list[n]=width_list[n+m+1]
				width_list[n+m+1]=width_temp
				height_temp = height_list[n]
				height_list[n]=height_list[n+m+1]
				height_list[n+m+1]=height_temp
#				print(filename,filename_2)
	for index in range(0,len(new_x_list)): #creates a new roi with all 4 roi parameters
		new_roi.append(new_x_list[index])
		new_roi.append(new_y_list[index])
		new_roi.append(width_list[index])
		new_roi.append(height_list[index])
		roi_list.append(new_roi)
		new_roi=[]
	for i in range(0,len(roi_list)): # makes new roi list, could use simple copying here
		new_roi_list.append(i)
	for n, x in enumerate(new_x_list):
		for roi in roi_list: #reorders roi list?
			if x == roi[0]:
				new_roi_list[n]=roi
	#print(new_roi_list)	
	#nothing in place for y
	for n, y in enumerate(y_list): # this step is in place to state function handles only horizontal alignments for now
		for y2 in y_list[n+1:]:
			if abs(abs(y) - abs(y2)) > 100:
				big_dif=True
	if big_dif:
		gui = GUI.newNonBlockingDialog("Y_axis_overlap?")
		gui.addMessage(" It seems that images may be aligned vertically, as opposed to horizontally. Is this correct?")
		gui.showDialog()
		if gui.wasOKed():
			print("ERROR: Currently does not handle vertical overlap")
			sys.exit("Currently does not handle vertical overlap")		
		elif not gui.wasOKed():
			pass				
#	print(new_x_list,new_y_list,width_list, height_list)
	for n, x in enumerate(new_roi_list): #section which images overlap to create overlap rois
		for x2 in new_roi_list[n+1:]:
			#print(x,x2)
			if x[0]+x[2] > x2[0]:
				new_x = [] + x
				new_x[0] = x2[0] -x[0]# both the new_x parameters have to been minus x[0] because if you have more than 2 images the x values will be with regards to the trakem2 postion and when cropping the parameters will be out of bounds when looking at a single image
#				new_x[2]=x[2]-x[0]
				new_x[2]=x[2]-(x2[0]-x[0]) #creates the overlap area length
				#print(new_x)
				temp_overlap_list.append(new_x)
		if len(temp_overlap_list) > 1: #only accomodates one overlap
			print("ERROR: 3 of your images are overlapping, currently cannot accomodate")
			sys.exit("3 of your images are overlapping, currently cannot accomodate")	
		elif  len(temp_overlap_list) == 1:	#the overlap roi list is made
			overlap_list.append(temp_overlap_list[0])
			for m, link in enumerate(x_list): #finds the associated roi to the new overlap roi
				#print(link-match_x, x[0])
				if link-match_x == x[0]: #this retrieves the old roi value
					#print(link-match_x, x[0])
					assoc_x_list.append([link,y_list[m],width_list[m],height_list[m]])
			temp_overlap_list=[]
		if not overlap_list:
			print("ERROR: expecting overlap")
			sys.exit("expecting overlap")	
	#print(overlap_list, assoc_x_list)	
	return overlap_list, assoc_x_list

#func: resizes image
#inputs:
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
#outputs:
#	filenames_keys:
#		file paths
#	filenames_values:
#		file names	
def resize_image(filenames_keys=None, filenames_values=None, joint_folder=None, windows=None, project_name=None, pattern=None, size=None, roi=None): #layerset=None, project=None
	imp = plugin.FolderOpener.open(filenames_keys[0], "virtual"); #open image stack
	title=imp.getTitle() #get image stack name
	ROI=imp.setRoi(roi.x-10,roi.y-10,roi.width+10,roi.height+10); #get roi values, with 10px of wiggle room
	#print(imp.getDimensions())
	imp=imp.crop("stack") #crop image to new roi
	old_dim=imp.getDimensions()
	width=imp.getDimensions()[0]*size #change image dimensions by specified factor
	height=imp.getDimensions()[1]*size
	#resize images
	imp = imp.resize(width, height, "none"); #resize image to changed image dimensions
	Title=imp.setTitle("") #create new image stack name
	output_scaled=make_dir(joint_folder, "_",imp, title, windows, True) #save to specified directory
	OV_file=filter(pattern.match, os.listdir(output_scaled)) #find new saved files
	OV_file=file_sort(OV_file) #sort in ascending order
	filenames_keys[0] = output_scaled #save new filepath and images to filenames_keys and filenames_values
	filenames_values[0] = OV_file
	return filenames_keys, filenames_values

#func: this one is a two parter 
#first cropping the images(all images but the rightmost one)
	#this part requires that the crop area be specified drawing from outputs of the overlap_area function
#second: then moving the rightmost folder from the inv to crop folder, this will faciliate if the script half way through
	#and so you can rerun immediately from the crop folder, no need to move them around
#inputs:
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
#	roi:
	#	this is the roi  per image stack in filenames_key
#	crop_roi:
	#	this is the area to be cropped from all images but rightmost
#	assoc_roi:
#		this gives you the associated crop roi for each roi	
#outputs:
#	filenames_keys:
	#
#	filenames_values:
	#				
def remove_area(filenames_keys=None, filenames_values=None, joint_folder=None, windows=None, project_name=None, pattern=None, roi=None, crop_roi=None, assoc_roi=None): #layerset=None, project=None
	#variables
	filenames_keys_copy = filenames_keys[:] #items in this list will be removed with each crop so that the right most image can be found
	numbered = list(range(0,len(roi))) # basically in place for when the overlay and directories aren't same order so that these two things can be properly associated when making the right most image folder in crop folder
	#print(filenames_keys, numbered)
	for m, r in enumerate(roi):#for loop to find each roi and its associated crop_roi via assoc_roi
		for n, assoc_r in enumerate(assoc_roi):
			#print(r,assoc_r)
			#assuming there is no two images at the same x coordinate, which there shouldn't
			if r.x == assoc_r[0]:
				#print(r,assoc_r)
				imp = plugin.FolderOpener.open(filenames_keys[m], "virtual");
				title=imp.getTitle()
				# cropper=int(-float(0.4)*float(crop_roi[n][0]+crop_roi[n][2])+float(crop_roi[n][0])) # adjusting the coordinates of the overlap area to the crop area (currently 0.4 of the overlay area to remain)
				cropper=int(float(0.4)*float(crop_roi[n][2])) # adjusting the coordinates of the overlap area to the crop area (currently 0.4 of the overlay area to remain)
				#print("cropper",cropper)
				#print(imp.getDimensions())
				#print(0,0,crop_roi[n][2]+crop_roi[n][0]-crop_roi[n][2]+cropper,crop_roi[n][3])
				ROI=imp.setRoi(0,0,crop_roi[n][2]+crop_roi[n][0]-crop_roi[n][2]+cropper,crop_roi[n][3]); #set up crop roi
#				ROI=imp.setRoi(0,0,crop_roi[n][2]+crop_roi[n][0]-crop_roi[n][2]+100,crop_roi[n][3]);
				imp=imp.crop("stack") #crop
				#this way name does not change between folders, if the order of the folders is not the order of the overlay
				output_scaled=make_dir(joint_folder, "_"+str(m),imp, title, windows, True) # make sub output directory
				OV_file=filter(pattern.match, os.listdir(output_scaled)) # find the new cropped images in the new output directory
				OV_file=file_sort(OV_file) #sort so that they are in numerical order
				#print(filenames_keys[m])
				filenames_keys_copy.remove(filenames_keys[m]) #remove the cropped folder from the copy folder
				numbered.remove(m) #remove the cropped folder number from the copy folder
				#print(numbered)
				filenames_keys[m] = output_scaled #update filenames_keys
				filenames_values[m] = OV_file #update filename_values
			#have to make a complimentary function, where when all roi are found remove, the none found one gets added to the crop directory
	#inverted_subs=folder_find(output_inverted,windows)
	#print(filenames_keys_copy)
	match = int(re.findall("(\d+)",str(filenames_keys_copy))[-1])#finds right most image
	#print(inverted_subs)
	#print(match)
	if windows:
		incrop=joint_folder+"/_"+str(match) #creates new name and filepath for right most image
		try: #if this image folder already exists will ask to overwrite it
			dest = shutil.move(filenames_keys_copy[0], joint_folder) 
		except shutil.Error:
			gui = GUI.newNonBlockingDialog("Overwrite?")
			gui.addMessage(" Press ok to overwrite crop substack folder?")
			gui.showDialog()
			if gui.wasOKed():
				match_1=re.findall(".[^\\\\]+",filenames_keys_copy[0])[-1]
				shutil.rmtree(joint_folder+match_1)
				dest = shutil.move(filenames_keys_copy[0], joint_folder)
			elif not gui.wasOKed():
				sys.exit()
		#print(filenames_keys)
		#print(numbered,"here")
		filenames_keys[numbered[0]]=incrop
		#print(incrop)
		#print(filenames_keys)
	elif not windows: #same as above but for not window machines
		incrop=joint_folder+"/_"+str(match)
		#print(incrop)
		#print(inverted_subs[-1])
		try:
			dest = shutil.move(filenames_keys_copy[0], joint_folder)
		except shutil.Error:
			gui = GUI.newNonBlockingDialog("Overwrite?")
			gui.addMessage(" Press ok to overwrite crop substack folder?")
			gui.showDialog()
			if gui.wasOKed():
				match_1=re.findall("\/.[^\/]+",filenames_keys_copy[0])[-1]
				shutil.rmtree(joint_folder+match_1)
				dest = shutil.move(filenames_keys_copy[0], joint_folder)
			elif not gui.wasOKed():
				sys.exit()
		print(filenames_keys)
		print(numbered,"here")
		filenames_keys[numbered[0]]=incrop
		#print(incrop)
		#print(filenames_keys)
	return filenames_keys, filenames_values	

#func: removes trakem2 tiles
# #inputs:
#	tiles:
#		trakem2 tiles from a layer
def remove_tiles(tiles=None):
	for tile in tiles:
		tile.remove(False)

#func: removes the OV tile
# #inputs:
#	layerset:
#		the trakem2 layers
#	image_rem_num:
#		tile number to remove
def remove_OV(layerset=None,image_rem_num=None):
	for i, layer in enumerate(layerset.getLayers()):
		tiles = layer.getDisplayables(Patch)
		tiles[image_rem_num].remove(False)

#func: exports images
#inputs:
#	layerset:
#		the trakem2 layers
#	output_dir:
#		directory to save files
#	canvas_roi:
#		precision on whether to save whole canvas or just images roi
#	processed:
#		whether to denoise and contrast images	
def export_image(layerset=None, output_dir=None, canvas_roi=False, processed=False):#, blocksize=None, histogram_bins=None,maximum_slope=None):
	#export variables
	export_type=0 #GRAY8
	backgroundColor = Color(0,0,0,0)
	scale = 1.0
	#additional processing variables (gaussian blur, CLAHE )
	sigmaPixels=0.7
	blocksize = 300
	histogram_bins = 256
	maximum_slope = 1.5
	mask = "*None*"
	fast = True
	process_as_composite = False
	composite = False
	mask = None
	for i, layer in enumerate(layerset.getLayers()): #loop through each layer
		#  print(layer)
		tiles = layer.getDisplayables(Patch)
		#  print(tiles)
		if canvas_roi:#save image with whole canvas
			roi=layerset.get2DBounds() 
		elif not canvas_roi:# save image without whole canvas
			roi = tiles[0].getBoundingBox() 
			for tile in tiles[1:]:
				roi.add(tile.getBoundingBox())
		ip = Patch.makeFlatImage( #image paramaters
		       export_type,
		       layer,
		       roi,
		       scale,
		       tiles, 
		       backgroundColor,
		       True)  # use the min and max of each tile
		imp = ImagePlus("Flat montage", ip) #creates image
		if processed: #processes image if desired
			imp.getProcessor().blurGaussian(sigmaPixels)
#			pretty sure 3 refers to median_filter
#			https://imagej.nih.gov/ij/developer/api/ij/ij/process/ImageProcessor.html#filter(int)
#			imp.getProcessor().filter(3)
			FastFlat.getFastInstance().run( imp, 
			                    blocksize,
			                    histogram_bins,
			                    maximum_slope,
			                    mask,
			                    composite)
		FileSaver(imp).saveAsTiff(output_dir + "/" + str(i + 1) + ".tif") #saves file to output directory