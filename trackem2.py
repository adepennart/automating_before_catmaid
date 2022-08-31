#run("TrakEM2 (blank)", "select=/Users/Auguste/Desktop/ex_image_stack/trakem2.1659102927438.226972917.1006530210");
# Albert Cardona 2011-06-05
# Script for Colenso Speer

#@ File (label = "Input directory", style = "directory") folder
#@ File (label = "Input directory 2 (if needed)", style = "directory", required= False) folder_2
#obselete
##@ int (label = "layer_count", value=5, min=1, max=10, style=slider ) layers
#@ File (label = "Output directory", style = "directory") output_dir
#@ String (label = "project name") project_name
#@ String(choices={"translation", "rigid", "similarity", "affine"}, style="list") model_index
##@ int (label = "octave_size", value=512, min=500, max=1200) octave_size
#@ String(choices={".GRAY8", ".GRAY16", ".GRAY32", ".COLOR_RGB"}, style="list") export_type
#@ boolean (label = "Don't invert images") inverted_image
#@ boolean (label = "not working on windows") not_windows
#Tile_002-001-001842_0-000.s1853_e01.tif
#DO THIS
#allow selection of rigid, affine, etc
#test dataset first?
#check if same named for each file
#adjust cores

import os, re, time, threading
from ij import IJ, ImagePlus, plugin
from ini.trakem2 import Project
from ini.trakem2.display import Display, Patch
from ini.trakem2.imaging import Blending
from ij.io import FileSaver
from java.awt import Color
from mpicbg.ij.clahe import Flat

from java.lang import Runtime
from java.util.concurrent import Executors


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

octave_size=512

if model_index == "translation":
	model_index=0
elif model_index == "rigid":
	model_index=1
elif model_index == "similarity":
	model_index=2
elif model_index == "affine":
	model_index=4

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
#specify pattern(not sure this actually impacts anything)
#pattern = re.compile(".*-([\d]{3})-([\d]+)_.*\.tif")
pattern = re.compile(".*_z[\d]_.*\.tif")

#folder = "/path/to/folder/with/all/images/"
#print(type(folder))
folder = folder.getAbsolutePath()
if folder_2:
	folder_2 = folder_2.getAbsolutePath()
#	print(folder_2)
#print(type(folder))
#print(folder)
#folder = "/Users/Auguste/Desktop/ex_image_stack/trakem2"
#print(type(output_dir))
output_dir = output_dir.getAbsolutePath()
#print(type(output_dir))

#match_1=re.findall("[\d]+",folder)
if not_windows:
	match_1=re.findall("\/.[^\/]+",folder)
	match_2=re.findall("\/.[^\/]+",folder_2)
elif not not_windows:
	match_1=re.findall(".[^\\\\]+",folder)
	match_2=re.findall(".[^\\\\]+",folder_2)

#print(match_1)
#print(match_2)

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
#print("hey")
#print(joint_folder)

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
#	print(filenames)
	if len(filenames) == len(filenames_2):
		filenames_3=filenames+filenames_2
#		print(filenames_3)
#		print(len(filenames_3))
	else:
		print("not an equal number of files in each folder")
		#need to kill code here so that they can delete duplicate
elif not folder_2:
	filenames_3=filenames

filenames_4=[]
for n,filename in enumerate(filenames_3):
#	print(filename)
	for m,filename_2 in enumerate(filenames_3[n+1:len(filenames_3)]):
		if filename == filename_2:
			print("found duplicate file name", filename, filename_2, "at position", n+1, m+1, "in folder" )
#			filenames_3.remove(filename_2)
			filenames_4.append(filename_2)
			break
if filenames_4 != []:
#	print(filenames_4)
	filenames_3=filenames_4
	
#print(len(filenames_4))
#project=IJ.run("TrakEM2 (blank)", "select=/Users/Auguste/Desktop/ex_image_stack/trakem2")
#project=IJ.run("TrakEM2 (blank)")
#Project.newFSProject("blank", None, folder)
# 1. Create a TrakEM2 project
project = Project.newFSProject("blank", None, joint_folder)
#only means to date i found for updating threads
#project.adjustProperties()

#project = Project.newFSProject("blank", None)
# OR: get the first open project
# project = Project.getProjects().get(0)

#exe = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors())
#exe = Executors.newScheduledThreadPool(1)
#print('ThreadRange = ' + str(exe))

#print(project)
layerset = project.getRootLayerSet()
##print(layerset)

##  2. Create 10 layers (or as many as you need)
##picks layer 0 even if there isn't one
#for i in range(layers):
#	layerset.getLayer(i, 1, True)
##  layerset.getLayer(i, 0, True)

# ... and update the LayerTree:
project.getLayerTree().updateList(layerset)
# ... and the display slider
Display.updateLayerScroller(layerset)

#  2. Create 10 layers (or as many as you need)
#picks layer 0 even if there isn't one

if filenames_2:
	for i in range(len(filenames)):
		layerset.getLayer(i, 1, True)
elif not filenames_2:
	for i in range(len(filenames)/2):
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
#	print(filename)
	#pattern on mac
	match = re.findall("(\d)",filename)
	#pattern on pc
#	match = re.findall("-(\d+)_",filename)
#	print(match)
#	match= re.findall("[\d]+",match)
#	for some reason does not work
#	match = re.search(".*_z(\d)_.*\.tif",filename).group(0)
#mac pattern
	if n == 0:
		n_start=int(match[1])
	elif n != 0 :
		num=int(match[1])
		if num < n_start:
			n_start=int(match[1])
#windows pattern
#	if n == 0:
#		n_start=int(match[0])
#	elif n != 0 :
#		num=int(match[0])
#		if num < n_start:
#			n_start=int(match[0])
#print(n_start)
	
			
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
#	pattern = re.compile(".*-[\d]{3}-0+"+ str(n_start+i) + "_.*\.tif")
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
#				print(filename)
	#			filepath_2 = os.path.join(folder_2, filename)
	#			print(filepath_2)
				filepath = os.path.join(folder_2, filename)
				patch = Patch.createPatch(project, filepath)
				layer.add(patch)
#				print(filepath)
#		filepath=filepath+filepath_2
#		print(filepath)
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
#def montaging(set_layer):
from mpicbg.trakem2.align import Align, AlignTask
#param = Align.ParamOptimize()  # which extends Align.Param
param = Align.ParamOptimize(
		desiredModelIndex=model_index,
		expectedModelIndex=model_index)#,
#		maxNumThreadsSift = Runtime.getRuntime().availableProcessors())  # which extends Align.Param
param.sift.maxOctaveSize = octave_size
#  ... above, adjust other parameters as necessary
# See:
#    features: https://fiji.sc/javadoc/mpicbg/trakem2/align/Align.Param.html
#    transformation models: https://fiji.sc/javadoc/mpicbg/trakem2/align/Align.ParamOptimize.html
#    sift: https://fiji.sc/javadoc/mpicbg/imagefeatures/FloatArray2DSIFT.Param.html

AlignTask.montageLayers(param, layerset.getLayers(), False, False, False, False)
#AlignTask.montageLayers(param, set_layer, False, False, False, False)
	
#threadRange = range(max(int(Runtime.getRuntime().availableProcessors()), 1))
#print(str(threadRange))
#
##you got to do everylayer
#for i, layer in enumerate(layerset.getLayers()):
#	for n in threadRange:
#		thread=threading.Thread(montaging(layer))
#		thread.start()

#AlignTask.montageLayers(param, layerset.getLayers(), False, False, False, False)

# 5. Resize width and height of the world to fit the montages
layerset.setMinimumDimensions()

# 6. Blend images of each layer
Blending.blendLayerWise(layerset.getLayers(), True, None)

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

front = Display.getFront(project)
#roi = front.getRoi()
scale = 1.0
backgroundColor = Color.black

# NOTE: EDIT THIS PATH
targetDir = output_dir

#For other output types, use ImagePlus.GRAY8, .GRAY16, GRAY32 or .COLOR_RGB, as listed in the documentation for the ImagePlus class.

for i, layer in enumerate(layerset.getLayers()):
#  print(layer)
  # Export the image here, e.g.:
  tiles = layer.getDisplayables(Patch)
  roi = tiles[0].getBoundingBox()
  for tile in tiles[1:]:
  	roi.add(tile.getBoundingBox())
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

print(time.time())
print("Done!")