# Automate PET - Bedard lab

My name is Rebekah Wickens, and I am a PhD student of Marc-Andre Bedard (Montreal Neurological Institute).
I've written a pipeline in Python for quantitative PET image processing on MINC files. This program assumes that one has processed the MRI files on CIVET and have generated files for transformation to standard space. 

The steps accomplished are: 

- (1) Averages a dynamic (multi-frame) PET scan into one static image 
- (2) Calculates the standardized uptake values based on weight and dose 
- (3) Autoregisters the PET file to the MRI file
- (4) Transforms the PET file into standard template
- (5) Takes the SUVR based on the reference region(s) of your choice (if multiple given, mean is taken)
- (6) Blurs the image in the resolution(s) of your choice
- (7) Does steps 5 and 6 in patient-space by doing a reverse transformation of the mask/atlas file (necessarily in standard space)
- (8) If desired, can split the initial dynamic PET scan into frames for the purposes of examination. (Section needs to be un-commented)

The following is the information for the user. 

-----------INFORMATION FOR USER:----------- 
- Three inputs to run the program: weight (kg), dose (mCi), and patient folder (full path needed)
- Example input to run program: python /home/minc/projectfolder/automate_PET.py 102 8.4 /home/minc/projectfolder/patientfolder
- Assumes you are in a project directory containing patients' folders.
- In this patient folder, you must have the IT file, TAL file, GRID file, and T1 file from CIVET,
- In the project directory, keep the json configuration file. In this file, you can change defaults (e.g, mask (reference tissue) used, standard template used) 
- If the json config is not present, program will look for WM mask file (WM_0.99_new.mnc) and MNI standard template file (mni_icbm152_t1_tal_nlin_sym_09c.mnc) in this project folder.
- Note: This program will overwrite files (if the file name of one of your ouputs already exists in that folder).   
