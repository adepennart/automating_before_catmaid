"""
Title: functions.py

Date: January 12th, 2023

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
    11. deactivate mipmaps
  
    
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

# func: flushing image cache
def releaseAll():
	Project.getProjects()[0].getLoader().releaseAll()

#func: finds mutual folder between both input folders
def mut_fold(folder_1=None,folder_2=None,is_windows=None):
#	variables
	joint_folder=[]
	if folder_1 == folder_2:
		print("ERROR: same folder selected for OV and NO" )
		sys.exit("same folder selected for OV and NO" )
	#finds all the parent directories of the input folders
	if is_windows:
		match_1=re.findall(".[^\\\\]+",folder_1)
		match_2=re.findall(".[^\\\\]+",folder_2)
	elif not is_windows:
		match_1=re.findall("\/.[^\/]+",folder_1)
		match_2=re.findall("\/.[^\/]+",folder_2)
#	print(match_1, match_2)
	for Folder in reversed(match_1):
		if Folder in match_2:
			joint_folder.insert(0,Folder)
	joint_folder="".join(joint_folder)
#	print(joint_folder)
	return joint_folder


#func:sort_
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

#make folder list including all folders found in loop_folder
def folder_find(loop_fold=None,  is_windows=None, append_fold=None):
#	variables
	all_folder_list=[]
	filenames =  os.listdir(loop_fold)
	for filename in filenames:
	#	fix if not mac
		if is_windows:
			filename = loop_fold+"\\"+filename
		elif not is_windows:
			filename = loop_fold+"/"+filename
#		print(filename)
		if os.path.isdir(filename):
	#		print("found folder")
			all_folder_list.append(filename)	
	if len(all_folder_list)==0: #if no folders found assumes, this is instead the folder to find files
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

	
	
#func: find files in input directories
def file_find(all_folder_list=None, pattern_1=None, pattern_2=None):
#	variables
	filenames_keys=[]
	filenames_values=[]
	for fold in all_folder_list:
		file_list=filter(pattern_2.match, os.listdir(fold))
		#not sure about this line of code
		if not file_list:
	 		file_list=filter(pattern_1.match, os.listdir(fold))
	 	filenames_keys.append(fold)
		filenames_values.append(file_sort(file_list))
	for num in range(0,len(filenames_keys)):	
		if not filenames_keys[num] or not filenames_values[num]:
			print("ERROR: no files found, check folder or pattern")
			sys.exit(" no files found, check folder or pattern")
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
def invert_image(filenames_keys=None, filenames_values=None, joint_folder=None, windows=None, pattern_3=None, file_start=1):
	for n, fold in enumerate(filenames_keys[file_start:]):
		for m, filename in enumerate(filenames_values[file_start:][n]):
			filepath = os.path.join(fold,filename)
			imp=IJ.openImage(filepath);
			IJ.run(imp, "Invert", "");
			sub_dir=make_dir(joint_folder, "_"+str(n), imp, "/"+str(m),windows, True)
#			print(sub_dir)
			NO_file=filter(pattern_3.match, os.listdir(sub_dir))
			NO_file=file_sort(NO_file)
			filenames_keys[n+file_start] = sub_dir
			filenames_values[n+file_start] = NO_file
	return filenames_keys, filenames_values

def add_patch(filenames_keys=None, filenames_values=None, project=None, start_lay=None, tot_lay=None): #layerset=None,
	layerset = project.getRootLayerSet()
	for i in range(start_lay,tot_lay):
		layerset.getLayer(i, 1, True)
	for i,layer in enumerate(layerset.getLayers()):
			for n, fold in enumerate(filenames_keys):
				print(fold)
				print(filenames_values[n][i])
				filepath = os.path.join(fold, filenames_values[n][i])
				patch = Patch.createPatch(project, filepath)
				layer.add(patch)
		#		print(patch)
			layer.recreateBuckets()
	return layerset

def add_patch_v2(filenames_keys=None, filenames_values=None, project=None, start_lay=None, tot_lay=None): #layerset=None,
	layerset = project.getRootLayerSet()
	for i in range(start_lay,tot_lay):
		layerset.getLayer(i, 1, True)
	for i ,layer in enumerate(layerset.getLayers()):
		if i >= start_lay:
			for n, fold in enumerate(filenames_keys):
				#print(fold)
				#print(filenames_values[n][i-start_lay])
				#print(i+start_lay)
				filepath = os.path.join(fold, filenames_values[n][i-start_lay])
				patch = Patch.createPatch(project, filepath)
				layer.add(patch)
		#		print(patch)
			layer.recreateBuckets()
	return layerset

def align_layers(model_index=None, octave_size=None, layerset=None, OV_lock=None):
	non_move=[]
	roi=None
	roi_list=[]
	tile_list=[]
#	param = Align.ParamOptimize(desiredModelIndex=model_index,expectedModelIndex=model_index, maxEpsilon=25,minInlierRatio=0.05,minNumInliers=7)  # which extends Align.Param
	param = Align.ParamOptimize(desiredModelIndex=model_index,expectedModelIndex=model_index, maxEpsilon=25,minInlierRatio=0.05,minNumInliers=7)  # which extends Align.Param
	param.sift.maxOctaveSize = octave_size
	param.sift.minOctaveSize = octave_size/2
	param.sift.steps = 3
	param.sift.fdBins = 8
	param.sift.fdSize = 4
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
	
	for n, layer in enumerate(layerset.getLayers()):
	  	tiles = layer.getDisplayables(Patch) #get list of tiles
		tile_list.append(tiles[0])
		layerset.setMinimumDimensions() #readjust canvas size
		if not OV_lock:	
			if n == 0:
				old_tiles=tiles
			if n > 0:
#				old_tiles[1].link(tiles[1])
				for n, old_tile in enumerate(old_tiles):
					for m, tile in enumerate(tiles):
#				for num in range(0,len(tiles)):
#					print(num)
#					old_tiles[num].link(tiles[num])
						if n == m:
							old_tile.link(tile)
							break
					old_tiles=tiles
					#print(tile.isLinked())
			tiles[0].setLocked(True) #lock the OV stack
			non_move.append(tiles[0]) #i believe tihs is what they are looking for
#		AlignTask.montageLayers(
#		param,
#		layerset.getLayers(),
#		False , 
#		False, 
#		False, 
#		False)	
		#montage or align?
	for n, layer in enumerate(layerset.getLayers()):
#		if n ==0:
	# 		layer=Layerset.getLayer(0)
		  	tiles = layer.getDisplayables(Patch) #get list of tiles
	#	  	if not OV_lock:	
	#	  		non_move = [tiles[0]] #i believe tihs is what they are looking for
	#		Align.connectTilePairs(param, 
	#		tiles, 
	#		tiles,
	#		1)
#			tiles = layer.getDisplayables(Patch) #get list of tiles
#			for tile in tiles[1:]:
#				roi = tile.getBoundingBox() #needed in OV alignment
#				roi_list.append(r)
			#check
			AlignTask.alignPatches(
			param,
			tiles,
			[tiles[0]],#non_move,
			False,
			False,
			False,
			False)
#			tiles = layer.getDisplayables(Patch) #get list of tiles
#			for tile in tiles[1:]:
#				new_roi = tile.getBoundingBox() #needed in OV alignment
##				new_roi_list.append(r)
#			x_dif = new_roi.x-roi.x	
#			y_dif =  new_roi.y-roi.y
			#from ini.trakem2.display import Displayable
	#		tiles.getBoundingBox()
	#		tile 1 needs to be changed to incorprate al
			#check if better linked
	#	AlignTask.alignPatches(param,tile_list, None, False, False,False,False) 
	#	for layer in layerset.getLayers():
			if OV_lock: #could be optimzied here, as repeat,funciton could take in value instead of OV_lock
				#will become list
#				tiles[1].unlink()
#				for num in range(0,len(tiles)):
#					tiles[num].unlink()
#				tiles[0].link(tiles[1])
#				for num in range(1,len(tiles)):
#					tiles[0].link(tiles[num])
				for n, tile in enumerate(tiles[:-2]):
					for m, tile_2 in enumerate(tiles[n:]):
						tile.link(tile_2)	
				for tile in tiles[0:]:
					roi = tile.getBoundingBox() #needed in OV alignment
					roi_list.append(roi)
				roi=roi_list
			if not OV_lock: 
				roi = tiles[1].getBoundingBox() #needed in OV alignment
				for tile in tiles[1:]:
					roi.add(tile.getBoundingBox())
#		else:
#			print(x_dif,y_dif)
#			tiles=layer.getDisplayables(Patch)
#			for tile in tiles[1:]:
#				tile.translate(x_dif,y_dif)
##		AlignTask.montageLayers(
#		param,
#		layerset.getLayers(),
#		False , 
#		False, 
#		False, 
#		False)	
	return roi, tiles

#def find_crop_area(filenames_keys=None, filenames_values=None, project=None, test_folder=None, proj_folder=None, windows=None, project_name=None, model_index=None, octave_size=None, invert_image=False,size=None): #layerset=None, pattern_3=None
def prep_test_align(filenames_keys=None, filenames_values=None,test_folder=None, windows=None, project_name=None,invert_image=False,size=None):
	temp_filenames_keys=[]
	temp_filenames_values=[]
	temp_filenames_keys+=filenames_keys
	temp_filenames_values+=filenames_values
	test_interim=make_dir(test_folder, "substack_"+re.findall("\d+",project_name)[-1])
#	for num in range(1,len(filenames_keys)):#do we need this for NO?
	for num in range(0,len(filenames_keys)):
#		print(filenames_values[num][0])
		path=os.path.join(filenames_keys[num], filenames_values[num][0]) #this (also in invert) could become funciton
		imp=IJ.openImage(path);
		title=imp.getTitle()
		if size:
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
		temp_filenames_keys[num]=sub_dir
		temp_filenames_values[num]=[title]
	return temp_filenames_keys, temp_filenames_values

def overlap_area(ROI=None):
	#file_sort(ROI)
	x_list=[]
	y_list=[]
	new_x_list=[]
	new_y_list=[]
	width_list=[]
	height_list=[]
	match_x=0
	match_y=0
	for n, r in  enumerate(ROI):
		x_list.append(r.x)
		y_list.append(r.y)
		width_list.append(r.width)
		height_list.append(r.height)
	print(x_list,y_list,width_list, height_list)
	for x in x_list:
		if x < match_x:
			match_x = 0 + x
	if match_x:
		for x in x_list:
			print("found -", x-match_x)
			new_x=x - match_x
			new_x_list.append(new_x)
	else:
		new_x_list=x_list
	for y in y_list:
		if y < match_y:
			match_y = 0 + y
	if match_y:
		for y in y_list:
			new_y= y - match_y
			new_y_list.append(new_y)
	else:
		new_y_list=y_list	
	for n, x in enumerate(new_x_list):
		for x2 in new_x_list[n+1:]: 
			print("here i am")
			print(x,x2)
			if x2 < x:
				print("this is unusual")
				new_x_list=file_sort(new_x_list, -1) #needed
	#basically have the file_sort functuin here
	for  n, x in enumerate(new_x_list):
		for m, x2 in enumerate(new_x_list[n+1:len(new_x_list)]):
			try:
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
	
	new_roi=[]
	roi_list=[]
	for index in range(0,len(new_x_list)):
		new_roi.append(new_x_list[index])
		new_roi.append(new_y_list[index])
		new_roi.append(width_list[index])
		new_roi.append(height_list[index])
		roi_list.append(new_roi)
		new_roi=[]
	#new_roi_list is made to add crop areas after
	new_roi_list=[]
	for i in range(0,len(roi_list)):
		new_roi_list.append(i)
	for n, x in enumerate(new_x_list):
		for roi in roi_list:
			if x == roi[0]:
				new_roi_list[n]=roi
	#print(new_roi_list)	
	#nothing in place for y
	#y_list=file_sort(new_y_list)
#	print(x_list,y_list,width_list, height_list)
	big_dif=False
	for n, y in enumerate(y_list):
		for y2 in y_list[n+1:]:
			if abs(abs(y) - abs(y)) > 15:
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
	overlap_list=[]
	temp_overlap_list=[]
	assoc_x_list=[]
	new_x=""
	for n, x in enumerate(new_roi_list):
		for x2 in new_roi_list[n+1:]:
			#print(x,x2)
			if x[0]+x[2] > x2[0]:
				new_x = [] + x
				new_x[0] = x2[0] -x[0]
#				new_x[2]=x[2]-x[0]
				new_x[2]=x[2]-(x2[0]-x[0])
				#print(new_x)
				temp_overlap_list.append(new_x)
		if len(temp_overlap_list) > 1:
			print("ERROR: 3 of your images are overlapping, currently cannot accomodate")
			sys.exit("3 of your images are overlapping, currently cannot accomodate")	
		elif  len(temp_overlap_list) == 1:
			#this is to make the crop area
			overlap_list.append(temp_overlap_list[0])
			#assuming image to left
#			assoc_x_list.append(x)
			for m, link in enumerate(x_list):
				#print(link-match_x, x[0])
				if link-match_x == x[0]:
					#print(link-match_x, x[0])
					assoc_x_list.append([link,y_list[m],width_list[m],height_list[m]])
			temp_overlap_list=[]
		if not overlap_list:
			print("ERROR: expecting overlap")
			sys.exit("expecting overlap")	
	#print("this is here")	
	#print(overlap_list, assoc_x_list)	
	return overlap_list, assoc_x_list

def remove_tiles(tiles=None):
	for tile in tiles:
		tile.remove(False)

#roi
def resize_image(filenames_keys=None, filenames_values=None, joint_folder=None, windows=None, project_name=None, pattern_3=None, size=None, roi=None): #layerset=None, project=None
	imp = plugin.FolderOpener.open(filenames_keys[0], "virtual");
	title=imp.getTitle()
	ROI=imp.setRoi(roi.x-10,roi.y-10,roi.width+10,roi.height+10);
	#print(imp.getDimensions())
	imp=imp.crop("stack")
	old_dim=imp.getDimensions()
	width=imp.getDimensions()[0]*size
	height=imp.getDimensions()[1]*size
	#resize images
	imp = imp.resize(width, height, "none");
	#print(old_dim, imp.getDimensions())
	#multiple files
	#mac or windows
	Title=imp.setTitle("")
	output_scaled=make_dir(joint_folder, "_",imp, title, windows, True)
	OV_file=filter(pattern_3.match, os.listdir(output_scaled))
	OV_file=file_sort(OV_file)
	filenames_keys[0] = output_scaled
	filenames_values[0] = OV_file
	return filenames_keys, filenames_values
	
def remove_area(filenames_keys=None, filenames_values=None, joint_folder=None, windows=None, project_name=None, pattern_3=None, roi=None, crop_roi=None, assoc_roi=None): #layerset=None, project=None
	roi_copy = roi[:]
	filenames_keys_copy = filenames_keys[:]
	numbered = list(range(0,len(roi)))
	print(filenames_keys,roi_copy, numbered)
	for m, r in enumerate(roi):
		for n, assoc_r in enumerate(assoc_roi):
			#print(r,assoc_r)
			#assuming there is no two images at the same x coordinate, which there shouldn't
			if r.x == assoc_r[0]:
				print(r,assoc_r)
				imp = plugin.FolderOpener.open(filenames_keys[m], "virtual");
				title=imp.getTitle()
				cropper=int(-float(0.4)*float(crop_roi[n][0]+crop_roi[n][2])+float(crop_roi[n][0]))
				#print("cropper",cropper)
				#print(imp.getDimensions())
				#print(0,0,crop_roi[n][2]+crop_roi[n][0]-crop_roi[n][2]+cropper,crop_roi[n][3])
				ROI=imp.setRoi(0,0,crop_roi[n][2]+crop_roi[n][0]-crop_roi[n][2]+cropper,crop_roi[n][3]);
#				ROI=imp.setRoi(0,0,crop_roi[n][2]+crop_roi[n][0]-crop_roi[n][2]+100,crop_roi[n][3]);
				imp=imp.crop("stack")
				#this way name does not change between folders, if the order of the folders is not the order of the overlay
				output_scaled=make_dir(joint_folder, "_"+str(m),imp, title, windows, True)
				OV_file=filter(pattern_3.match, os.listdir(output_scaled))
				OV_file=file_sort(OV_file)
				roi_copy.remove(r)
				#print(filenames_keys[m])
				filenames_keys_copy.remove(filenames_keys[m])
				numbered.remove(m)
				print(numbered)
				filenames_keys[m] = output_scaled
				filenames_values[m] = OV_file
			#have to make a complimentary function, where when all roi are found remove, the none found one gets added to the crop directory
	#should be made into funciton
	
	#inverted_subs=folder_find(output_inverted,windows)
	print(filenames_keys_copy)
	match = int(re.findall("(\d+)",str(filenames_keys_copy))[-1])
#	match=len(filenames_keys)
	#print(inverted_subs)
	#print(match)
	if windows:
		incrop=joint_folder+"/_"+str(match)
		try:
			dest = shutil.move(filenames_keys_copy[0], joint_folder)
		except shutil.Error:
			pass
		#print(filenames_keys)
		#print(numbered,"here")
		filenames_keys[numbered[0]]=incrop
		#print(incrop)
		#print(filenames_keys)
	elif not windows:
		incrop=joint_folder+"/_"+str(match)
#		incrop=output_scaled+"/_"+str(match)
		#print(incrop)
		#print(inverted_subs[-1])
		try:
			dest = shutil.move(filenames_keys_copy[0], joint_folder)
#			dest = shutil.move(inverted_subs[-1], output_scaled)
		#if this folder already exists, should ask for overwrite
		except shutil.Error:
			pass
			#os.rename(inverted_subs[-1], output_scaled)
		print(filenames_keys)
		print(numbered,"here")
		filenames_keys[numbered[0]]=incrop
		#print(incrop)
		#print(filenames_keys)
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
			                    mask,
			                    composite)
		FileSaver(imp).saveAsTiff(output_dir + "/" + str(i + 1) + ".tif") #saves file to output directory