#!/usr/bin/python
# Rebekah Wickens, 2020
# Version 1.0.1

from pathlib import Path
from copy import deepcopy
import argparse
import subprocess
import sys
import os
from importlib import import_module
import json
import glob
import statistics

newest_minctools = max(glob.glob("/opt/minc/1.9.*"))
MINC_DIR = Path(newest_minctools)
DEFAULT_MINC_CONFIG = MINC_DIR / 'minc-toolkit-config.sh'
DEFAULT_MINC_BEST_LIN = MINC_DIR.joinpath('bin/bestlinreg_s')

parser = argparse.ArgumentParser('image processing inputs')
parser.add_argument('patient_folder')    

args = parser.parse_args()

def splice(path: Path, modifier, warning = False) -> Path:
    dir_name = str(os.path.dirname(path))
    base_name = str(os.path.basename(path))
    base_count = base_name.count(".")
    if base_count > 1:
        base_count_until_last = base_count-1 
        newbase = base_name.replace('.','-', base_count_until_last) 
        if warning == True:
            print("The names of the generated files will be slightly modified as such:", newbase, ". Periods other than the (assumed) file extension have been removed.")
        newbase = Path(newbase)
        dir_name = Path(dir_name)
        path = dir_name / newbase
    return path.parent.joinpath(path.stem + modifier).with_suffix(path.suffix)

def main(patient_folder):
    patient_code = str(os.path.basename(Path(patient_folder)))
    output_txt_file = patient_folder + '/_'+ patient_code + '_output_log.txt'
    command_log_file = patient_folder + '/_'+ patient_code + '_command_log.csv'
   
    with open(output_txt_file, 'w') as f:
        with open(command_log_file, 'w') as g:
                     
            def print_and_write(*my_tuple):
                if type(my_tuple) == str:
                    my_output = my_tuple
                elif type(my_tuple) == int or type(my_tuple) == float:
                    my_output = str(my_tuple)
                elif type(my_tuple) == tuple:
                    print_statement = [str(i) for i in my_tuple]
                    my_output = " ".join(print_statement)
                print(my_output + "\n")
                f.write(my_output + "\n")

            minc_cmd_dict = {}
            global minc_counter
            minc_counter = 0 
            
            def write_to_minc_dict(minc_command_list):
                global minc_counter
                minc_command_list = [str(c) for c in minc_command_list]
                minc_cmd_dict[minc_counter] = " ".join(minc_command_list)
                g.write("%s,%s\n"%(minc_counter,minc_cmd_dict[minc_counter]))
                #print_and_write("MINC COMMAND EXECUTED (#, command): %s,%s\n"%(minc_counter,[minc_cmd_dict[minc_counter]]))
                minc_counter += 1
            
            def bash_command(*args):
                bash_output = subprocess.check_output([str(c) for c in args], universal_newlines=True)
                write_to_minc_dict(args)
                print_and_write(str(bash_output))
                return bash_output

            def bash_command_shell(*args):
                bash_output_shell = subprocess.check_output(args, shell=True, universal_newlines=True, executable='/bin/bash')
                write_to_minc_dict(args)
                print_and_write(str(bash_output_shell))
                return bash_output_shell

            def ask_consent(recursion=False):
                if recursion == False:
                    warning_text = "WARNING! JSON file not detected by the program. It is supposed to be located at " + str(json_path) + " Have you changed its location or have you renamed the file to something other than config.json? \n Would you like the program to continue with the default settings (y/n)? "       
                elif recursion == True:
                    warning_text = "Would you like the program continue with the default settings (y/n)? "
                f.write(warning_text)
                user_choice = input(warning_text)
                if user_choice == 'Y' or user_choice ==  'y':
                    print_statement = "The user opted to use the defaults settings. "
                    print_and_write(print_statement)
                elif user_choice == 'N' or user_choice == 'n':
                    print_statement = "The user rejected using the defaults. \n Because no config.json file was detectable and the defaults were not selected, the program will now terminate."
                    print_and_write(print_statement)
                    sys.exit(0)
                else: 
                    print_statement = "Invalid response. Please enter 'y' or 'n'"
                    print(print_statement)
                    ask_consent(recursion=True)
            
            def check_file_structure(input_path_list, input_path_list_name, input_suffix, MRImessage = 0):
                if len(input_path_list) > 1:
                    print_and_write("Multiple", input_path_list_name, "files ending in suffix:","'"+ input_suffix +"'", 
                    ".Check that there are only one patient's files in this patient folder!")
                    if MRImessage == 1:
                        print_and_write("For example, did you check that only one, CIVET-processed, MRI file is in this folder (not raw MRI files?)")
                    sys.exit(0)
                elif len(input_path_list) == 0:  
                    print_and_write("No", input_path_list_name, "file found. Please check that your", input_path_list_name, 
                    "file ends in suffix:","'" + input_suffix + "'")
                    sys.exit(0)

            def grab_files_check_and_shorten(suffixlist, stringlist): 
                list_of_globfiles  = []
                for i in range(len(suffixlist)):
                    globlist = glob.glob(patient_folder + "/*" + suffixlist[i])
                    if suffixlist[i] == MRIsuffix: 
                        check_file_structure(globlist, stringlist[i], suffixlist[i], 1)
                    else:
                        check_file_structure(globlist, stringlist[i], suffixlist[i])
                    globfile = Path(globlist[0]) 
                    print_and_write(stringlist[i] + " file used:", globfile)
                    list_of_globfiles.append(globfile)
                tuple_of_globfiles = tuple(list_of_globfiles)
                return tuple_of_globfiles
            
            projectdir = Path(patient_folder).parent   
            print_and_write("Project folder used is:", projectdir)
            patient_dir = Path(patient_folder)
            print_and_write("Patient folder used is:", patient_dir)
            print_and_write("Patient code is:", patient_code)

            json_path = projectdir / 'config.json'
            print_and_write("Json path searched at:", json_path)
            
            if json_path.exists():
                config = json.load(json_path.open())
                PETsuffix = config['PET_SUFFIX']
                MRIsuffix = config['MRI_SUFFIX']
                talsuffix = config['TAL_SUFFIX']
                ITsuffix = config['IT_SUFFIX']
                weight_dose_suffix = config['WEIGHT_DOSE_SUFFIX']
                MNItemplatepath = config['MNI_TEMPLATE_PATH']
                mask_or_atlas_path = config['MASK_OR_ATLAS_PATH']
                should_mask_or_atlas_be_resampled = config['SHOULD_MASK_OR_ATLAS_BE_RESAMPLED']
                maskbinvalue = config['MASK_BIN_VALUE']
                mincconfigpath = config['MINC_CONFIG_PATH']
                mincbestlinregpath = config['MINC_BEST_LIN_REG_PATH']
                preferred_blur_list = config['PREFERRED_BLUR']
                perform_patient_space_analyses = config['PERFORM_PATIENT_SPACE_ANALYSES']
                show_images = config['SHOW_IMAGES']
            else:
                ask_consent()
                PETsuffix = "4D_MC01.mnc" 
                MRIsuffix = "_t1.mnc"   
                talsuffix = "t1_tal.xfm"
                ITsuffix = "_It.xfm"
                weight_dose_suffix = "weight_dose.txt"
                MNItemplatepath = projectdir / "mni_icbm152_t1_tal_nlin_sym_09c.mnc"
                mask_or_atlas_path = projectdir / "WM_0.99_new.mnc"
                should_mask_or_atlas_be_resampled = False
                maskbinvalue = [1]
                mincconfigpath = DEFAULT_MINC_CONFIG
                mincbestlinregpath = DEFAULT_MINC_BEST_LIN
                preferred_blur_list = [4,6,8]
                perform_patient_space_analyses = True
                show_images = True

            gridsuffix = "It_grid_0.mnc" #this is non-modifiable; Minc looks for this suffix. 

            print_and_write("Standard template file used:", MNItemplatepath, )
            print_and_write("Reference region mask or atlas file used:", mask_or_atlas_path)
            print_and_write("Reference region mask or atlas - will it be resampled:", should_mask_or_atlas_be_resampled)
            number_regions = bash_command('volume_stats', '-quiet', '-max', mask_or_atlas_path)
            print_and_write("The number of regions detected in the atlas is:", number_regions)
            print_and_write("Reference region mask or atlas - which maskbin (mask binary) values used:", maskbinvalue)
            print_and_write("Minc config file used:", mincconfigpath)
            print_and_write("Minc best lin reg file used:", mincbestlinregpath)
            print_and_write("Chosen FWHM blur(s), in mm:", preferred_blur_list)
            print_and_write("Perform patient-space analyses:", perform_patient_space_analyses)

            suffix_list = [PETsuffix, MRIsuffix, talsuffix, ITsuffix, gridsuffix, weight_dose_suffix]     
            string_list = ["PET", "MRI", "Tal", "IT", "Grid", "Weight_and_dose"]
            
            PETpath, MRIpath, talpath, ITpath, gridpath, weight_dose_path = grab_files_check_and_shorten(suffix_list, string_list) 
                        
            number_frames = bash_command('mincinfo', '-dimlength', 'time', PETpath)
            print_and_write("Number of time-frames extracted from PET file is", number_frames)

            e = open(weight_dose_path, 'r')
            list_contents = e.read().replace(",", "").split()
            weight, dose = float(list_contents[0]), float(list_contents[1])

            print_and_write("Weight inputted is (kg):", weight)
            print_and_write("Dose inputted is (mCi):", dose)
                      
            mylist = []
            xfmlist = []
            mylist.append(PETpath)
            outputPETpath = mylist[-1]
            outputPETpath_xfm = outputPETpath.with_suffix('.xfm')
            xfmlist.append(outputPETpath_xfm)

            """
            #0. Split the PET file into single frames - un-comment if this step is desired
            print_and_write("#0. Split the PET file into single frames")
            number_frames = int(number_frames)
            for t in range(number_frames):
                t = str(t)
                staticfile = patient_folder+"/_" + patient_code + "frame_{}.mnc".format(t)
                bash_command('mincreshape', '-clobber', '-dimrange', 'time=' + str(t), PETpath, staticfile)
            """
            """
            # 1. Change the file extension from .v to .mnc - un-comment if this step is desired
            # Needed if dealing with .v files - such as with FDG

            outputPETpath = PETpath.with_suffix('.mnc')
            mylist.append(outputPETpath)
            bash_command('ecattominc', '-short', PETpath, outputPETpath)
            """
            
            # 2. Average the PET frames
            
            print_and_write("# 2. Average the PET frames")
            outputPETpath = splice(outputPETpath, '_avg', True)
            mylist.append(outputPETpath)
            bash_command('mincaverage', '-clobber', mylist[-2], outputPETpath, '-avgdim', 'time')

            # 3. Take the SUV

            print_and_write("#3. Take the SUV")
            constant = dose * 1000 / weight
            print_and_write("dose * 1000 / weight  <----- constant to generate SUV's")
            print_and_write(dose, "* 1000 /", weight, "= ", constant)
            outputPETpath = splice(outputPETpath, "_suv")
            mylist.append(outputPETpath)
            bash_command('mincmath', '-clobber', '-div', mylist[-2], '-const', constant, outputPETpath)

            # 4. Automatic coregistration of subject PET to subject MRI to obtain .xfm files

            print_and_write("# 4. Automatic coregistration of subject PET to subject MRI to obtain .xfm files.\nGo take a coffee break! The next steps take a while to run.")
            outputPETpath_xfm = splice(outputPETpath_xfm, "_autoreg")
            xfmlist.append(outputPETpath_xfm)
            outputPETpath = splice(outputPETpath, "_autoreg")
            mylist.append(outputPETpath)
            bash_command_shell("source " + str(mincconfigpath))
            bash_command(mincbestlinregpath, '-clobber', '-nmi', '-lsq6', mylist[-2], MRIpath, outputPETpath_xfm, outputPETpath)
            mylist_patient = deepcopy(mylist)  # Divergence in image processing (template-space versus patient-space)
            
            # 5. Linear and non-linear transformations to put the PET file into MNI space (toST = to Standard Template)

            print_and_write("# 5. Linear and non-linear transformations to put the PET file into MNI space (toST = to Standard Template)")
            outputPETpath_xfm = splice(outputPETpath_xfm, '_toST').with_suffix('.xfm')
            xfmlist.append(outputPETpath_xfm)
            bash_command('xfmconcat', '-clobber', xfmlist[-2], talpath, ITpath, outputPETpath_xfm)
            outputPETpath = splice(outputPETpath, "_ST")
            mylist.append(outputPETpath)
            bash_command('mincresample', '-clobber', mylist[-3], '-like', MNItemplatepath, '-transform', outputPETpath_xfm,
                        outputPETpath)

            # 6A. Take the SUVR in MNIspace
                  
            print_and_write("# 6A. Take the SUVR in MNIspace")                 
            if should_mask_or_atlas_be_resampled == True:
                mask_or_atlas_resampled = patient_folder + "/_atlas_mask_resampled_" + patient_code + ".mnc "
                bash_command('mincresample', '-clobber', '-like', outputPETpath, '-nearest', mask_or_atlas_path, mask_or_atlas_resampled)
                mask_or_atlas_path = mask_or_atlas_resampled
          
            if len(maskbinvalue) == 1:
                maskbinvalue = maskbinvalue[0]
            else:
                maskbinvalue = str(tuple(maskbinvalue)).replace(" ", "").replace("(", "").replace(")", "")

            try: 
                mask_SUV = bash_command('mincstats', '-mask', mask_or_atlas_path, '-mask_binvalue', maskbinvalue, outputPETpath, '-mean')
            except:
                print_and_write("Did you resample the ref. region mask/atlas to match your PET file? You can do this on the JSON configuration file by setting MASK_OR_RESAMPLE_ATLAS equal to true")
                sys.exit(0)
            print_and_write("The raw output given by mincstats (in MNI-space) is:\n", mask_SUV)
            mask_SUV_split = mask_SUV.split()

            means_array = [float(mask_SUV_split[i]) for i in range(len(mask_SUV_split)) if i != 0 and mask_SUV_split[i-1] == 'Mean:']
            print_and_write("The mean(s) of the reference region mask areas (in MNI-space) are:", means_array)
            if 0.0 in means_array:
                print_and_write("The output for at least one of your reference region mask areas is 0.0, which means that the corresponding binvalue does not exist, or that the area is outside the skull/scalp")
                sys.exit(0)
            mask_SUV = statistics.mean(means_array)

            mask_SUV = str(mask_SUV)
            print_and_write("The extracted average of the mean(s) of the reference region mask area(s) (in MNI-space) is:", mask_SUV)
            outputPETpath = splice(outputPETpath, '_SUVR')
            mylist.append(outputPETpath)
            bash_command('mincmath', '-clobber', '-div', '-const', mask_SUV, mylist[-2], outputPETpath)
                
            # 7A. Blur the SUVR PET (in MNI-space) in select resolution(s) (default = 4, 6, and 8mm)
                    
            print_and_write("# 7A. Blur PET in select resolution(s) (default = 4, 6, and 8mm)")
            templist = []
            deepcopyPETpath = deepcopy(outputPETpath) 
            for i in preferred_blur_list:
                blur_word = "_" + str(i)
                outputPETpath = splice(deepcopyPETpath, blur_word).with_suffix('')
                outputPETpath_for_list = splice(outputPETpath, '_blur').with_suffix('.mnc')
                templist.append(outputPETpath_for_list)
                bash_command('mincblur', '-clobber','-fwhm', i, mylist[-1], outputPETpath)
            mylist = [*mylist, *templist]
            
            # 8A. Finished. Show the patient's SUVR PET image on MNI template
            
            if show_images == True:

                bash_command('register', mylist[-1], MNItemplatepath)

            if perform_patient_space_analyses == True:

                # 6B - Take the SUVR in patient space

                print_and_write("# 6B - Take the SUVR in patient space")
                PETsubjectmask = patient_folder + "/_" + patient_code + "_subject_mask.mnc"
                bash_command('mincresample', '-clobber', '-like', mylist_patient[-2], '-nearest', '-transform', outputPETpath_xfm, '-invert_transformation', mask_or_atlas_path, PETsubjectmask)
                mask_SUV_patient = bash_command('mincstats', '-mask', PETsubjectmask, '-mask_binvalue', maskbinvalue, mylist_patient[-2], '-mean')
                print_and_write("The raw output given by mincstats (in patient-space) is:\n", mask_SUV_patient)

                mask_SUV_patient_split = mask_SUV_patient.split()

                means_array_patient = [float(mask_SUV_patient_split[i]) for i in range(len(mask_SUV_patient_split)) if i != 0 and mask_SUV_patient_split[i-1] == 'Mean:']

                print_and_write("The mean(s) of the reference region mask area(s) are (in patient-space):", means_array_patient)
                mask_SUV_patient = statistics.mean(means_array_patient)
                print_and_write("The extracted average of the means(s) of the reference region area(s) (in patient-space) is:", mask_SUV_patient)
                outputPETpath_patient = splice(mylist_patient[-1], '_patient_SUVR')
                mylist_patient.append(outputPETpath_patient)
                bash_command('mincmath', '-clobber', '-div', '-const', mask_SUV_patient, mylist_patient[-2], outputPETpath_patient)

                #This is a check to see that radioactivity in patient-space matches that of MNI-space to ensure transformations were done correctly:
            
                percent_mask_difference = abs(float(mask_SUV) - float(mask_SUV_patient))/float(mask_SUV_patient)*100
                print_and_write("% Mask radioactivity difference (template versus patient-space):", percent_mask_difference)  
                
                if percent_mask_difference > 2:
                    print_and_write("WARNING! The reference region values in patient-space versus MNI-space seem to differ more than 2%! This could mean that transformations were incorrectly applied.")
                else:
                    print_and_write("Test passed. Minimal percentage difference between reference region radioactivity in template- and patient-space.")

                # 7B. Blur SUVR image in patient space in select resolution(s) (default = 4, 6, and 8mm)
                
                print_and_write("# 7B. Blur patient space PET in select resolution(s) (default = 4, 6, and 8mm)")
                templist_patient = []
                deepcopyPETpath_patient = deepcopy(outputPETpath_patient)
                for i in preferred_blur_list: 
                    blur_word_patient = "_" + str(i)           
                    outputPETpath_patient = splice(deepcopyPETpath_patient, blur_word_patient).with_suffix('')
                    outputPETpath_patient_for_list = splice(outputPETpath_patient, '_blur').with_suffix('.mnc')
                    templist_patient.append(outputPETpath_patient_for_list)
                    bash_command('mincblur', '-clobber', '-fwhm', i, mylist_patient[-1], outputPETpath_patient)
                mylist_patient = [*mylist_patient, *templist_patient]

                #8B. Show patient's SUVR PET image in their MRI space  
            
                if show_images == True:
                    bash_command('register', mylist_patient[-1], MRIpath)
            
main(**vars(args))