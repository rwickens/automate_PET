#!bin/bash

# In order to run: 
# Customize the "full/path_to/project_folder/*/ and the 
# full/path_to/automate_PET.py to match your settings.
# Also, this script can be easily run on terminal. 

for i in /full/path_to/project_folder/*/  ; 
do python /full/path_to/automate_PET.py $i; 
done
