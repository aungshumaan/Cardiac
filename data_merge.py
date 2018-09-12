# Data merging functions
import pandas as pd
import numpy as np
import pickle
from Clean_Fun import *

def pairwise_sheet_merge(live_path, archive_path, live_sheet_pkl_path, archive_sheet_pkl_path, datecol_pkl_path):
    """
    Concatonates pairs of sheets from two different spreadsheets, retaining only the sheets and columns specified
    in pickles. Returns a dictionary with keys as sheet names and values as concatonated dataframes.

    Keyword Arguments
    -----------------
    live_path -- File path for the live data spreadsheet
    archive_path -- File path for the archive data spreadsheet
    live_sheet_pkl_path -- Path to pickle containing dictionary for live spreadsheet with sheet names (keys, case sensitive) and a list
    of column names (values) for each sheet (i.e. {sheet1_name: [col1, col2,...coln], sheet2_name: [col1,...]})
    archive_sheet_pkl_path -- Same as live_sheet_pkl_path but for the archive spreadsheet
    datecol_pkl_path -- Path to pickle containing dictionary of sheets as keys and their associated date columns
    """
    # Load live sheet dictionary from pickle
    with open(live_sheet_pkl_path, 'rb') as f:
        live_sheet_dict = pickle.load(f)

    # Load archive sheet dictionary from pickle
    with open(archive_sheet_pkl_path, 'rb') as f:
        archive_sheet_dict = pickle.load(f)

    # Load date columns from pickle
    with open(datecol_pkl_path, 'rb') as f:
        datecol_dict = pickle.load(f)

    # Store sheet dictionary keys as variables and load dataframe dictionaries from spreadsheets
    archive_sheets = list(archive_sheet_dict.keys())
    live_sheets = list(live_sheet_dict.keys())
    archive_df_dict = pd.read_excel(archive_path, sheet_name=archive_sheets)
    live_df_dict = pd.read_excel(live_path, sheet_name=live_sheets)

    # Rename 'patient_id' column to 'patient_link' for consistency, do the same in live sheet dictionary
    live_df_dict['patients'].rename(columns={'patient_id': 'patient_link'}, inplace=True)
    live_sheet_dict['patients'][0] = 'patient_link'

    # Convert all column names to lowercase for consistancy
    # For each sheet dataframe, keep only the specified columns
    for sheet_name in live_sheets:
        live_df_dict[sheet_name].columns = [x.lower().strip() for x in live_df_dict[sheet_name].columns]
        live_df_dict[sheet_name] = live_df_dict[sheet_name][list(map(str.lower, live_sheet_dict[sheet_name]))]
        print('Sheet name: \"{}\"'.format(sheet_name))
        print('Retained columns: {}\n'.format(list(live_df_dict[sheet_name].columns)))
    print('\n\n')
    # Repeat for archive sheets
    for sheet_name in archive_sheets:
        archive_df_dict[sheet_name].columns = [x.lower().strip() for x in archive_df_dict[sheet_name].columns]
        archive_df_dict[sheet_name] = archive_df_dict[sheet_name][list(map(str.lower, archive_sheet_dict[sheet_name]))]
        print('Sheet name: \"{}\"'.format(sheet_name))
        print('Retained columns: {}\n'.format(list(archive_df_dict[sheet_name].columns)))

    # Make sure all date columns have appropriate datetime format, otherwise change to NaT
    for sheet_name in list(datecol_dict.keys()):
        live_df_dict[sheet_name][datecol_dict[sheet_name]] = datetime_fixer(live_df_dict[sheet_name][datecol_dict[sheet_name]])
        archive_df_dict[sheet_name][datecol_dict[sheet_name]] = datetime_fixer(archive_df_dict[sheet_name][datecol_dict[sheet_name]])
        print('Date column \"{}\" in sheet \"{}\" has been converted to appropriate datatype\n'.format(datecol_dict[sheet_name], sheet_name))

    live_df_dict['patients']['date_of_birth'] = datetime_fixer(live_df_dict['patients']['date_of_birth'])
    print('Date column "date_of_birth" in sheet "patients" has been converted to appropriate datatype')
    
    combined_df_dict = {}

    # Concatonate pairs of sheets and store in new combined_df_dict
    for sheet_name in archive_sheets:
        combined_df_dict[sheet_name] = pd.concat([archive_df_dict[sheet_name], live_df_dict[sheet_name]], ignore_index=True)

    # Add 'patients' sheet to combined_df_dict, because it is not in archive
    combined_df_dict['patients'] = live_df_dict['patients']

    return combined_df_dict
