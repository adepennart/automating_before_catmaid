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
#@ File (label = "interim directory", style = "directory") output_scaled
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ boolean (label = "Don't invert images") inverted_image
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
pattern_1 = re.compile(".*_z[\d]_.*\.tif")
#pattern_1 = re.compile("([\d]+).*\.tif")
pattern_2 = re.compile(".*_z[\d]_.*\.tif")
#pattern_2 = re.compile(".*-([\d]{3})-([\d]+)_.*\.tif")
pattern_v2_p1 = (".*_z")
pattern_v2_p2 = ("_.*\.tif")
z_axis_start=0 #z axis number in filename
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
backgroundColor = Color.black

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
output_scaled = output_scaled.getAbsolutePath()
output_dir = output_dir.getAbsolutePath()
#print(folder)
#print(folder_2)
#print(output_scaled)
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
#print(joint_folder)

#func: find files in input directories
filenames = filter(pattern_1.match, os.listdir(folder))
filenames_2 = filter(pattern_2.match, os.listdir(folder_2))
#func: find duplicates in NO folder
for n,filename in enumerate(filenames_2):
	for m,filename_2 in enumerate(filenames_2[n+1:len(filenames_2)]):
		if filename == filename_2:
			print("ERROR: found duplicate", filename, filename_2, "at position", n+1, m+1, "in folder" )
			sys.exit("found duplicate", filename, filename_2, "at position", n+1, m+1, "in folder" )
print(filenames)
print(filenames_2)
#func: checks for same amount of images in both input folders
if len(filenames) == len(filenames_2):
	filenames_3=filenames+filenames_2
else:
	print("ERROR: not an equal number of files in each folder")
	sys.exit("not an equal number of files in each folder")
	#need to kill code here so that they can delete duplicate
print(filenames_3)

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

#func: rescaling 
#open OV image stack
imp = plugin.FolderOpener.open(folder, "virtual");
title=imp.getTitle()
print(imp.getDimensions())
width=imp.getDimensions()[0]*size
height=imp.getDimensions()[1]*size
#resize images
imp = imp.resize(width, height, "none");
print(imp.getDimensions())
#multiple files
#mac or windows
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


# ... and update the LayerTree:
#project.getLayerTree().updateList(layerset)
#works without this...
# ... and the display slider
#Display.updateLayerScroller(layerset)
#works without this...

#Creates a layer for each image in folder 1 stack 
#and
#since filenames are integers, finds smallest integer from where to start iterating from

for n, filename in enumerate(filenames):
#	print(filename)
	layerset.getLayer(n, 1, True)
	match = re.findall("(\d)",filename)
	if n == 0:
		n_start=int(match[z_axis_start])
	elif n != 0 :
		num=int(match[z_axis_start])
		if num < n_start:
			n_start=int(match[z_axis_start])
#print/(n_start)

#for i in range(len(filenames)):
#	layerset.getLayer(i, 1, True)
#
#for n, filename in enumerate(filenames_3):
##	print(filename)
#	match = re.findall("(\d)",filename)
#	if n == 0:
#		n_start=int(match[0])
#	elif n != 0 :
#		num=int(match[0])
#		if num < n_start:
#			n_start=int(match[0])
#print/(n_start)

#populates layers with OV and NO images
for i,layer in enumerate(layerset.getLayers()):
	# EDIT the following pattern to match the filename of the images
	pattern_v2 = re.compile(pattern_v2_p1 + str(n_start+i) + pattern_v2_p2)
	for filename in filter(pattern_v2.match, filenames_3):
#    print(pattern.match,i)
#    print(filename)
		if filename in filenames:
#			print(filename)
			filepath = os.path.join(folder, filename)
			patch = Patch.createPatch(project, filepath)
			layer.add(patch)
#			print(filepath)
		if filename in filenames_2:
#			print(filename)
			filepath = os.path.join(folder_2, filename)
			patch = Patch.createPatch(project, filepath)
			layer.add(patch)
#			print(filepath)
#	print(filepath, patch, layer)
# 	 Update internal quadtree of the layer
#	need to find out what this does
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

gui = GenericDialog("Aligned?")
gui.addMessage("Inspect alignment results. If there is any jitter (that isn't already present\n in the OV itself), manually fix this by re-running the alignment with updated\n parameters (i.e., try increasing Maximum Image Size parameter by\n 200 px.)\n\n Check image tile overlap and blend if desired.\n (Note: There is no 'Undo' for blending).\n\n If you would like to revert to previous state, use project 'montage_checkpoint.xml'.\n\n When image alignment is satisfactory, select 'Export'. A project .xml file\n will be saved in <dir> with user changes. Images will be exported as .tif to <dir>.")
gui.showDialog()
#
project.saveAs(os.path.join(joint_folder, project_name+"with_OV"), False)
#if gui.wasOKed():
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

#exports images
for i, layer in enumerate(layerset.getLayers()):
#  print(layer)
  tiles = layer.getDisplayables(Patch)
#  print(tiles)
  roi = tiles[0].getBoundingBox() #needed in OV alignment
  for tile in tiles[1:]:
  	roi.add(tile.getBoundingBox())
  	#image paramaters, i believe
  ip = Patch.makeFlatImage(
           export_type,
           layer,
           roi,
           scale,
           [tiles[0]], # only getting NO patch
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