#!/usr/bin/python
# Rebekah Wickens, 2020
# Version 1.0.1

from pathlib import Path
from copy import deepcopy
import argparse
import subprocess
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

def splice(path: Path, modifier) -> Path:
    dir_name = str(os.path.dirname(path))
    base_name = str(os.path.basename(path))
    base_count = base_name.count(".")
    if base_count > 1:
        base_count_until_last = base_count-1 
        newbase = base_name.replace('.','-', base_count_until_last)
        print("Your file names will be named ---", newbase, "--- Extra periods '.' have been removed.")
        newbase = Path(newbase)
        dir_name = Path(dir_name)
        path = dir_name / newbase
    return path.parent.joinpath(path.stem + modifier).with_suffix(path.suffix)

def main(patient_folder):
#def main(weight, dose, patient_folder):
    
    patient_code = str(os.path.basename(patient_folder))
    output_txt_file = patient_folder + '/_output_log_' + patient_code + '.txt'
    command_log_file = patient_folder + '/_'+ patient_code + '_command_log.csv'
   
    minc_cmd_dict = {}
    global minc_counter
    minc_counter = 0 

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

            def write_to_minc_dict(minc_command_list):
                global minc_counter
                minc_command_list = [str(c) for c in minc_command_list]
                minc_cmd_dict[minc_counter] = " ".join(minc_command_list)
                g.write("%s,%s\n"%(minc_counter,minc_cmd_dict[minc_counter]))
                minc_counter += 1
            
            projectdir = Path(patient_folder).parent   
            print_and_write("Project folder used is:", projectdir)
            patient_dir = Path(patient_folder)
            print_and_write("Patient folder used is:", patient_dir)

            json_path = projectdir / 'config.json'
            print_and_write("json config file used is:", json_path)

            if json_path.exists():
                config = json.load(json_path.open())
                PETsuffix = config['PET_SUFFIX']
                MRIsuffix = config['MRI_SUFFIX']
                talsuffix = config['TAL_SUFFIX']
                ITsuffix = config['IT_SUFFIX']
                weight_dose_suffix = config['WEIGHT_DOSE_SUFFIX']
                MNItemplatepath = config['MNI_TEMPLATE_PATH']
                mask_or_atlas_path = config['MASK_OR_ATLAS_PATH']
                maskbinvalue = config['MASK_BIN_VALUE']
                mincconfigpath = config['MINC_CONFIG_PATH']
                mincbestlinregpath = config['MINC_BEST_LIN_REG_PATH']
                preferred_blur_list = config['PREFERRED_BLUR']
            else:
                print_and_write("WARNING: json file not detected so going with defaults (MNI 152, WM_0.99 mask)")
                PETsuffix = "4D_MC01.mnc" 
                MRIsuffix = "_t1.mnc"   
                talsuffix = "t1_tal.xfm"
                ITsuffix = "_It.xfm"
                weight_dose_suffix = "weight_dose.txt"
                MNItemplatepath = projectdir / "mni_icbm152_t1_tal_nlin_sym_09c.mnc"
                mask_or_atlas_path = projectdir / "WM_0.99_new.mnc"
                maskbinvalue = [1]
                mincconfigpath = DEFAULT_MINC_CONFIG
                mincbestlinregpath = DEFAULT_MINC_BEST_LIN
                preferred_blur_list = [4,6,8]
            
            PETpath = []
            MRIpath = []
            talpath = []
            ITpath = []
            gridpath = []
            weight_dose_path = []

            PETpath = glob.glob(patient_folder + "/*" + PETsuffix)
            MRIpath = glob.glob(patient_folder + "/*" + MRIsuffix)
            talpath = glob.glob(patient_folder + "/*" + talsuffix)
            ITpath = glob.glob(patient_folder + "/*" + ITsuffix)
            gridpath = glob.glob(patient_folder + "/*It_grid_0.mnc")
            weight_dose_path = glob.glob(patient_folder + "/*" + weight_dose_suffix)

            print_and_write("PET file used:", PETpath)
            print_and_write("MRI file used:", MRIpath)
            print_and_write("Tal file used:", talpath)
            print_and_write("IT file used:", ITpath)
            print_and_write("Grid file used:", gridpath)
            print_and_write("Weight and dose file used:", weight_dose_path)

            if len(gridpath) == 0: 
                print_and_write("No grid file detected! Minc will likely raise an error about this during the transformations.")
            elif Path(gridpath[0]).parent != (Path(talpath[0]).parent or Path(ITpath[0]).parent) :
                print_and_write("Your grid file needs to be in the same folder as the TAL and IT files (CIVET)! This is likely to cause a problem later during the transformation stage")
            
            def check_file_structure(input_path, input_suffix, MRImessage = 0):
                if len(input_path) > 1:
                    print_and_write("Multiple", input_path, "files ending in", input_suffix, ". Check that there are only one patient's files in this patient folder!")
                    if MRImessage == 1:
                        print_and_write("Did you check that only one CIVET MRI file is in this folder (not raw MRI files?")
                    raise SystemExit(0)
                elif len(input_path) == 0: 
                    print_and_write("No file found. Please check that your", input_path, "ends in", input_suffix)
                    raise SystemExit(0)
            
            check_file_structure(PETpath,PETsuffix)
            check_file_structure(MRIpath, MRIsuffix, 1)
            check_file_structure(talpath, talsuffix)
            check_file_structure(ITpath, ITsuffix)
            check_file_structure(weight_dose_path, weight_dose_suffix)

            PETpath = Path(PETpath[0])
            MRIpath = Path(MRIpath[0])
            talpath = Path(talpath[0])
            ITpath= Path(ITpath[0])
            weight_dose_path = Path(weight_dose_path[0])

            e = open(weight_dose_path, 'r')
            list_contents = e.read().split()
            weight = float(list_contents[0])
            dose = float(list_contents[1])

            print_and_write("Weight inputted is (kg):", weight)
            print_and_write("Dose inputted is (mCi):", dose)
            
            def bash_command(*args):
                global minc_counter
                bash_output = subprocess.check_output([str(c) for c in args], universal_newlines=True)
                write_to_minc_dict(args)
                print_and_write(str(bash_output))

            def bash_command_shell(*args):
                global minc_counter
                bash_output_shell = subprocess.check_output(args, shell=True, universal_newlines=True, executable='/bin/bash')
                write_to_minc_dict(args)
                print_and_write(str(bash_output_shell))
            
            mylist = []
            xfmlist = []
            mylist.append(PETpath)
            outputPETpath = mylist[-1]
            outputPETpath_xfm = outputPETpath.with_suffix('.xfm')
            xfmlist.append(outputPETpath_xfm)
            
            """
            #0. Split the PET file into single frames - un-comment if this step is desired
            
            number_frames_subprocess = ['mincinfo', '-dimlength', 'time', str(PETpath)]
            number_frames = subprocess.check_output(number_frames_subprocess, universal_newlines = True)
            print_and_write("number of time frames extracted is", number_frames)
            write_to_minc_dict(number_frames_subprocess)
            number_frames = int(number_frames)
            staticfiles = []
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

            outputPETpath = splice(outputPETpath, '_avg')
            mylist.append(outputPETpath)
            bash_command('mincaverage', '-clobber', mylist[-2], outputPETpath, '-avgdim', 'time')

            # 3. Take the SUV

            constant = dose * 1000 / weight
            print_and_write("dose * 1000 / weight")
            print_and_write(dose, "* 1000 /", weight, "= ", constant)
            outputPETpath = splice(outputPETpath, "_suv")
            mylist.append(outputPETpath)
            print("Go take a coffee break! The next steps take several minutes to run.")
            bash_command('mincmath', '-clobber', '-div', mylist[-2], '-const', constant, outputPETpath)

            # 4. Automatic coregistration of subject PET to subject MRI to obtain .xfm files

            outputPETpath_xfm = splice(outputPETpath_xfm, "_autoreg")
            xfmlist.append(outputPETpath_xfm)
            outputPETpath = splice(outputPETpath, "_autoreg")
            mylist.append(outputPETpath)
            bash_command_shell("source " + str(mincconfigpath))
            bash_command(mincbestlinregpath, '-clobber', '-nmi', '-lsq6', mylist[-2], MRIpath, outputPETpath_xfm, outputPETpath)
            mylist_patient = deepcopy(mylist)  # Divergence in image processing (template space versus patient space)
            
            # 5. Linear and non-linear transformations to put the PET file into MNI space (toST = to Standard Template)
            
            outputPETpath_xfm = splice(outputPETpath_xfm, '_toST').with_suffix('.xfm')
            xfmlist.append(outputPETpath_xfm)
            bash_command('xfmconcat', '-clobber', xfmlist[-2], talpath, ITpath, outputPETpath_xfm)
            outputPETpath = splice(outputPETpath, "_ST")
            mylist.append(outputPETpath)
            bash_command('mincresample', '-clobber', mylist[-3], '-like', MNItemplatepath, '-transform', outputPETpath_xfm,
                        outputPETpath)

            # 6A. Take the SUVR in MNIspace      
            #think about whether we want this resampling to be done
            """
            number_regions_subprocess = ['volume_stats', '-quiet', '-max', mask_or_atlas_path]
            number_regions = subprocess.check_output(number_regions_subprocess, universal_newlines = True)
            print_and_write("The number of regions in the atlas is", number_regions)
            write_to_minc_dict(number_regions_subprocess)
            if int(number_regions) > 1:
                mask_or_atlas_resampled = patient_folder + "/_atlas_mask_resampled_" + patient_code + ".mnc "
                bash_command('mincresample', '-clobber', '-like', outputPETpath, '-nearest', mask_or_atlas_path, mask_or_atlas_resampled)
                mask_or_atlas_path = mask_or_atlas_resampled
            """
            if len(maskbinvalue) == 1:
                maskbinvalue = maskbinvalue[0]
            else:
                minicsv = ""
                counter = 0
                for i in maskbinvalue:
                    counter += 1
                    i = str(i)
                    minicsv += i
                    if counter != len(maskbinvalue):
                        minicsv += ","
                print_and_write("minicsv is:", minicsv)
                maskbinvalue = minicsv

            mask_SUV_subprocess = ['mincstats', '-mask', str(mask_or_atlas_path), '-mask_binvalue', str(maskbinvalue), str(outputPETpath), '-mean']
            mask_SUV = subprocess.check_output(mask_SUV_subprocess, universal_newlines = True)
            write_to_minc_dict(mask_SUV_subprocess)
            print_and_write("the raw output given by mincstats in MNI-space is", mask_SUV)
            mask_SUV_split = mask_SUV.split()

            means_array = [float(mask_SUV_split[i]) for i in range(len(mask_SUV_split)) if i != 0 and mask_SUV_split[i-1] == 'Mean:']

            print_and_write("The mean or means of the mask in MNI-space are", means_array)
            mask_SUV = statistics.mean(means_array)
            mask_SUV = str(mask_SUV)
            print_and_write("The extracted average of the mask (reference region) section(s) in MNI-space is", mask_SUV)
            outputPETpath = splice(outputPETpath, '_SUVR')
            mylist.append(outputPETpath)
            bash_command('mincmath', '-clobber', '-div', '-const', mask_SUV, mylist[-2], outputPETpath)
                
            # 7A. Blur PET in select resolution(s) (default = 4, 6, and 8mm)
                    
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
            
            bash_command('register', mylist[-1], MNItemplatepath)

            # 6B - Take the SUVR in patient space
            
            PETsubjectmask = patient_folder + "/_subject_mask_" + patient_code + ".mnc"
            bash_command('mincresample', '-clobber', '-like', mylist_patient[-2], '-nearest', '-transform', outputPETpath_xfm, '-invert_transformation', mask_or_atlas_path, PETsubjectmask)
            mask_SUV_patient_subprocess = ['mincstats', '-mask', str(PETsubjectmask), '-mask_binvalue', str(maskbinvalue), str(mylist_patient[-2]), '-mean']
            mask_SUV_patient = subprocess.check_output(mask_SUV_patient_subprocess, universal_newlines = True)
            write_to_minc_dict(mask_SUV_patient_subprocess)
            print_and_write("The raw output of mincstats in patient-space is", mask_SUV_patient)

            mask_SUV_patient_split = mask_SUV_patient.split()

            #modify this to accommodate the multiple means given that -quiet has now been added
            means_array_patient = [float(mask_SUV_patient_split[i]) for i in range(len(mask_SUV_patient_split)) if i != 0 and mask_SUV_patient_split[i-1] == 'Mean:']

            print_and_write("The mean or means of the mask are (in patient-space)", means_array_patient)
            mask_SUV_patient = statistics.mean(means_array_patient)
            print_and_write("The extracted average of the mask (reference region) section(s) in patient-space is", mask_SUV_patient)
            outputPETpath_patient = splice(mylist_patient[-1], '_patient_SUVR')
            mylist_patient.append(outputPETpath_patient)
            bash_command('mincmath', '-clobber', '-div', '-const', mask_SUV_patient, mylist_patient[-2], outputPETpath_patient)

            #This is a check to see that radioactivity in patient-space matches that of MNI space to ensure transformations were done correctly:
        
            percent_mask_difference = abs(float(mask_SUV) - float(mask_SUV_patient))/float(mask_SUV_patient)*100
            print_and_write("% MASK RADIOACTIVITY DIFFERENCE (MNI versus PATIENT SPACE)", percent_mask_difference)  
            
            if percent_mask_difference > 5:
                print_and_write("WARNING: the reference region values in patient-space versus MNI-space seem to differ more than 5%! This could mean that a transformation went wrong.")
            else:
                print_and_write("TEST PASSED (Comparing template- and patient-space reference region radioactivity levels in order to examine whether transformation were correctly applied.")

            # 7B. Blur patient space in select resolution(s) (default = 4, 6, and 8mm)
            
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
            
            bash_command('register', mylist_patient[-1], MRIpath)
            
main(**vars(args))