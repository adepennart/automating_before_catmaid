
<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#About">About</a>
    </li>
    <li>
      <a href="#Installation">Installation</a>
      <ul>
        <li><a href="#Dependencies">Dependencies</a></li>
      </ul>
    </li>
    <li><a href="#Usage">Usage</a></li>
      <ul>
        <li><a href="#Input">Input</a></li>
      </ul>
      <ul>
        <li><a href="#Example">Example</a></li>
      </ul>
  </ol>
</details>

## About
Two scripts to use subquentially for aligning low resolution images (low_res.py) and then high resolution images to the low resolution ones(high_res.py).

A final script is needed for uploading images to catmaid(catmaid.py) after either low_res.py or high_res.py. 

Additional useful scripts are also present for use.

example inputs and outputs are also provided.

The scripts runs on ImageJ.


## Installation
This program can be directly installed from github (green Code button, top right).

Make sure to change into the downloaded directory, the code should resemble something like this.
```bash=
cd Downloads/automating_before_catmaid
```

### Dependencies
The script runs with ImageJ/Fiji=1.53. ImageJ can be downloaded via the link below:
https://imagej.net/software/fiji/downloads

## Usage
The script can be opened by dragging it onto the ImageJ toolbar.
You can also open via the File>Open.. tab for ImageJ.

Once the script is loaded, there is a 'Run' button on the bottom left. Pressing this button will prompt you with a menu of parameters to fill.

### Input
#### low_res.py

Below you have the parameter menu given to you for low_res.py and further below the explanation for each parameter. 
```
Input directory
Output directory
project name
Invert images
octave_size
Model_index
using a windows machine
script previously run (alignment parameter saved in file)
Elastic Alignment
Unorganized input
```

INPUT DIRECTORY, The directory with all the images to be aligned. Image substacks are to be placed in sub directories. Image tiles are to be further placed in subsub directories. I.e., folder structure below.
```
++------/input
+	+------/OV
+		+------/OV1
+			+------/ov1_1_.tif
+			+------/ov1_2_.tif
+			+------[...]
+			+------/ov1_n_.tif
+		+------/OV2
+			+------/ov2_1_.tif
+			+------/ov2_2_.tif
+			+------[...]
+			+------/ov2_n_.tif
+		+------/[...]
+		+------/OVn
+			+------/ovn_1_.tif
+			+------/ovn_2_.tif
+			+------[...]
+			+------/ovn_n_.tif
```
OUTPUT DIRECTORY, an empty directory where output images will be placed.

PROJECT NAME, chosen name for your Trackem2 project.

INVERT IMAGES, specify whether you would like your images inverted.
        
OCTAVE_SIZE, maximum image size(px). Default should be 1000.

MODEL_INDEX, choice of alignment between translation, rigid, similarity and affine.

USING A WINDOWS MACHINE, specify whether you are using a windows machine or not.

SCRIPT PREVIOUSLY RUN (alignment parameter saved in file), Select when rerunning script, i.e., when a previous run crashes before the end.

ELASTIC ALIGNMENT, Specify whether you would like to elastically align the images.

UNORGANIZED INPUT, Specify whether you have SBEM info files present to correctly organize files for alignment.

ELASTIC ALIGNMENT, Specify whether you would like to elastically align the images.

UNORGANIZED INPUT, Specify whether you have SBEM info files present to correctly organize files for alignment.

#### high_res.py

Below you have the parameter menu given to you for high_res.py and further below the explanation for each parameter. 
```
low resolution directory
high resolution directory
Output directory
project name
Invert high resolution images
low resolution rescale factor
octave_size
Model_index
using a windows machine
script previously run (alignment parameter saved in file)
Elastic Alignment
Unorganized input
```

LOW RESOLUTION DIRECTORY, The directory with all the low resolution images to be aligned. Image substacks are to be placed in sub directories. Image tiles are to be further placed in subsub directories. I.e., folder structure below.
```
++------/input
+	+------/OV
+		+------/OV1
+			+------/ov1_1_.tif
+			+------/ov1_2_.tif
+			+------[...]
+			+------/ov1_n_.tif
+		+------/OV2
+			+------/ov2_1_.tif
+			+------/ov2_2_.tif
+			+------[...]
+			+------/ov2_n_.tif
+		+------[...]
+		+------/OVn
+			+------/ovn_1_.tif
+			+------/ovn_2_.tif
+			+------[...]
+			+------/ovn_n_.tif
```

HIGH RESOLUTION DIRECTORY, The directory with all the high resolution images to be aligned. Image substacks are to be placed in sub directories. Image tiles are to be further placed in subsub directories. 
```
++------/input
+	+------/NO
+		+------/NO1
+			+------/NO1_tile1
+				+------/no1_tile1_1_.tif
+				+------/no1_tile1_2_.tif
+				+------[...]
+				+------/no1_tile1_n_.tif
+			+------/NO1_tile2
+				+------/no1_tile2_1_.tif
+				+------/no1_tile2_2_.tif
+				+------[...]
+				+------/no1_tile2_n_.tif
+			+------[...]
+			+------/NO1_tilen
+				+------/no1_tilen_1_.tif
+				+------/no1_tilen_2_.tif
+				+------[...]
+				+------/no1_tilen_n_.tif
+		+------/NO2
+			+------/NO2_tile1
+				+------/no2_tile1_1_.tif
+				+------/no2_tile1_2_.tif
+				+------[...]
+				+------/no2_tile1_n_.tif
+			+------/NO2_tile2
+				+------/no2_tile2_1_.tif
+				+------/no2_tile2_2_.tif
+				+------[...]
+				+------/no2_tile2_n_.tif
+			+------[...]
+			+------/NO2_tilen
+				+------/non_tilen_1_.tif
+				+------/non_tilen_2_.tif
+				+------[...]
+				+------/no2_tilen_n_.tif
+		+------/[...]
+		+------/NOn
+			+------/NOn_tile1
+				+------/non_tile1_1_.tif
+				+------/non_tile1_2_.tif
+				+------[...]
+				+------/non_tile1_n_.tif
+			+------/NOn_tile2
+				+------/non_tile2_1_.tif
+				+------/non_tile2_2_.tif
+				+------[...]
+				+------/non_tile2_n_.tif
+			+------[...]
+			+------/NOn_tilen
+				+------/non_tilen_1_.tif
+				+------/non_tilen_2_.tif
+				+------[...]
+				+------/non_tilen_n_.tif

++++++++++++++++++++++++++++++++++++++++++++++++++
```
OUTPUT DIRECTORY, an empty directory where output images will be placed.

PROJECT NAME, chosen name for your Trackem2 project.

INVERT HR IMAGES, specify whether you would like your high resolution images inverted.

RESCALE OV FACTOR, specify the magnitude difference between high and low resolution images. Default is 4, where high resolution images are 4 times more magnified than low resolution.
        
OCTAVE_SIZE, maximum image size(px). Default should be 1000.

MODEL_INDEX, choice of alignment between translation, rigid, similarity and affine.

USING A WINDOWS MACHINE, specify whether you are using a windows machine or not.

SCRIPT PREVIOUSLY RUN (alignment parameter saved in file), Select when rerunning script, i.e., when a previous run crashes before the end.

ELASTIC ALIGNMENT, Specify whether you would like to elastically align the images.

UNORGANIZED INPUT, Specify whether you have SBEM info files present to correctly organize files for alignment.

#### catmaid.py

Below you have the parameter menu given to you for catmaid.py. 

```
Input directory
Output directory
project name
using a windows machine
add images to layers in trackem2
export images as unprocessed and processed"
is project already loaded in trakem2 as only loaded project
```

INPUT DIRECTORY, The directory with all the images to be aligned.

OUTPUT DIRECTORY, an empty directory where output images will be placed.

PROJECT NAME, chosen name for your Trackem2 project.
        
USING A WINDOWS MACHINE, specify whether you are using a windows machine or not.

ADD IMAGES...TRACKEM2, add images to layers of trakem2 project.

EXPROT IMAGES...PROCESSED, specify whether you would like to export images as processed and unprocessed.

IS PROJECT...LOADED PROJECT, specify whether to make a new trakem2 project or use the one and only project already loaded in trakem2.

## Example

Below is an example of the inputs needed for the high-resolution script to get the outputs seen in the output folder. 

```
low resolution directory: OV 
high resolution directory:  NO 
Output directory: output 
project name: NO_test
Invert high resolution images: √
low resolution rescale factor: 1
octave_size: 500
Model_index: translation
using a windows machine: unchecked (if not using windows)
script previously run (alignment parameter saved in file) unchecked
Elastic Alignment: unchecked
Unorganized input: unchecked
```


