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

Below you have the parameter menu given to you for low_res.py. 
```
Input directory
Output directory
project name
Invert images
octave_size
Model_index
using a windows machine
run test(if OV has not been inverted)
Elastic Alignment
Unorganized input
```


OV DIRECTORY, The directory with all the images to be aligned. Image substacks are to be placed in sub directories. Image tiles are to be further placed in subsub directories. 

OUTPUT DIRECTORY, an empty directory where output images will be placed.

PROJECT NAME, chosen name for your Trackem2 project.

INVERT IMAGES, specify whether you would like your images inverted.
        
OCTAVE_SIZE, maximum image size(px). Default should be 1000.

MODEL_INDEX, choice of alignment between translation, rigid, similarity and affine.

USING A WINDOWS MACHINE, specify whether you are using a windows machine or not.

RUN TEST(IF OV HAS NOT BEEN INVERTED) specify whether you would like to run a test to check if alignment will work.

ELASTIC ALIGNMENT, Specify whether you would like to elastically align the images.

UNORGANIZED INPUT, Specify whether you have SBEM info files present to correctly organize files for alignment.

#### high_res.py

Below you have the parameter menu given to you for high_res.py. 

```
low resolution directory
high resolution directory
Output directory
project name
Invert HR images
low resolution rescale factor
octave_size
Model_index
using a windows machine
run test(if your low resolution has not been rescaled)
Elastic Alignment
Unorganized input
```

LOW RESOLUTION DIRECTORY, The directory with all the low resolution images to be aligned. Image substacks are to be placed in sub directories. Image tiles are to be further placed in subsub directories. 

HIGH RESOLUTION DIRECTORY, The directory with all the high resolution images to be aligned. Image substacks are to be placed in sub directories. Image tiles are to be further placed in subsub directories. 

OUTPUT DIRECTORY, an empty directory where output images will be placed.

PROJECT NAME, chosen name for your Trackem2 project.

INVERT HR IMAGES, specify whether you would like your high resolution images inverted.

RESCALE OV FACTOR, specify the magnitude difference between high and low resolution images. Default is 4, where high resolution images are 4 times more magnified than low resolution.
        
OCTAVE_SIZE, maximum image size(px). Default should be 1000.

MODEL_INDEX, choice of alignment between translation, rigid, similarity and affine.

USING A WINDOWS MACHINE, specify whether you are using a windows machine or not.

RUN TEST specify whether you would like to run a test to check if alignment will work.

ELASTIC ALIGNMENT, Specify whether you would like to elastically align the images.

UNORGANIZED INPUT, Specify whether you have SBEM info files present to correctly organize files for alignment.

#### catmaid.py

Below you have the parameter menu given to you for final_alignment.py. 

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

#### examples

LOW RESOLUTION DIRECTORY, OV folder

HIGH RESOLUTION DIRECTORY, No folder

OUTPUT DIRECTORY, output folder

PROJECT NAME, NO_test

INVERT HR IMAGES, yes

RESCALE OV FACTOR, 1

OCTAVE_SIZE, maximum image size(px). 500

MODEL_INDEX, translation

USING A WINDOWS MACHINE, no (using mac)

RUN TEST, yes

ELASTIC ALIGNMENT, no

UNORGANIZED INPUT,no

