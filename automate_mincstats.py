#!/usr/bin/python
import os
import subprocess
from pathlib import Path
import numpy
import pandas as pd
import json
import argparse
from copy import deepcopy

parser = argparse.ArgumentParser('my_args')
parser.add_argument('json_file')    
args = parser.parse_args()

def main(json_file):

    json_path = Path(json_file)

    if json_path.exists():
        config = json.load(json_path.open())
        FOLDER_OF_SCANS = config["FOLDER_OF_SCANS"]
        ROI_PATHS = config["ROI_PATHS"]
        STATS_REQUESTED = config['STATS_REQUESTED']
        MNI_ATLAS_RESAMPLED_PATH = config['MNI_ATLAS_RESAMPLED_PATH']
        MNI_ATLAS_BIN_VALUES = config['MNI_ATLAS_BIN_VALUES']
    
    if len(MNI_ATLAS_RESAMPLED_PATH) != 0:
        MNI_ATLAS_RESAMPLED_PATH = MNI_ATLAS_RESAMPLED_PATH[0]
    
    num_reg_atlas_list = []
    for i in ROI_PATHS:
        number_regions = subprocess.check_output(['volume_stats', '-quiet', '-max', i], universal_newlines = True)
        number_regions = int(number_regions)
        num_reg_atlas_list.append(number_regions)
    
    num_reg_atlas_list = [[d for d in range(1, item+1)] for item in num_reg_atlas_list]

    newdict = {}
    counter = 0
    for z in num_reg_atlas_list:
        newdict[ROI_PATHS[counter]] = z
        counter += 1
    
    if len(MNI_ATLAS_RESAMPLED_PATH) != 0:
        newdict[MNI_ATLAS_RESAMPLED_PATH] = MNI_ATLAS_BIN_VALUES
    
    STATS_REQUESTED = [stat.lower() for stat in STATS_REQUESTED]
    
    stat_dict = {}
    file_roi_bin_dict = {}
    roi_df_dict = {}
    roi_df = pd.DataFrame()  

    for filename in os.listdir(FOLDER_OF_SCANS):
        if filename.endswith(".mnc") == True: 
            full_filename = os.path.join(FOLDER_OF_SCANS,filename)
            for ROI, binvalues in newdict.items():
                for subbinvalue in binvalues:
                    subbinvalue = str(subbinvalue)
                    for stat in STATS_REQUESTED: 
                        stat_dict[stat] = subprocess.check_output(['mincstats', '-mask', str(ROI), '-mask_binvalue', subbinvalue, '-quiet', str(full_filename), stat], universal_newlines = True)
                        stat_dict[stat] = float(stat_dict[stat])
                    ROI_BASENAME = os.path.basename(Path(ROI))
                    file_roi_bin_dict = {"File": filename, "ROI": ROI_BASENAME + "_BIN_" + subbinvalue}
                    roi_df_dict = dict(file_roi_bin_dict, **stat_dict)
                    roi_df = roi_df.append(roi_df_dict, ignore_index = True)

    unstacked = roi_df.groupby(['File','ROI'],sort=False).mean().unstack()
    new_cols = unstacked.columns.map(' | '.join)
    unstacked.columns = new_cols

    combinations = [(a,b) for a in roi_df.ROI.unique() for b in STATS_REQUESTED]

    col_order = [(b+' | '+a) for a,b in combinations]
    
    unstacked = unstacked[col_order]
    
    #formatting of columns
    formatted_columns = [column[1:column.find('|')].upper() 
                     + column[column.find('|'):] 
                     for column in unstacked.columns.tolist()]
    unstacked.columns = formatted_columns

    json_parent = json_path.parent
    unstacked.to_csv(json_parent/'roi_df.csv')

main(**vars(args))

