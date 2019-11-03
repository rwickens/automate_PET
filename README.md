# Automate PET - Bedard lab

My name is Rebekah Wickens. I'm a PhD student of Marc-Andre Bedard (Montreal Neurological Institute). 

I've written a pipeline in Python for quantitative PET image processing on MINC files. 

This program assumes that the MRI file inputted has been spatially normalized, and that the xfm files for this transformation have been kept.  

The steps that the pipeline achieves are: 

- (1) Averages a dynamic (multi-frame) PET scan into one static image 
- (2) Calculates the standardized uptake values based on weight and dose 
- (3) Autoregisters the PET file to the MRI file using linear regression
- (4) Transforms the PET file into standard template (this requires certain xfm files from CIVET)
- (5) Takes the SUVR based on the reference region(s) of your choice (if multiple given, the mean is taken)
- (6) Blurs the image in the resolution(s) of your choice
- (7) Does steps 5 and 6 in patient-space by doing a reverse transformation of the mask/atlas file (necessarily in standard space)
- (8) If desired, split the initials dynamic PET scan into single frames for the purposes of examination. (This part of code needs to be un-commented to work.)


-----------INFORMATION FOR USER:----------- 
- Three inputs to run the program: weight (kg), dose (mCi), and patient folder (full path needed)
- Example input to run program: python /home/minc/projectfolder/automate_PET.py 102 8.4 /home/minc/projectfolder/patientfolder
- Assumes you are in a project directory containing patients' folders.
- In this patient folder, you must have the IT file, TAL file, GRID file, and T1 file from CIVET.
- The program searches for files with specific suffixes. The defaults are based on CIVET outputs. These are customizable in the JSON configuration file. 
- In the project directory, keep the JSON configuration file. In this file, you can change defaults (e.g, mask (reference tissue) used, standard template used), and suffixes for your file naming conventions.  
- If the JSON config is not present, program will look for WM mask file (WM_0.99_new.mnc) and MNI standard template file (mni_icbm152_t1_tal_nlin_sym_09c.mnc) in this project folder.
- Note: This program will overwrite files (if the file name of one of your ouputs already exists in that folder).   
