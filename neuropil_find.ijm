//will have to male the photos align with the "is matching question"

/*
 * Macro template to process multiple images in a folder
 */
//#@ File (label = "Template", style = "file") Template
#@ File (label = "Template", style = "directory") template
#@ File (label = "Input directory", style = "directory") input
#@ File (label = "Output directory", style = "directory") inverted
#@ String (label = "File suffix", value = ".tif") suffix
#@ boolean (label = "Don't invert images") inverted_image
#@ int (label = "all image reduction", value=1, min=0, max=10, style=slider ) reduce
#@ int (label = "overview size", value=1, min=0, max=40, style=slider ) ov_size
#@ int (label = "neuropil size", value=1, min=0, max=40, style=slider  ) neu_size
//https://imagej.net/imagej-wiki-static/Macros
//invert template
//doesn't show first image, whether invereted or not
// doesn't check if empty folders, overwrites?
//changing of the name is only correct the first time through
// should check if files already present so doesn't have to reload
// need to look at the pictures in low quality
//virtual stack, all images are set to same pixel dimensions
//confirm match title could be nice if it asked which ROI is in question
// rename to specifc neuropil when match is confirmed

// See also Process_Folder.py for a version of this code
// in the Python scripting language.


//print(inverted);

//print("output is 'inverted'");
if (inverted_image == 0){
	run("Image Sequence...", "select="+input+" dir="+input+" sort use");
	Input=getTitle();
	run("Virtual Stack...", "output="+inverted+" output_format=TIFF text1=run(\"Invert\");\n");
	new_input=getTitle();
//	print(new_input);
	close(Input);
}else{
	File.openSequence(input, "virtual");
	new_input=getTitle();
}
//open(template);
//File.openSequence(template, "virtual");
//Template=getTitle();
//templaten=nSlices;
//print(Template);
//print(new_input);
//selectWindow(new_input);
//selectWindow(Template);
//	input
selectWindow(new_input);
getDimensions(width, height, channels, slices, frames);
print("   width: "+width);
width=width/(reduce);
print("   width: "+width);
height=height/(reduce);
run("Size...", "width="+width+ " height="+height+" depth="+slices+" constrain average interpolation=Bilinear");
//run("Threshold...");
//	run("32-bit");
//	setThreshold(2.0000, 1000000000000000000000000000000.0000);
//	run("NaN Background");
//selectWindow(new_input);
//run("32-bit");
//run("Virtual Stack...", "output_format=TIFF text1=[//run(\"Threshold...\");\nsetThreshold(2.0000, 1000000000000000000000000000000.0000);\nrun(\"NaN Background\");\n]");

print(template);
filelist = getFileList(template);
Array.print(filelist);
for (i = 0; i <= lengthOf(filelist)-1; i++) {
//    if (endsWith(filelist[i], ".tif")) { 
	open(template + File.separator + filelist[i]);
//    } 
//	selectWindow(Template);
	selectWindow(filelist[i]);
	print(i);
//    setSlice(i);
	ratio=neu_size/ov_size;
//	template
	getDimensions(width, height, channels, slices, frames);
	print("   width: "+width);
	width=width/(ratio*reduce);
	print("   width: "+width);
	height=height/(ratio*reduce);
	run("Size...", "width="+width+ " height="+height+" depth=1 constrain average interpolation=Bilinear");
//	run("32-bit");
	run("Template Matching Image", "template=["+filelist[i]+"] image="+new_input+" rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
}
//for (i = 1; i <= templaten; i++) {
//	selectWindow(Template);
//    setSlice(i);
//    print(i);

    //have to change depth
	//run("Size...", "width=500 height=10 depth=4 constrain average interpolation=Bilinear");
//    run("Template Matching Image", "template=["+Template+"] image="+new_input+" rotate=[] matching_method=[Normalised 0-mean cross-correlation] number_of_objects=1 score_threshold=0.5 maximal_overlap=0.4 add_roi show_result");
    // do something here;
//    getBoolean("debugging. continue?");
//}

 selectWindow("Results");
Table.sort("Score");

value=getValue("results.count");
print(value);
//how=Table.setSelection(value-1, value-1);
//print(how);
//print(selected)
String.copyResults;
selected=String.paste;
//print(selected);
fulltable = split(selected,"\n");
//Array.print(fulltable);

for (a=0; a<lengthOf(fulltable); a++){
	headings=fulltable[a];
//	print(headings);
	item = split(headings,"\t");
	Array.print(item);
	for (i = 0; i < lengthOf(item); i++) {
		if (i == 1){
//	    	print(item[i]);
	    	image_title=item[i];
	//		Stack.setPosition(inverted, headings[a],1);
	//		image_title=headings[a];
	//		image_title_2=image_title.replace(".tif", "");
	//		print(image_title);
    	}
    	if (i == 2){
//	    	print(item[i]);
	    	stack_pos=item[i];
	//		Stack.setPosition(inverted, headings[a],1);
	//		image_title=headings[a];
	//		image_title_2=image_title.replace(".tif", "");
	//		print(image_title);
    	}
    	if (i == 3){
//	    	print(item[i]);
	    	temp_title=item[i];
	//		Stack.setPosition(inverted, headings[a],1);
	//		image_title=headings[a];
	//		image_title_2=image_title.replace(".tif", "");
	//		print(image_title);
    	}
		if (i == 4){
//			print(item[i]);
//			print(image_title);
	    	if (item[i] == "1.000"){
	    		print(new_input,image_title);
	    		Stack.setPosition(new_input, stack_pos,1);
	    		
	    		image_title_2=image_title.replace(".tif", "");
//	    		selectWindow(Template);
	    		selectWindow(temp_title);
//	    		Stack.setPosition(Template, stack_pos,1);
				match=getBoolean("Confirm Match?");
				if (match == 0){
					print("No match");
				} else {
					print("Match");	
					// choose neuropil name, doesn't remove first .tif
					File.rename(inverted+"/"+image_title, inverted+"/"+image_title_2+temp_title+".tif");
				}
	    	}
		}
	}
}



   


//
//for (a=0; a<lengthOf(headings); a++)
//    if (a == 1){
//    	print(headings[a]);
//		Stack.setPosition(inverted, headings[a],1);
//		image_title=headings[a];
//		image_title_2=image_title.replace(".tif", "");
//		print(image_title);
//    }
//    else if (a == 2){
//    	setSlice(headings[a]);
//    	}
//
//selectWindow(Template);
//match=getBoolean("Confirm Match?");
//if (match == 0){
//	print("No match");
//} else {
//	print("Match");	
//	// choose neuropil name, doesn't remove first .tif
//	File.rename(inverted+"/"+image_title, inverted+"/"+image_title_2+"_neuropil_start.tif");
//}

//processFile(Template, new_input);

function processFile(neuropil, overview ) {
	// Do the processing here by adding your own code.
	print("Processing: " + overview );
}

