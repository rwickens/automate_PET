# Automate PET - Bedard lab

My name is Rebekah Wickens, and I am a PhD student in Marc-Andre Bedard's lab (Montreal Neurological Institute)
This is some of my work towards automating the Bedard lab's PET image processing pipeline

For the automate_PET.py program, the following is the information for the user. 

-----------INFORMATION FOR USER:----------- 
- Three inputs to run the program: weight (kg), dose (mCi), and patient folder (full path needed)
- Example input to run program: python /home/minc/projectfolder/automate_PET.py 102 8.4 /home/minc/projectfolder/patientfolder
- Assumes you are in a project directory containing patients' folders.
- In this patient folder, you must have the IT file, TAL file, GRID file, and T1 file from CIVET,
- In the project directory, keep the json configuration file. In this file, you can change defaults (e.g, mask (reference tissue) used, standard template used) 
- If the json config is not present, program will look for WM mask file (WM_0.99_new.mnc) and MNI standard template file (mni_icbm152_t1_tal_nlin_sym_09c.mnc) in this project folder.
- Note: This program will overwrite files (if the file name of one of your ouputs already exists in that folder).   
