#!bin/bash

# In order to run: 
# Suppress the register commands in steps 8A and *B
# Change the "full/path_to/project_folder/*/ and the 
# full/path_to/automate_PET.py to match your settings. 

for i in /full/path_to/project_folder/*/  ; 
do python /full/path_to/automate_PET.py $i; 
done
