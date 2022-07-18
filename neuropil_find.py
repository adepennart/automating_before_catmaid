
#@ File    (label = "Template", style = "file") template
#@ File    (label = "Image Stack directory", style = "directory") srcFile
#@ File    (label = "Output directory", style = "directory") dstFile
#@ String  (label = "File extension", value=".tif") ext
#@ String  (label = "File name contains", value = "") containString
#@ boolean (label = "Keep directory structure when saving", value = true) keepDirectories

# See also Process_Folder.ijm for a version of this code
# in the ImageJ 1.x macro language.

import os
from ij import IJ, ImagePlus, plugin

def run():
  Template = template.getAbsolutePath()
  srcDir = srcFile.getAbsolutePath()
  dstDir = dstFile.getAbsolutePath()
  for root, directories, filenames in os.walk(srcDir):
    filenames.sort();
    for filename in filenames:
      # Check for file extension
      if not filename.endswith(ext):
        continue
      # Check for file name pattern
      if containString not in filename:
        continue
      process(Template, srcDir, dstDir, root, filename, keepDirectories)
 
def process(Template, srcDir, dstDir, currentDir, fileName, keepDirectories):
  print "Processing:"
   
  # Opening the image
  print "Open image file", fileName
#  imp = IJ.openImage(os.path.join(currentDir, fileName))
  print(Template)
  imp = IJ.openImage(Template);
  imp = plugin.FolderOpener.open(srcDir, "");
  print(imp)
  # Put your processing commands here!
  IJ.run(imp, "Template Matching Image", "template=[Screen Shot 2022-07-11 at 3.18.09 PM.png] image=screenshots rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
  # Saving the image
  saveDir = currentDir.replace(srcDir, dstDir) if keepDirectories else dstDir
  if not os.path.exists(saveDir):
    os.makedirs(saveDir)
  print "Saving to", saveDir
  IJ.saveAs(imp, "Tiff", os.path.join(saveDir, fileName));
  imp.close()
  
imp = IJ.openImage("/Users/Auguste/Desktop/ex_image_stack/screenshots/Screen Shot 2022-07-11 at 3.17.58 PM.png");
imp = IJ.openImage("/Users/Auguste/Desktop/ex_image_stack/Screen Shot 2022-07-11 at 3.18.09 PM.png");
print(imp)
run()
