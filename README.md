## About
Two scripts to use subquentially for aligning low resolution images (low_res.py) and then high resolution images to the low resolution ones(high_res.py).

Additionally, a final_alignment.py script is provided to align all substacks (in the z-plane), for either low_res.py or high_res.py outputs.

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
The script can be dragged onto the ImageJ toolbar and this will open up of the script.
You can also open via the File>Open.. tab for ImageJ.

Once the script loaded, there is a 'Run' button on the bottom left. Pressing this button will prompt you with a menu of parameters to fill.

### Input
#### low_res.py

Below you have the parameter menu given to you for low_res.py. 
```
OV directory
Output directory
project name
Invert images
octave_size
Model_index
using a windows machine
run test(if OV has not been inverted)
```


OV DIRECTORY, The directory with all the images to be aligned. Image substacks are to be placed in sub directories. Image tiles are to be further placed in subsub directories. 

OUTPUT DIRECTORY, an empty directory where output images will be placed.

PROJECT NAME, chosen name for your Trackem2 project.

INVERT IMAGES, specify whether you would like your images inverted.
        
OCTAVE_SIZE, maximum image size(px). Default should be 1000.

MODEL_INDEX, choice of alignment between translation, rigid, similarity and affine.

USING A WINDOWS MACHINE, specify whether you are using a windows machine or not.

RUN TEST(IF OV HAS NOT BEEN INVERTED) specify whether you would like to run a test to check if alignment will work.

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
```


LOW RESOLUTION DIRECTORY, The directory with all the OV images to be aligned. Image substacks are to be placed in sub directories. Image tiles are to be further placed in subsub directories. 

HIGH RESOLUTION DIRECTORY, The directory with all the NO images to be aligned. Image substacks are to be placed in sub directories. Image tiles are to be further placed in subsub directories. 

OUTPUT DIRECTORY, an empty directory where output images will be placed.

PROJECT NAME, chosen name for your Trackem2 project.

INVERT HR IMAGES, specify whether you would like your high resolution images inverted.

RESCALE OV FACTOR, specify the magnitude difference between high and low resolution images. Default is 4, where high resolution images are 4 times more magnified than low resolution.
        
OCTAVE_SIZE, maximum image size(px). Default should be 1000.

MODEL_INDEX, choice of alignment between translation, rigid, similarity and affine.

USING A WINDOWS MACHINE, specify whether you are using a windows machine or not.

RUN TEST specify whether you would like to run a test to check if alignment will work.

#### final_alignment.py

Below you have the parameter menu given to you for final_alignment.py. 
```
directory
Output directory
project name
octave_size
Model_index
using a windows machine
```


DIRECTORY, The directory with all the images to be aligned. Image substacks are to be placed in sub directories. Image tiles are to be further placed in subsub directories. 

OUTPUT DIRECTORY, an empty directory where output images will be placed.

PROJECT NAME, chosen name for your Trackem2 project.
        
OCTAVE_SIZE, maximum image size(px). Default should be 1000.

MODEL_INDEX, choice of alignment between translation, rigid, similarity and affine.

USING A WINDOWS MACHINE, specify whether you are using a windows machine or not.
