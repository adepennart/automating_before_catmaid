/*
 * Macro template to process multiple images in a folder
 */
#@ File (label = "Template", style = "file") template
#@ File (label = "Input directory", style = "directory") input
#@ File (label = "Output directory", style = "directory") inverted
#@ String (label = "File suffix", value = ".tif") suffix
#@ boolean (label = "Don't invert images") inverted_image

// doesn't check if empty folders, overwrites?
//changing of the name is only correct the first time through

// See also Process_Folder.py for a version of this code
// in the Python scripting language.


print(inverted);
//if (matches(title, ".*[AB]\\.[jJ][pP]e*[gG]$")) {setThreshold(146.0000, 255.0000);}

print("output is 'inverted'");
if (inverted_image == 0){
File.openSequence(input, "virtual");
Input=getTitle();

run("Virtual Stack...", "output="+inverted+" output_format=TIFF text1=run(\"Invert\");\n");
new_input=getTitle();
print(new_input);
close(Input);
}else{
File.openSequence(input, "virtual");
new_input=getTitle();
}
open(template);
Template=getTitle();
//Select
//File.openSequence(output, "virtual");
//new_input=getTitle();
print(Template);
print(new_input);
run("Template Matching Image", "template=["+Template+"] image="+new_input+" rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
 selectWindow("Results");
Table.sort("Score");

value=getValue("results.count");
print(value);
//Table.setSelection(value-1, value-1);
//Array.getSequence(n);
how=Table.setSelection(value-1, value-1);
print(how);
//selected=String.copyResults;
//String.copyResults;
//print(selected)
String.copyResults;
selected=String.paste;
//run("Paste");
print(selected);
headings = split(selected,"\t");
//print(headings)
Array.print(headings);

for (a=0; a<lengthOf(headings); a++)
    if (a == 1){
    	print(headings[a]);
//    	open(inverted+"/"+headings[a]);
//		selectWindow(headings[a]);
		Stack.setPosition(inverted, headings[a],1);
		image_title=headings[a];
		image_title_2=image_title.replace(".tif", "");
		print(image_title);
    }
    else if (a == 2){
    	setSlice(headings[a]);
    	}

selectWindow(Template);
match=getBoolean("Confirm Match?");
if (match == 0){
	print("No match");
} else {
	print("Match");	
	// choose neuropil name, doesn't remove first .tif
	File.rename(inverted+"/"+image_title, inverted+"/"+image_title_2+"_neuropil_start.tif");
}

//selectImage(id);
//run("Set Slice...");

//Stack.setSlice(n);
//Stack.setPosition(inverted, headings[a]);
//label
//
//best=getResult("Image");
//print(best);
//setOption("CopyHeaders", true);
//String.copyResults
//run("Paste");
//getResult("Column", row);
//List.get(key);
//Result
//String.copyResults -;
//processFile(Template, new_input);

//got to no use global variables
//function processFile(input, output) {
function processFile(neuropil, overview ) {
	// Do the processing here by adding your own code.
	print("Processing: " + overview );
	//run("Template Matching Image", "template=[Screen Shot 2022-07-11 at 3.18.09 PM.png] image=screenshots rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
//	run("Template Matching Image", "template=[Template] image=new_input rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
//    run("Template Matching Image", "template=[Template] image=[Template] rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
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
