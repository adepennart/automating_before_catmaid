/*
 * Macro template to process multiple images in a folder
 */
// #@ File (label = "Template", style = "file") template
#@ File (label = "Template", style = "file") template
#@ File (label = "Input directory", style = "directory") input
#@ File (label = "Output directory", style = "directory") output
#@ String (label = "File suffix", value = ".tif") suffix
// See also Process_Folder.py for a version of this code
// in the Python scripting language.

processFolder(input);

// function to scan folders/subfolders/files to find files with correct suffix
function processFolder(input) {
	list = getFileList(input);
	list = Array.sort(list);
	for (i = 0; i < list.length; i++) {
		if(File.isDirectory(input + File.separator + list[i]))
			processFolder(input + File.separator + list[i]);
		if(endsWith(list[i], suffix))
			processFile(input, output, list[i]);
	}
}

function processFile(input, output, file) {
	// Do the processing here by adding your own code.
	print("Processing: " + input + File.separator + file);
	run("Template Matching Image", "template=[/Users/Auguste/Desktop/Screen Shot 2022-07-11 at 3.18.09 PM.png] image=[/Users/Auguste/Desktop/ex_image_stack/screenshots/] rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
	// Leave the print statements until things work, then remove them.
	print("Saving to: " + output);
}

// open("/Users/Auguste/Desktop/Screen Shot 2022-07-11 at 3.18.09 PM.png");
// File.openSequence("/Users/Auguste/Desktop/ex_image_stack/screenshots/", "virtual");
// run("Template Matching Image", "template=[Screen Shot 2022-07-11 at 3.18.09 PM.png] image=screenshots rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
// saveAs("Results", "/Users/Auguste/Desktop/ex_image_stack/Results.csv");
// close("Results");
// roiManager("Discard");
// selectWindow("Screen Shot 2022-07-11 at 3.18.09 PM.png");
// showMessage("message");
