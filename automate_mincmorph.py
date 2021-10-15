#!/usr/bin/env python
import os
import subprocess
from pathlib import Path
import json
import argparse

parser = argparse.ArgumentParser('my_args')
parser.add_argument('json_file')    
args = parser.parse_args()

def splice(path: Path, modifier) -> Path:
    dir_name = str(os.path.dirname(path))
    base_name = str(os.path.basename(path))
    return path.parent.joinpath(path.stem + modifier).with_suffix(path.suffix)

def main(json_file):

    json_path = Path(json_file)

    if json_path.exists():
        config = json.load(json_path.open())
        TTEST_FILE_FULL_PATH = Path(config["TTEST_FILE_FULL_PATH"])
        STATS_THRESHOLD = config["STATS_THRESHOLD"]
        CLUSTER_THRESHOLD = str(config["CLUSTER_THRESHOLD"])
        BBMASK_FILE = Path(config["BBMASK_FILE"])
        TEMPLATE_FILE = Path(config["TEMPLATE_FILE"])

    def bash_command(*args):
        bash_output = subprocess.check_output([str(c) for c in args], universal_newlines=True)
        print(*args)
        print(str(bash_output))
        return bash_output

    STATS_THRESHOLD_MOD = str(STATS_THRESHOLD).replace('.', 'pt')
    #Invert the t-test file : 
    INVERTED_T_TEST_FILE = splice(TTEST_FILE_FULL_PATH, '_INVERTED')
    bash_command('mincmath', '-clobber', '-mult', TTEST_FILE_FULL_PATH, '-const', '-1', INVERTED_T_TEST_FILE)
    #mincmath –mult ttestfile.mnc –const -1 ttestfile-INV.mnc
    
    #find all voxels above your statistical threshold
    STATS_THRESHOLD_MASK_FILE = splice(TTEST_FILE_FULL_PATH, '_stats_threshold_t_mask_'+ STATS_THRESHOLD_MOD)
    bash_command('mincmath', '-clobber', '-ge', '-const', STATS_THRESHOLD, TTEST_FILE_FULL_PATH, STATS_THRESHOLD_MASK_FILE)
    #mincmath -ge -const <thresh> tmap.mnc thresh.mnc 

    #find all voxels above your statistical threshold IN INVERTED MAP
    INVERTED_STATS_THRESHOLD_MASK_FILE = splice(INVERTED_T_TEST_FILE, '_stats_threshold_t_mask_'+ STATS_THRESHOLD_MOD)
    bash_command('mincmath', '-clobber', '-ge', '-const', STATS_THRESHOLD, INVERTED_T_TEST_FILE, INVERTED_STATS_THRESHOLD_MASK_FILE)
    #mincmath -ge -const <thresh> tmap.mnc thresh.mnc

    #apply the threshold mask to t-test
    STATS_THRESHOLD_MAP_FILE = splice(TTEST_FILE_FULL_PATH, '_stats_threshold_t_map_'+ STATS_THRESHOLD_MOD)
    bash_command('mincmask', '-clobber', TTEST_FILE_FULL_PATH, STATS_THRESHOLD_MASK_FILE, STATS_THRESHOLD_MAP_FILE)

    #apply the threshold mask to the inverted t-test
    INVERTED_STATS_THRESHOLD_MAP_FILE = splice(INVERTED_T_TEST_FILE, '_stats_threshold_t_map_'+ STATS_THRESHOLD_MOD)
    bash_command('mincmask', '-clobber', INVERTED_T_TEST_FILE, INVERTED_STATS_THRESHOLD_MASK_FILE, INVERTED_STATS_THRESHOLD_MAP_FILE)

    #use mincmorph to find the groups (using a 3D 6 connectivity kernel) - mincmorph will order the groups by size. 
    GROUPS_MINCMORPH_FILE = splice(TTEST_FILE_FULL_PATH, '_t_'+ STATS_THRESHOLD_MOD + '_groups_mincmorph')
    bash_command('mincmorph', '-clobber', '-group', '-3D06', STATS_THRESHOLD_MASK_FILE, GROUPS_MINCMORPH_FILE)
    #mincmorph -group -3D06 thresh.mnc groups.mnc

    #use mincmorph to find the groups (using a 3D 6 connectivity kernel) - mincmorph will order the groups by size - FOR INVERTED MAP
    INVERTED_GROUPS_MINCMORPH_FILE = splice(INVERTED_T_TEST_FILE, '_t_' + STATS_THRESHOLD_MOD + '_groups_mincmorph')
    bash_command('mincmorph', '-clobber', '-group', '-3D06', INVERTED_STATS_THRESHOLD_MASK_FILE, INVERTED_GROUPS_MINCMORPH_FILE)
    #mincmorph -group -3D06 thresh.mnc groups.mnc

    #use mincstats to find the number of values in each group via a histogram
    HIST_FILE = splice(TTEST_FILE_FULL_PATH, '_t_' + STATS_THRESHOLD_MOD + '_histogram').with_suffix('.txt')
    bash_command('mincstats', '-clobber', '-histogram', HIST_FILE, '-discrete_histogram', GROUPS_MINCMORPH_FILE)
    #mincstats -histogram hist.txt -discrete_histogram group.mnc 
    
    #use mincstats to find the number of values in each group via a histogram FOR INVERTED GROUPS
    INVERTED_HIST_FILE = splice(INVERTED_T_TEST_FILE, '_t_' + STATS_THRESHOLD_MOD + '_histogram').with_suffix('.txt')
    bash_command('mincstats', '-clobber', '-histogram', INVERTED_HIST_FILE, '-discrete_histogram', INVERTED_GROUPS_MINCMORPH_FILE)
    #mincstats -histogram hist.txt -discrete_histogram group.mnc 

    #Then look at hist.txt and find the group number that suits the number > of voxels you want in each group. 
    #You can then find all groups greater > than this by a simple threshold >  
    RESULTING_MASK_FILE = splice(TTEST_FILE_FULL_PATH, '_t_' + STATS_THRESHOLD_MOD + '_clust_' + CLUSTER_THRESHOLD + '_mask_file')
    bash_command('mincmath', '-clobber', '-le', '-const', CLUSTER_THRESHOLD, GROUPS_MINCMORPH_FILE, RESULTING_MASK_FILE)   
    #mincmath -gt -const <group-threshold> group.mnc mask.mnc 

    #Then look at hist.txt and find the group number that suits the number > of voxels you want in each group. 
    #You can then find all groups greater > than this by a simple threshold >  
    INVERTED_RESULTING_MASK_FILE = splice(INVERTED_T_TEST_FILE, '_t_' + STATS_THRESHOLD_MOD + '_clust_' + CLUSTER_THRESHOLD +'_mask_file')
    bash_command('mincmath', '-clobber', '-le', '-const', CLUSTER_THRESHOLD, INVERTED_GROUPS_MINCMORPH_FILE, INVERTED_RESULTING_MASK_FILE)   
    #mincmath -gt -const <group-threshold> group.mnc mask.mnc

    #apply the mask 
    MASKED_OUTPUT_FILE = splice(TTEST_FILE_FULL_PATH, '_t_' + STATS_THRESHOLD_MOD + '_clust_' + CLUSTER_THRESHOLD +'_masked_output')
    bash_command('mincmask', '-clobber', GROUPS_MINCMORPH_FILE, RESULTING_MASK_FILE, MASKED_OUTPUT_FILE) 

    #apply the mask to the inverted file
    INVERTED_MASKED_OUTPUT_FILE = splice(INVERTED_T_TEST_FILE, '_t_' + STATS_THRESHOLD_MOD + '_clust_' + CLUSTER_THRESHOLD +'_masked_output')
    bash_command('mincmask', '-clobber', INVERTED_GROUPS_MINCMORPH_FILE, INVERTED_RESULTING_MASK_FILE, INVERTED_MASKED_OUTPUT_FILE)

    #apply a black border mask
    MASKED_OUTPUT_FILE_BLACKBORDER = splice(MASKED_OUTPUT_FILE, '_blackborder')
    bash_command('mincmask', '-clobber', MASKED_OUTPUT_FILE, BBMASK_FILE, MASKED_OUTPUT_FILE_BLACKBORDER)

    #apply a black border mask to the inverted file
    INVERTED_MASKED_OUTPUT_FILE_BLACKBORDER = splice(INVERTED_MASKED_OUTPUT_FILE, '_blackborder')
    bash_command('mincmask', '-clobber', INVERTED_MASKED_OUTPUT_FILE, BBMASK_FILE, INVERTED_MASKED_OUTPUT_FILE_BLACKBORDER)

    #show the result! 
    bash_command('register', MASKED_OUTPUT_FILE_BLACKBORDER, TEMPLATE_FILE)
    bash_command('register', INVERTED_MASKED_OUTPUT_FILE_BLACKBORDER, TEMPLATE_FILE) 

main(**vars(args))
