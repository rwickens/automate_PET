#!bin/bash

# In order to run: 
# Suppress the register commands in steps 8A and 8B
# Customize the "full/path_to/project_folder/*/ and the 
# full/path_to/automate_PET.py to match your settings.
# This can be easily be done on terminal. 

for i in /full/path_to/project_folder/*/  ; 
do python /full/path_to/automate_PET.py $i; 
done
