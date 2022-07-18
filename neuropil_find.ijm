/*
 * Macro template to process multiple images in a folder
 */
#@ File (label = "Template", style = "file") template
#@ File (label = "Input directory", style = "directory") input
#@ File (label = "Output directory", style = "directory") output
#@ String (label = "File suffix", value = ".tif") suffix
// See also Process_Folder.py for a version of this code
// in the Python scripting language.


//print(Template);
//if (matches(title, ".*[AB]\\.[jJ][pP]e*[gG]$")) {setThreshold(146.0000, 255.0000);}

print(output)

File.openSequence(input, "virtual");
Input=getTitle();

run("Virtual Stack...", "output=[output] output_format=TIFF text1=run(\"Invert\");\n");
new_input=getTitle();
print(new_input)
close(Input)

open(template);
Template=getTitle();

//File.openSequence(output, "virtual");
//new_input=getTitle();

run("Template Matching Image", "template=[Template] image=[Template] rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");

//processFile(Template, new_input);

//got to no use global variables
//function processFile(input, output) {
function processFile(neuropil, overview ) {
	// Do the processing here by adding your own code.
	print("Processing: " + overview );
	//run("Template Matching Image", "template=[Screen Shot 2022-07-11 at 3.18.09 PM.png] image=screenshots rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
//	run("Template Matching Image", "template=[Template] image=new_input rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
    run("Template Matching Image", "template=[Template] image=[Template] rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
//	saveAs("Results", "/Users/Auguste/Desktop/ex_image_stack/Results.csv");
	// Leave the print statements until things work, then remove them.
//	print("Saving to: " + output);
}

// open("/Users/Auguste/Desktop/Screen Shot 2022-07-11 at 3.18.09 PM.png");
// File.openSequence("/Users/Auguste/Desktop/ex_image_stack/screenshots/", "virtual");
// run("Template Matching Image", "template=[Screen Shot 2022-07-11 at 3.18.09 PM.png] image=screenshots rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
// saveAs("Results", "/Users/Auguste/Desktop/ex_image_stack/Results.csv");
// close("Results");
// roiManager("Discard");
// selectWindow("Screen Shot 2022-07-11 at 3.18.09 PM.png");
// showMessage("message");
