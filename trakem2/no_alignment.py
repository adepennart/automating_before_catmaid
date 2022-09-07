#run("TrakEM2 (blank)", "select=/Users/Auguste/Desktop/ex_image_stack/trakem2.1659102927438.226972917.1006530210");
# Albert Cardona 2011-06-05
# Script for Colenso Speer

#@ File (label = "Input directory", style = "directory") folder
#@ File (label = "Input directory 2 (if needed)", style = "directory", required= False) folder_2
#obselete
#@ File (label = "interim directory", style = "directory") output_scaled
##@ int (label = "layer_count", value=5, min=1, max=10, style=slider ) layers
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ String(choices={".GRAY8", ".GRAY16", ".GRAY32", ".COLOR_RGB"}, style="list") export_type
#@ boolean (label = "Don't invert images") inverted_image
#Tile_002-001-001842_0-000.s1853_e01.tif
#DO THIS
#should be able to count layers in file
#only accepts tif files as input
#invert at beginning
#rescale at beginning 
# crop at beginning

import os, re
from ij import IJ, ImagePlus, plugin
from ini.trakem2 import Project
from ini.trakem2.display import Display, Patch
from ini.trakem2.imaging import Blending
from ij.io import FileSaver
from java.awt import Color
from mpicbg.ij.clahe import Flat

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

if export_type == ".GRAY8":
	export_type=0
elif export_type == ".GRAY16":
	export_type=1
elif export_type == ".GRAY32":
	export_type=2
elif export_type == ".COLOR_RGB":
	export_type=4

#variable
joint_folder=[]
pattern = re.compile(".*_z[\d]_.*\.tif")
#for line 170 to work with one input folder
filenames_2=""

#folder = "/path/to/folder/with/all/images/"
#print(type(folder))
folder = folder.getAbsolutePath()
if folder_2:
	folder_2 = folder_2.getAbsolutePath()
	print(folder_2)
#print(type(folder))
print(folder)
#folder = "/Users/Auguste/Desktop/ex_image_stack/trakem2"
#print(type(output_dir))
output_dir = output_dir.getAbsolutePath()
print(type(output_dir))

match_1=re.findall("\/.[^\/]+",folder)
if folder_2:
	match_2=re.findall("\/.[^\/]+",folder_2)
#print(match_1)
#print(match_2)

if folder_2:
	if match_1[len(match_1)-1] == match_2[len(match_2)-1]:
	#	print("woot",match_1[len(match_1)-1],match_2[len(match_2)-1])
		joint_folder=match_1
	elif match_1[len(match_1)-1] != match_2[len(match_2)-1]:
	#	print("sad",match_1[len(match_1)-1],match_2[len(match_2)-1])
		for fold in reversed(match_1):
			if fold in match_2:
	#			print(fold,"found")
	#			fold_good=re.search("(\/.[^\/]+)",fold).group(0)
	#			joint_folder.insert(0,fold_good)	
				joint_folder.insert(0,fold)
	#print((joint_folder))
	#		if fold 
	joint_folder="".join(joint_folder)
#print((joint_folder))
elif not folder_2:
	joint_folder=match_1
	joint_folder="".join(joint_folder)

#set threads

#gaussian_blur
sigmaPixels=2
#CLAHE
blocksize = 50
histogram_bins = 128
maximum_slope = 3
mask = "*None*"
fast = True
process_as_composite = False
composite = False
mask = None

# 3. To each layer, add images that have "_zN_" in the name
#     where N is the index of the layer
#     and also end with ".tif"
filenames = filter(pattern.match, os.listdir(folder))
for n,filename in enumerate(filenames):
	for m,filename_2 in enumerate(filenames[n+1:len(filenames)]):
		if filename == filename_2:
			print("found duplicate", filename, filename_2, "at position", n+1, m+1, "in folder" )
			#need to kill code here so that they can delete duplicate
#		for num in range(0,len(filename)):
#			if filename[num] == filename_2[num]:
##				print(filename, filename_2,filename[num])
#				if filename[num] == len(filename):
#					print("found duplicate ", filename, filename_2, " at", n, m )
#			elif filename[num] != filename_2[num]:
#				break
if folder_2:
	filenames_2 = filter(pattern.match, os.listdir(folder_2))
	#print(filenames)
	if len(filenames) == len(filenames_2):
		filenames_3=filenames+filenames_2
	else:
		print("not an equal number of files in each folder")
		#need to kill code here so that they can delete duplicate
elif not folder_2:
	filenames_3=filenames
print(filenames_3)

#project=IJ.run("TrakEM2 (blank)", "select=/Users/Auguste/Desktop/ex_image_stack/trakem2")
#project=IJ.run("TrakEM2 (blank)")
#Project.newFSProject("blank", None, folder)
# 1. Create a TrakEM2 project
project = Project.newFSProject("blank", None, joint_folder)
#project = Project.newFSProject("blank", None)
# OR: get the first open project
# project = Project.getProjects().get(0)


#print(project)
layerset = project.getRootLayerSet()
##print(layerset)
##  2. Create 10 layers (or as many as you need)
##picks layer 0 even if there isn't one
#for i in range(layers):
#	layerset.getLayer(i, 1, True)
##  layerset.getLayer(i, 0, True)


imp = plugin.FolderOpener.open(folder, "virtual");
title=imp.getTitle()
dimen=IJ.getScreenSize()
print(dimen.width,dimen.height)
print(imp.getDimensions())
width=imp.getDimensions()[0]*4
height=imp.getDimensions()[1]*4
imp = imp.resize(width, height, "none");
print(imp.getDimensions())
#IJ.saveAs(imp, "Tiff", folder+"/"+"ov_z1_-1.tif");
#IJ.saveAs(imp, "Tiff", folder+"/"+"ov_z1_.tif");
#IJ.saveAs(imp, "Tiff", folder);
output_scaled = output_scaled.getAbsolutePath()
title=imp.setTitle("")
#what if one file
if imp.getDimensions()[3] != 1:
	plugin.StackWriter.save(imp, output_scaled+"/", "format=tiff");
#IJ.saveAs(imp, "Tiff", output_scaled+"/"+title);
elif imp.getDimensions()[3] == 1:
	IJ.saveAs(imp, "Tiff", output_scaled+"/"+title);

# ... and update the LayerTree:
project.getLayerTree().updateList(layerset)
# ... and the display slider
Display.updateLayerScroller(layerset)

#  2. Create 10 layers (or as many as you need)
#picks layer 0 even if there isn't one
if filenames_2:
	for i in range(len(filenames)):
		layerset.getLayer(i, 1, True)
#this is correct
#elif not filenames_2:
#	for i in range(len(filenames)/2):
#		layerset.getLayer(i, 1, True)
#this is incorrect
elif not filenames_2:
	for i in range(len(filenames)):
		layerset.getLayer(i, 1, True)
		#assumes only two different layers
	
	
#for filename in filenames_3:
#	print(filename)
#	#find another matching code
#	match = re.findall("(\d)",filename)
##	for some reason does not work
##	match = re.search(".*_z(\d)_.*\.tif",filename).group(0)
#	n_start=int(match[1])
#	print(n_start)
#	break

for n, filename in enumerate(filenames_3):
	print(filename)
	#find another matching code
	match = re.findall("(\d)",filename)
#	for some reason does not work
#	match = re.search(".*_z(\d)_.*\.tif",filename).group(0)
#	if n == 0:
#		n_start=int(match[1])
#	elif n != 0 :
#		num=int(match[1])
#		if num < n_start:
#			n_start=int(match[1])
#only one number here
	if n == 0:
		n_start=int(match[0])
	elif n != 0 :
		num=int(match[0])
		if num < n_start:
			n_start=int(match[0])
print(n_start)
	
			
#for filename in filenames_3:
#	filename.encode('ascii','ignore')

##.*-([\d]{3})-.*\.tif
#for filename in filenames_3:
#	print(filename)
#	if re.search(".*_z\d_.*\.tif",filename):
#	match = re.search(".*_z(\d)_.*\.tif",filename).group(0)

for i,layer in enumerate(layerset.getLayers()):
	# EDIT the following pattern to match the filename of the images
	# that must be inserted into section at index i:
	#will have to get input from user what the start file is
	pattern = re.compile(".*_z" + str(n_start+i) + "_.*\.tif")
	for filename in filter(pattern.match, filenames_3):
#    print(pattern.match,i)
#    print(filename)
#		filepath = os.path.join(folder, filename)
		if filename in filenames:
#			print(filename)
			filepath = os.path.join(folder, filename)
			patch = Patch.createPatch(project, filepath)
			layer.add(patch)
#			print(filepath)
		if filename in filenames_2:
#			print(filename)
#			filepath_2 = os.path.join(folder_2, filename)
#			print(filepath_2)
			filepath = os.path.join(folder_2, filename)
			patch = Patch.createPatch(project, filepath)
			layer.add(patch)
#			print(filepath)
#	filepath=filepath+filepath_2
#	print(filepath)
#    print(patch)
#    print(layer)
# 	 Update internal quadtree of the layer
	layer.recreateBuckets()
#
#for i,layer in enumerate(layerset.getLayers()):
#  # EDIT the following pattern to match the filename of the images
#  # that must be inserted into section at index i:
#  pattern = re.compile(".*_z" + str(i) + "_.*\.tif")
#  for filename in filter(pattern.match, filenames):
##    print(pattern.match,i)
##    print(filename)
#    filepath = os.path.join(folder, filename)
##		if filename in os.path.join(folder, filename):
##	  		filepath = os.path.join(folder, filename)
##	  		print(filepath)
##		if filename in os.path.join(folder_2, filename):
##	  		filepath_2 = os.path.join(folder_2, filename)
##	  		print(filepath_2)
##    	filepath=filepath+filepath_2
#    print(filepath)
#    patch = Patch.createPatch(project, filepath)
#    layer.add(patch)
#    print(patch)
##    print(layer)
#  # Update internal quadtree of the layer
#  layer.recreateBuckets()

# 4. Montage each layer independently
from mpicbg.trakem2.align import Align, AlignTask
from mpicbg.trakem2.align import RegularizedAffineLayerAlignment
from java.util import HashSet

#Align.alignLayersLinearly(layerset.getLayers(),1)
#for layer in layerset.getLayers():
#	tiles = layer.getDisplayables(Patch)
##	fix so that set patches can be determined
##  	0=linear sift correspondance
#	tiles[0].setLocked(True)
#	Align.alignLayer(layer, 1)
param = Align.ParamOptimize(desiredModelIndex=0,expectedModelIndex=0)  # which extends Align.Param
param.sift.maxOctaveSize = 512
for layer in layerset.getLayers():
  	tiles = layer.getDisplayables(Patch)
#	fix so that set patches can be determined
#  	0=linear sift correspondance
#	non_move = {tiles[0]}
#	tiles[0].scale(
#		0,
#		0,
#		0,
#		0)
	layerset.setMinimumDimensions()
	tiles[0].setLocked(True)
	non_move = [tiles[0]]
#	non_move = []
#	AlignTask.alignPatches(tiles,non_move,0)
#	AlignTask.alignMultiLayerMosaicTask(layer,non_move)
#AlignTask(tilesAreInPlace=False)
#	AlignTask.tilesAreInPlace=False
	AlignTask.alignPatches(
	param,
	tiles,
	non_move,
	False,
	False,
	False,
	False) 

#select actually imports, just copied
#https://github.com/templiert/ufomsem/blob/79a02010533f8127deeb0fed04cfc1ea90edb7f0/stitch_align.py
#import os, time, sys
#from ij import IJ, Macro
#import java
#from java.lang import Runtime
#from java.awt import Rectangle
#from java.awt.geom import AffineTransform
#from java.util import HashSet
#from ini.trakem2 import Project, ControlWindow
#from ini.trakem2.display import Patch, Display
#from ini.trakem2.imaging import StitchingTEM
#from ini.trakem2.imaging.StitchingTEM import PhaseCorrelationParam
#from mpicbg.trakem2.align import RegularizedAffineLayerAlignment


#param = RegularizedAffineLayerAlignment.Param()
#param = Align.ParamOptimize(desiredModelIndex=0,expectedModelIndex=0)  # which extends Align.Param
#param = Align.ParamOptimize()  # which extends Align.Param
#param.sift.maxOctaveSize = 512
#param.ppm.sift.maxOctaveSize = 512
#fixedLayers = HashSet()
#for i in range(len(layerset.getLayers())):
#    fixedLayers.add(layerset.getLayers().get(i))

#emptyLayers = HashSet()

#layerRange = layerset.getLayers(len(layerset.getLayers())-1,len(layerset.getLayers()))
#layerRange = layerset.getLayers(len(layerset.getLayers())-2,len(layerset.getLayers())-1)
#  ... above, adjust other parameters as necessary
# See:
#    features: https://fiji.sc/javadoc/mpicbg/trakem2/align/Align.Param.html
#    transformation models: https://fiji.sc/javadoc/mpicbg/trakem2/align/Align.ParamOptimize.html
#    sift: https://fiji.sc/javadoc/mpicbg/imagefeatures/FloatArray2DSIFT.Param.
#print("hey")
#print(layerRange)
#print(param)
#AlignTask.montageLayers(param, layerset.getLayers(), False, False, False, False)
#RegularizedAffineLayerAlignment().exec(
#        param,
#        layerRange,	
#        fixedLayers,
#        emptyLayers,
#        layerset.get2DBounds(),
#        False,
#        False,
#        None)
# 5. Resize width and height of the world to fit the montages
layerset.setMinimumDimensions()
roi=layerset.get2DBounds()

# 6. Blend images of each layer
#Blending.blendLayerWise(layerset.getLayers(), True, None)

#front = Display.getFront() # the active TrakEM2 display window
#layer = front.getLayer()
#tiles = layer.getDisplayables(Patch)
##tiles = front.getSelection().get(Patch)  # selected Patch instances only
#backgroundColor = Color.black
#scale = 1.0
#
##roi=Patch.getBoundingBox()	
#print(front)
#print(layer)
#print(Patch)
#print(tiles)
#
#roi = tiles[0].getBoundingBox()
#for tile in tiles[1:]:
#	roi.add(tile.getBoundingBox())
#		
#ip = Patch.makeFlatImage(
#          ImagePlus.GRAY16,
#           layer,
#           roi,
#           scale,
#           tiles,
#          backgroundColor,
#          True)  # use the min and max of each tileimp = ImagePlus("Flat montage", ip)
#imp = ImagePlus("Flat montage", ip)
#imp.show() 

#project = Project.getProjects()[0]
#layerset = project.getRootLayerSet()

#front = Display.getFront(project)
#roi = front.getRoi()
#roi=roi.getBoundingBox()
scale = 1.0
backgroundColor = Color.black

# NOTE: EDIT THIS PATH
targetDir = output_dir

#For other output types, use ImagePlus.GRAY8, .GRAY16, GRAY32 or .COLOR_RGB, as listed in the documentation for the ImagePlus class.

#this may not be what we are looking for as roi is the bonding box
#for i, layer in enumerate(layerset.getLayers()):
##  print(layer)
#  # Export the image here, e.g.:
#  tiles = layer.getDisplayables(Patch)
#  roi = tiles[0].getBoundingBox()
#  for tile in tiles[1:]:
#  	roi.add(tile.getBoundingBox())
#  ip = Patch.makeFlatImage(
#           export_type,
#           layer,
#           roi,
#           scale,
#           tiles,
#           backgroundColor,
#           True)  # use the min and max of each tile

for i, layer in enumerate(layerset.getLayers()):
#  print(layer)
  # Export the image here, e.g.:
#  roi=layer.getMinimalBoundingBox()
#  roi=roi.getBoundingBox()
  tiles = layer.getDisplayables(Patch)
#  print(tiles)
#  roi = tiles[0].getBoundingBox()
#  for tile in tiles[1:]:
#  	roi.add(tile.getBoundingBox())
  ip = Patch.makeFlatImage(
           export_type,
           layer,
           roi,
           scale,
           tiles,
           backgroundColor,
           True)  # use the min and max of each tile

  imp = ImagePlus("Flat montage", ip)
  #invert
  if inverted_image == 0:
  	imp.getProcessor().invert()
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
  FileSaver(imp).saveAsTiff(targetDir + "/" + str(i + 1) + ".tif")

## 7. Save the project
project.saveAs(os.path.join(joint_folder, project_name), False)


print("Done!")