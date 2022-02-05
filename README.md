# PET pipeline automation

Pipeline in Python for quantitative PET image processing on MINC files. 

This program assumes that the patient's MRI file has been spatially normalized on CIVET, and that the xfm files for this transformation have been kept.  

The steps that the pipeline achieves are: 

- (1) Averages a dynamic (multi-frame) PET scan into one static image 
- (2) Calculates the standardized uptake values based on weight and dose 
- (3) Autoregisters the PET file to the MRI file using mutual information and linear regression
- (4) Transforms the PET file into standard template (this requires certain xfm files from CIVET)
- (5) Takes the SUVR based on the reference region(s) of your choice (if multiple given, the mean is taken)
- (6) Blurs the image in the resolution(s) of your choice
- (7) Does steps 5 and 6 in patient-space by doing a reverse transformation of the mask/atlas file (necessarily in standard space)
- (8) If desired, split the initial dynamic PET scan into single frames for the purposes of examination. (This part of code needs to be un-commented to work.)


-----------INFORMATION FOR USER:----------- 
- One input to run the program: patient folder (full path needed)
- Example input to run program: python /home/minc/projectfolder/automate_PET.py /home/minc/projectfolder/patientfolder
- In this patient folder, you must have the PET file, IT file, TAL file, GRID file, and T1 file from CIVET, as well as a txt file containing two numbers separated by a space: weight of patient (kg) and dose (mCi) of radioactivity injected 
- The program searches for the above files with specific suffixes. The defaults are based on CIVET outputs. These are customizable in the JSON configuration file. 
- In the project directory, keep the JSON configuration file. In this file, you can change defaults (e.g, mask (reference tissue) used, standard template used), and suffixes for your file naming conventions.  
- If the JSON config is not present, program will look for WM mask file (WM_0.99_new.mnc) and MNI standard template file (mni_icbm152_t1_tal_nlin_sym_09c.mnc) in this project folder.
- Note: This program will overwrite files (if the file name of one of your ouputs already exists in that folder).   

----------------------------------------------

**Additional programs**: automate_mincstats and mincmorph. They each require a json file, samples provided. 
