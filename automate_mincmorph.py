#!/usr/bin/env python
from mailbox import linesep
import os
import subprocess
from pathlib import Path
import json
import argparse
import pandas as pd

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

    output_txt_file = str(TTEST_FILE_FULL_PATH.parent) + '/_output_log.txt'
    command_log_file = str(TTEST_FILE_FULL_PATH.parent) + '/_command_log.txt'

    def give_cluster_rank(hist_file, CLUSTER_THRESHOLD): 
        df = pd.read_fwf(hist_file, skiprows=4, usecols=['bin','counts'])
        df.dropna(inplace=True)
        CLUSTER_THRESHOLD = int(CLUSTER_THRESHOLD)
        cluster_rank = int(df[df.counts >= CLUSTER_THRESHOLD]['bin'].tail(1).values[0])
        return (cluster_rank + 1)

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
                minc_counter += 1

            def bash_command(*args):
                bash_output = subprocess.check_output([str(c) for c in args], universal_newlines=True)
                print(*args)
                write_to_minc_dict(args)
                print_and_write(str(bash_output))
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
            #bash_command('mincmask', '-clobber', TTEST_FILE_FULL_PATH, STATS_THRESHOLD_MASK_FILE, STATS_THRESHOLD_MAP_FILE)
            #replace with multiplication only
            bash_command('mincmath', '-mult','-clobber', TTEST_FILE_FULL_PATH, STATS_THRESHOLD_MASK_FILE, STATS_THRESHOLD_MAP_FILE)
            #mincmath -mult <inputfile> <maskfile>.tmp <outputfile>


            #apply the threshold mask to the inverted t-test
            INVERTED_STATS_THRESHOLD_MAP_FILE = splice(INVERTED_T_TEST_FILE, '_stats_threshold_t_map_'+ STATS_THRESHOLD_MOD)
            #bash_command('mincmask', '-clobber', INVERTED_T_TEST_FILE, INVERTED_STATS_THRESHOLD_MASK_FILE, INVERTED_STATS_THRESHOLD_MAP_FILE)
            #replace with multiplication only
            bash_command('mincmath', '-mult', '-clobber', INVERTED_T_TEST_FILE, INVERTED_STATS_THRESHOLD_MASK_FILE, INVERTED_STATS_THRESHOLD_MAP_FILE)
            #mincmath -mult <inputfile> <maskfile>.tmp <outputfile>


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
            bash_command('mincstats', '-clobber', '-histogram', HIST_FILE, '-integer_histogram', GROUPS_MINCMORPH_FILE)
            #mincstats -histogram hist.txt -discrete_histogram group.mnc 
            
            #use mincstats to find the number of values in each group via a histogram FOR INVERTED GROUPS
            INVERTED_HIST_FILE = splice(INVERTED_T_TEST_FILE, '_t_' + STATS_THRESHOLD_MOD + '_histogram').with_suffix('.txt')
            bash_command('mincstats', '-clobber', '-histogram', INVERTED_HIST_FILE, '-integer_histogram', INVERTED_GROUPS_MINCMORPH_FILE)
            #mincstats -histogram hist.txt -discrete_histogram group.mnc 

            #Then look at hist.txt and find the group number that suits the number > of voxels you want in each group. 
            #You can then find all groups greater > than this by a simple threshold > 
            cluster_rank = give_cluster_rank(HIST_FILE, CLUSTER_THRESHOLD)
            RESULTING_MASK_FILE = splice(TTEST_FILE_FULL_PATH, '_t_' + STATS_THRESHOLD_MOD + '_clust_' + CLUSTER_THRESHOLD + 'vox_mask_file')
            bash_command('mincmath', '-clobber', '-segment', '-const2', '1', cluster_rank, GROUPS_MINCMORPH_FILE, RESULTING_MASK_FILE)   
            #mincmath -gt -const <group-threshold> group.mnc mask.mnc 

            #Then look at hist.txt and find the group number that suits the number > of voxels you want in each group. 
            #You can then find all groups greater > than this by a simple threshold >  
            cluster_rank_inverted = give_cluster_rank(INVERTED_HIST_FILE, CLUSTER_THRESHOLD)
            INVERTED_RESULTING_MASK_FILE = splice(INVERTED_T_TEST_FILE, '_t_' + STATS_THRESHOLD_MOD + '_clust_' + CLUSTER_THRESHOLD +'vox_mask_file')
            bash_command('mincmath', '-clobber', '-segment', '-const2', '1', cluster_rank_inverted, INVERTED_GROUPS_MINCMORPH_FILE, INVERTED_RESULTING_MASK_FILE)   
            #mincmath -gt -const <group-threshold> group.mnc mask.mnc

            #apply the mask 
            MASKED_OUTPUT_FILE = splice(TTEST_FILE_FULL_PATH, '_t_' + STATS_THRESHOLD_MOD + '_clust_' + CLUSTER_THRESHOLD +'vox_masked_output')
            bash_command('mincmask', '-clobber', STATS_THRESHOLD_MAP_FILE, RESULTING_MASK_FILE, MASKED_OUTPUT_FILE) 

            #apply the mask to the inverted file
            INVERTED_MASKED_OUTPUT_FILE = splice(INVERTED_T_TEST_FILE, '_t_' + STATS_THRESHOLD_MOD + '_clust_' + CLUSTER_THRESHOLD +'vox_masked_output')
            bash_command('mincmask', '-clobber', INVERTED_STATS_THRESHOLD_MAP_FILE, INVERTED_RESULTING_MASK_FILE, INVERTED_MASKED_OUTPUT_FILE)

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