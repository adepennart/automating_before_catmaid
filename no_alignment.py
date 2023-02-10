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

#@ File (label = "OV directory", style = "directory") folder
#@ File (label = "NO directory or parent directory only containing NO directories", style = "directory") folder_2
##@ File (label = "OV interim directory", style = "directory") output_scaled
#this needs to be silent
##@ File (label = "test interim directory", style = "directory",required=False) test_interim
##@ File (label = "NO interim directory", style = "directory",required=False) output_inverted
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ boolean (label = "Invert images") inverted_image
#@ int (label = "rescale OV factor", default=4, min=0, max=10 ) size
#@ int (label = "octave_size", default=800, min=0, max=1500 ) octave_size
#@ String(choices={"translation", "rigid", "similarity", "affine"}, style="list") model_index
#@ boolean (label = "using a windows machine") windows




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
#could be useful for threads
from java.lang import Runtime
from java.util.concurrent import Executors


# variables
# --------------------------------------------------------------------------------------
joint_folder=[]
#pattern_1 = re.compile(".*_z[\d]_.*\.tif")
pattern_1 = re.compile("([\d]+).*\.tif")
#pattern_2 = re.compile(".*_z[\d]_.*\.tif")
pattern_2 = re.compile(".*-([\d]{3})-([\d]+)_.*\.tif")
pattern_3 = re.compile(".*[\d]*.tif")
pattern_v2_p1 = (".*_z")
pattern_v2_p2 = ("_.*\.tif")
z_axis_start=0 #z axis number in filename
NO_folder_list=[]
filenames_keys=[]
filenames_values=[]
filenames_NO=[]

#additional processing variables (gaussian blur, CLAHE )
sigmaPixels=2
blocksize = 50
histogram_bins = 128
maximum_slope = 3
mask = "*None*"
fast = True
process_as_composite = False
composite = False
mask = None
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

#func: get string of folder paths
folder = folder.getAbsolutePath()
folder_2 = folder_2.getAbsolutePath()
#output_scaled = output_scaled.getAbsolutePath()
#output_inverted = output_inverted.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()

#print(folder)
#print(folder_2)
#print(output_scaled)
#print(output_inverted)
#print(output_dir)


#func: finds mutual folder between both input folders
#finds all the parent directories of the input folders
if windows:
	match_1=re.findall(".[^\\\\]+",folder)
	match_2=re.findall(".[^\\\\]+",folder_2)
elif not windows:
	match_1=re.findall("\/.[^\/]+",folder)
	match_2=re.findall("\/.[^\/]+",folder_2)
#print(match_1)
#print(match_2)

#check for the same folder and if dfferent folder finds mutual parent folders
if match_1[len(match_1)-1] == match_2[len(match_2)-1]:
	print("ERROR: same folder selected for OV and NO" )
	sys.exit("same folder selected for OV and NO" )
elif match_1[len(match_1)-1] != match_2[len(match_2)-1]:
	for Folder in reversed(match_1):
		if Folder in match_2:
			joint_folder.insert(0,Folder)
joint_folder="".join(joint_folder)
print(joint_folder)

#func: find files in input directories
NO_folder_list.append(folder)
filenames_2 =  os.listdir(folder_2)
print(filenames_2)
for filename in filenames_2:
#	fix if not mac
	if windows:
		filename = folder_2+"\\"+filename
	elif not windows:
		filename = folder_2+"/"+filename
#	print(filename)
	if os.path.isdir(filename):
#		print("found folder")
		NO_folder_list.append(filename)
if  len(NO_folder_list)==1:
	NO_folder_list.append(folder_2)

#NO_folde_list bad name as ov too								
print(NO_folder_list)
for i in NO_folder_list:
	NO_file=filter(pattern_2.match, os.listdir(i))
	if not NO_file:
 		NO_file=filter(pattern_1.match, os.listdir(i))
# 	print(NO_file)
	for  n, filename in enumerate(NO_file):
		for m, filename_2 in enumerate(NO_file[n+1:len(NO_file)]):
			match = int(re.findall("(\d+)",filename)[0])
			match_2 = int(re.findall("(\d+)",filename_2)[0])
#			print(filename,filename_2)
			if match > match_2:
				temp_1=filename
				temp_2=filename_2
#				print(filename,filename_2)
				filename=temp_2
				filename_2=temp_1
				NO_file[n]=temp_2
				NO_file[n+m+1]=temp_1
#				print(filename,filename_2)
	filenames_keys.append(i)
	filenames_values.append(NO_file)
print(filenames_keys,filenames_values)

	
	
#func: find duplicates in NO folder, should look in all foldesr
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

#func: checks for same amount of images in both input folders
#if len(filenames) == len(filenames_2):
#	filenames_3=filenames+filenames_2
#else:
#	print("ERROR: not an equal number of files in each folder")
#	sys.exit("not an equal number of files in each folder")
#	#need to kill code here so that they can delete duplicate
#print(filenames_3)

#Creates a TrakEM2 project
project = Project.newFSProject("blank", None, joint_folder)
#got to figure out if it is a new project or not
# OR: get the first open project
# project = Project.getProjects().get(0)

#work in progress
#threading for image crop, invert, scale
exe = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors())
#print(exe)

#print(project.adjustProperties()[0])
#print(project.getProperty(("Number_of_threads_for_mipmaps")))
#print(project.getProperty(("Autosave_every")))
#print(project.setProperty("Number_of_threads_for_mipmaps", "2"))

#adjust properties window
project.adjustProperties()

#print(project)
#creates initial collection of layers variable
layerset = project.getRootLayerSet()

##func:  inverse
#imp = plugin.FolderOpener.open(folder_2, "virtual");
##imp.show()
#print(imp)
#title=imp.getTitle()
#imp=imp.getProcessor().invert()
#print(imp)
##IJ.run("Invert", "");
##IJ.run("Virtual Stack...", "output="+output_inverted+" text1=run(\"Invert\");\n");
##elif not windows:
##if imp.getDimensions()[3] != 1:
##plugin.StackWriter.save(imp, output_inverted+"/", "format=tiff");
#IJ.saveAs(imp, "Tiff", output_inverted+"/"+title);

#func: invert
if inverted_image:
	output_inverted=os.path.join(joint_folder, "NO_interim")
	try:
		os.mkdir(output_inverted)
	except OSError:
		pass
	for n, namefile in enumerate(filter(pattern_2.match,filenames_2)):
#		print(n)
		filepath = os.path.join(folder_2,namefile)
		imp=IJ.openImage(filepath);
		IJ.run(imp, "Invert", "");
	#	imp=imp.getProcessor().invert()
		IJ.saveAs(imp, "Tiff", output_inverted+"/"+str(n));
		for i, fold in enumerate(filenames_keys):
			if fold == folder_2:
				#check
				NO_file=filter(pattern_3.match, os.listdir(output_inverted))
				for  n, filename in enumerate(NO_file):
					for m, filename_2 in enumerate(NO_file[n+1:len(NO_file)]):
						match = int(re.findall("(\d+)",filename)[0])
						match_2 = int(re.findall("(\d+)",filename_2)[0])
			#			print(filename,filename_2)
						if match > match_2:
							temp_1=filename
							temp_2=filename_2
			#				print(filename,filename_2)
							filename=temp_2
							filename_2=temp_1
							NO_file[n]=temp_2
							NO_file[n+m+1]=temp_1
			#				print(filename,filename_2)
				filenames_keys[i] = output_inverted
				filenames_values[i] = NO_file	

#func: rescaling 
#open OV image stack
#temporary fix
if size != 1:
#if size == 1:
	test_interim=os.path.join(joint_folder, "test_trakem2")
	try:
		os.mkdir(test_interim)
	except OSError:
		pass
	for num in range(1,len(filenames_keys)):
		path=os.path.join(filenames_keys[num], filenames_values[num][0])
		imp=IJ.openImage(path);
		title=imp.getTitle()
		print(imp.getDimensions())
#		width=int(imp.getDimensions()[0]*(1/size))
		width=int((imp.getDimensions()[0])*(float(1)/float(size)))
#		height=int(imp.getDimensions()[1]*(1/size))
		height=int((imp.getDimensions()[1])*(float(1)/float(size)))
		print(width, height)
		#resize images
		imp = imp.resize(width, height, "none");
		print(imp.getDimensions())
		#multiple files
		#mac or windows
		test_interim = os.path.join(test_interim, "_"+str(num))
		print(test_interim)
		try:
			os.mkdir(test_interim)
		except OSError:
			pass
		if windows:
			#one file
			IJ.saveAs(imp, "Tiff", test_interim+"\\"+title);
		elif not windows:
			#one file
			IJ.saveAs(imp, "Tiff", test_interim+"/"+title);
	layerset.getLayer(0, 1, True)
		
	#populates first layer with OV and NO images
	for i,layer in enumerate(layerset.getLayers()):
		for n, fold in enumerate(filenames_keys):
	#		print(fold)
	#		print(filenames_dict[fold][i])
			filepath = os.path.join(fold, filenames_values[n][i])
			patch = Patch.createPatch(project, filepath)
			layer.add(patch)
	#		print(patch)
		layer.recreateBuckets()
		pass
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
	 	print(roi.width,roi.height)
		project.saveAs(os.path.join(joint_folder, project_name+"test"), False)	
		for tile in tiles:
			tile.remove(False)
		
#		layer.remove(False)
	imp = plugin.FolderOpener.open(folder, "virtual");
	title=imp.getTitle()
	ROI=imp.setRoi(roi.x-10,roi.y-10,roi.width+10,roi.height+10);
	print(imp.getDimensions())
	imp=imp.crop("stack")
#	imp.cropAndSave(ROI,
#					"Users/lamarcki/Desktop/automating_before_catmaid/trakem2/interim_folder",
#					"show")
#	imp = imp.resize(roi.width+10, roi.height+10, "bilinear");
	
	print(imp.getDimensions())
	width=imp.getDimensions()[0]*size
	height=imp.getDimensions()[1]*size
	#resize images
	imp = imp.resize(width, height, "none");
	print(imp.getDimensions())
	#multiple files
	#mac or windows
	Title=imp.setTitle("")
	output_scaled=os.path.join(joint_folder, "OV_interim")
	try:
		os.mkdir(output_scaled)
	except OSError:
		pass
	if windows:
		if imp.getDimensions()[3] != 1:
			plugin.StackWriter.save(imp, output_scaled+"\\", "format=tiff");
		#one file
		elif imp.getDimensions()[3] == 1:
			IJ.saveAs(imp, "Tiff", output_scaled+"\\"+title);
	elif not windows:
		if imp.getDimensions()[3] != 1:
			plugin.StackWriter.save(imp, output_scaled+"/", "format=tiff");
		#one file
		elif imp.getDimensions()[3] == 1:
			IJ.saveAs(imp, "Tiff", output_scaled+"/"+title);
	for i, fold in enumerate(filenames_keys):
		if fold == folder:
			#check
			OV_file=filter(pattern_3.match, os.listdir(output_scaled))
			for  n, filename in enumerate(OV_file):
				for m, filename_2 in enumerate(OV_file[n+1:len(OV_file)]):
					match = int(re.findall("(\d+)",filename)[0])
					match_2 = int(re.findall("(\d+)",filename_2)[0])
		#			print(filename,filename_2)
					if match > match_2:
						temp_1=filename
						temp_2=filename_2
		#				print(filename,filename_2)
						filename=temp_2
						filename_2=temp_1
						OV_file[n]=temp_2
						OV_file[n+m+1]=temp_1
		#				print(filename,filename_2)
			filenames_keys[i] = output_scaled
			filenames_values[i] = OV_file	
print(filenames_keys,filenames_values)

# ... and update the LayerTree:
#project.getLayerTree().updateList(layerset)
#works without this...
# ... and the display slider
#Display.updateLayerScroller(layerset)
#works without this...

#Creates a layer for each image in folder 1 stack 
#and
#since filenames are integers, finds smallest integer from where to start iterating from

for  m, fold in enumerate(filenames_keys):
	for n, filename in enumerate(filenames_values[m][1:len(filenames_values[m])+1]):
#		print(filename)
		layerset.getLayer(n+1, 1, True)
	pass	
	
#populates layers with OV and NO images
for i,layer in enumerate(layerset.getLayers()):
	for n, fold in enumerate(filenames_keys):
#		print(fold)
#		print(filenames_dict[fold][i])
		filepath = os.path.join(fold, filenames_values[n][i])
		patch = Patch.createPatch(project, filepath)
		layer.add(patch)
#		print(patch)
	layer.recreateBuckets()

#Montages/aligns each layer
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

# readjusts canvas size to alignment/montage
#layerset.setMinimumDimensions() #useful in OV script
#roi=layerset.get2DBounds() # was useful for saving NO in 2D space

# Blends images of each layer
#if blending wanted, this would be later between layers
#Blending.blendLayerWise(layerset.getLayers(), True, None)

#gui = GenericDialog("Aligned?")
#gui.addMessage("Inspect alignment results. If there is any jitter (that isn't already present\n in the OV itself), manually fix this by re-running the alignment with updated\n parameters (i.e., try increasing Maximum Image Size parameter by\n 200 px.)\n\n Check image tile overlap and blend if desired.\n (Note: There is no 'Undo' for blending).\n\n If you would like to revert to previous state, use project 'montage_checkpoint.xml'.\n\n When image alignment is satisfactory, select 'Export'. A project .xml file\n will be saved in <dir> with user changes. Images will be exported as .tif to <dir>.")
#gui.showDialog()
#
project.saveAs(os.path.join(joint_folder, project_name+"with_OV"), False)
#if gui.wasOKed():
if 1:
#    inString = gui.getNextString()
#    inBool   = gui.getNextBoolean()
#    inChoice = gui.getNextChoice() # one could alternatively call the getNextChoiceIndex too
#    inNum    = gui.getNextNumber() # This always return a double (ie might need to cast to int)
#some sort of if statement if a decision to realign with 200 higher parameters is needed

#removes the OV tile
	for i, layer in enumerate(layerset.getLayers()):
		tiles = layer.getDisplayables(Patch)
		tiles[0].remove(False)
	layerset.setMinimumDimensions() #readjust canvas to only NO tiles
	
	roi=layerset.get2DBounds() # was useful for saving NO in 2D space
	#exports images
	for i, layer in enumerate(layerset.getLayers()):
	#  print(layer)
	  tiles = layer.getDisplayables(Patch)
	#  print(tiles)
	#  roi = tiles[0].getBoundingBox() #needed in OV alignment
	#  for tile in tiles[1:]:
	#  	roi.add(tile.getBoundingBox())
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
	  #unsure if we need to correct for Gaussianblur
	#  imp.getProcessor().blurGaussian(sigmaPixels)
	#pretty sure 3 refers to median_filter
	#https://imagej.nih.gov/ij/developer/api/ij/ij/process/ImageProcessor.html#filter(int)
	#  imp.getProcessor().filter(3)
	#  Flat.getInstance().run( imp, 
	#                        blocksize,
	#                        histogram_bins,
	#                        maximum_slope,
	#                        mask,
	#                        composite )
	  FileSaver(imp).saveAsTiff(output_dir + "/" + str(i + 1) + ".tif") #saves file to output directory
	
	#Saves the project
	project.saveAs(os.path.join(joint_folder, project_name+"without_OV"), False)
	
	print("Done!")