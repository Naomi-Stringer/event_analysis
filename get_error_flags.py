# Get error flags
# Contains a function to identify erroneous data (should probably move to 'util' and update scripts which call this function accordingly!) 


#------------------------ Step 0: Import required packages ------------------------
# Import packages required for program
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 500)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import calendar
import seaborn as sns
import itertools
import datetime
from time import gmtime, strftime

import solar_analytics
import requested_regions
import util
import util_plotting


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Inputs
REGION = 'south_australia'
TIME_INTERVALS = 5
DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_2017_03_03_v2.csv'
META_DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_c_id_info_v2.csv'
INVERTER_DATA_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_site_info_v2.csv'
DATA_DATE = '2017_03_03'
# NOTE don't forget the date!^

# REGION = 'victoria'
# TIME_INTERVALS = 30
# DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_2018_01_18_v2.csv'
# META_DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_c_id_info_v2.csv'
# INVERTER_DATA_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_site_info_v2.csv'
# DATA_DATE = '2018_01_18'

# Fraction of data allowed in 'other' polarity before being flagged as mixed polarity (note 0.01 = 1%)
FRACTION_FOR_MIXED_POLARITY = 0.01
LOAD_FRACTION_FOR_MIXED_POLARITY = 0.01
PV_GEN_START_HR = '05:00'
PV_GEN_END_HR = '20:00'

load_list = ['ac_load_net', 'ac_load']
pv_list = ['pv_site_net', 'pv_site']

# Manual additions based on visualisations (will be saved under 'profile_irregularities') - TODO - maybe use a csv??
# SA 5 sec data, 3/3/2017
# irreg_cids = ['']
# SA 5 sec data, 3/3/2017

# SA 5 sec data, 3/3/2017

# SA 5 sec data, 3/3/2017

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


def get_error_flags(REGION, TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH, DATA_DATE, FRACTION_FOR_MIXED_POLARITY, LOAD_FRACTION_FOR_MIXED_POLARITY, PV_GEN_START_HR, PV_GEN_END_HR, load_list, pv_list) :

    #------------------------ Step 1: Get data ------------------------
    # IF 25 August 2018 data then need to use different fnct in factory to get data
    # Change data columns names IF 25 August 2018 data (differently named)
    if DATA_DATE == '25_august_2018':
        data = solar_analytics.get_august_data_using_file_path(TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH)
        # Change column names for frequency and energy
        data = data.rename(columns = {'e':'energy', 'f':'frequency'})
        print(data.head())

    else:
        data = solar_analytics.get_data_using_file_path(REGION, TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH)
        # print(data)

    # Get c_id_info df, this df will contain error flags
    error_flags_df = pd.read_csv("/mnt/f/05_Solar_Analytics/" + META_DATA_FILE_PATH, index_col='c_id')
    # NOTE Minor clean - check if ever using a different file above ^ 
    error_flags_df = error_flags_df[['site_id', 'con_type']]

    #------------------------ Step 2: Make error flags df ------------------------

    # Filter out c_ids not in data
    # NOTE - it is possible that there are c_ids in the data which are not in the meta data file - worth checking! Checked - this is fine, same number of c_ids in both.
    c_ids_data = data['c_id'].drop_duplicates().tolist()
    error_flags_df = error_flags_df.loc[c_ids_data]

    # Get two separate lists of c_ids remaining which are load / PV
    pv_cids = error_flags_df[error_flags_df['con_type'].isin(pv_list)]
    pv_cids = pv_cids.index.values.tolist()
    load_cids = error_flags_df[error_flags_df['con_type'].isin(load_list)]
    load_cids = load_cids.index.values.tolist()

    # Add new columns for flags
    error_flags_df['zero_output'] = np.nan
    error_flags_df['constant_50hz'] = np.nan
    error_flags_df['mixed_polarity'] = np.nan
    error_flags_df['profile_irregularities'] = np.nan
    error_flags_df['any_error_flag'] = np.nan

    # Add new columns for other things we want to record
    error_flags_df['sum_energy_joules'] = np.nan
    error_flags_df['positive_export'] = np.nan
    error_flags_df['negative_export'] = np.nan
    error_flags_df['polarity_fix'] = np.nan

    # print(error_flags_df)


    #------------------------ Step 3: Loop through c_ids for error flags ------------------------
    # Loop through sites - both PV and load
    for c_id in c_ids_data:

        # test cases: 298 (non zero), 5326 (zero)
        # c_id = 5326

        # Filter data for specific c_id
        c_id_data = data[data['c_id'] == c_id]
        # print(c_id_data)

        #------------------------ Check for 'zero_output' ------------------------
        # Sum energy vals
        energy_sum = c_id_data['energy'].sum()
        error_flags_df.loc[float(c_id),'sum_energy_joules'] = energy_sum
        # print(energy_sum)

        if energy_sum == 0 :
            error_flags_df.loc[float(c_id),'zero_output'] = 1
        # print('yay')

        #------------------------ Check for 'constant_50hz' ------------------------
        frequency_sum = c_id_data['frequency'].sum()

        num_data_pts = len(c_id_data) - c_id_data.frequency.isnull().sum()
        frequency_check = 50.0 * num_data_pts

        if frequency_sum == frequency_check :
            error_flags_df.loc[float(c_id),'constant_50hz'] = 1


    for c_id in pv_cids:
        # Filter data for specific c_id
        c_id_data = data[data['c_id'] == c_id]

        #------------------------ Check for 'mixed_polarity' - pv sites only! ------------------------

        # Assign polarity as positive or negative (simple first approach)
        # Get sum of positive energy vals
        positive_energy_sum = c_id_data.energy[c_id_data['energy'] > 0.0].sum()
        # print(positive_energy_sum)
        negative_energy_sum = c_id_data.energy[c_id_data['energy'] < 0.0].sum()
        # print(negative_energy_sum)
        # Calc sum of positive and negative energies as abs val
        abs_sum_energy = abs(positive_energy_sum) + abs(negative_energy_sum)
        # print(abs_sum_energy)

        # Simple approach to assigning polarity - doesn't account for very small negative / positive values over night
        if negative_energy_sum == 0 and positive_energy_sum != 0 :
            error_flags_df.loc[float(c_id),'positive_export'] = 1
        if positive_energy_sum == 0 and negative_energy_sum != 0 :
            error_flags_df.loc[float(c_id),'negative_export'] = 1

        # Less simple approach, takes into account small measures in opposite polarity
        if abs_sum_energy != 0:
            fraction_positive_energy = float(abs(positive_energy_sum)) / float(abs_sum_energy)
            fraction_negative_energy = float(abs(negative_energy_sum)) / float(abs_sum_energy)

            if fraction_positive_energy > (1 - FRACTION_FOR_MIXED_POLARITY) and fraction_negative_energy < FRACTION_FOR_MIXED_POLARITY :
                error_flags_df.loc[float(c_id),'positive_export'] = 1
            if fraction_negative_energy > (1 - FRACTION_FOR_MIXED_POLARITY) and fraction_positive_energy < FRACTION_FOR_MIXED_POLARITY :
                error_flags_df.loc[float(c_id),'negative_export'] = 1

            # If there is more than 1% of both positive and negative vals then mixed polarity flag
            if fraction_negative_energy > FRACTION_FOR_MIXED_POLARITY and fraction_positive_energy > FRACTION_FOR_MIXED_POLARITY :
                error_flags_df.loc[float(c_id),'mixed_polarity'] = 1




    #------------------------ Get load polarities ------------------------
    # Similarly using the negative / positive method above, however only consider data outside solar PV times.

    # Filter data for load
    load_data = data[data['con_type'].isin(load_list)]
    # filter for time between PV end hr and PV start hr (inputs above)
    load_data = load_data.between_time(PV_GEN_END_HR, PV_GEN_START_HR)


    # LOOP
    for c_id in load_cids:
        # test cases: 59226 (consumption is positive, profile clearly net)
        # c_id = 59226

        # Filter data for specific c_id
        c_id_data = load_data[load_data['c_id'] == c_id]

        # Assign polarity as positive or negative (simple first approach)
        # Get sum of positive energy vals
        positive_energy_sum = c_id_data.energy[c_id_data['energy'] > 0.0].sum()
        # print(positive_energy_sum)
        negative_energy_sum = c_id_data.energy[c_id_data['energy'] < 0.0].sum()
        # print(negative_energy_sum)
        # Calc sum of positive and negative energies as abs val
        abs_sum_energy = abs(positive_energy_sum) + abs(negative_energy_sum)
        # print(abs_sum_energy)

        # Simple approach to assigning polarity - doesn't account for very small negative / positive values over night
        if negative_energy_sum == 0 and positive_energy_sum != 0 :
            error_flags_df.loc[float(c_id),'positive_export'] = 1
        if positive_energy_sum == 0 and negative_energy_sum != 0 :
            error_flags_df.loc[float(c_id),'negative_export'] = 1

        # Less simple approach, takes into account small measures in opposite polarity
        if abs_sum_energy != 0:
            fraction_positive_energy = float(abs(positive_energy_sum)) / float(abs_sum_energy)
            fraction_negative_energy = float(abs(negative_energy_sum)) / float(abs_sum_energy)

            # Could possibly simplify this a bit, but be careful with zero vals!
            if fraction_positive_energy > (1 - LOAD_FRACTION_FOR_MIXED_POLARITY) and fraction_negative_energy < LOAD_FRACTION_FOR_MIXED_POLARITY :
                error_flags_df.loc[float(c_id),'positive_export'] = 1
            if fraction_negative_energy > (1 - LOAD_FRACTION_FOR_MIXED_POLARITY) and fraction_positive_energy < LOAD_FRACTION_FOR_MIXED_POLARITY :
                error_flags_df.loc[float(c_id),'negative_export'] = 1

            # If there is more than 1% of both positive and negative vals then mixed polarity flag
            if fraction_negative_energy > LOAD_FRACTION_FOR_MIXED_POLARITY and fraction_positive_energy > LOAD_FRACTION_FOR_MIXED_POLARITY :
                error_flags_df.loc[float(c_id),'mixed_polarity'] = 1



    #------------------------ Step 4: Summing findings ------------------------
    for c_id in c_ids_data:
        #------------------------ calculate polarity fix ------------------------
        if np.isnan(error_flags_df.loc[float(c_id),'positive_export']):
            positive_export = 0
        else:
            positive_export = 1

        if np.isnan(error_flags_df.loc[float(c_id),'negative_export']):
            negative_export = 0
        else:
            negative_export = 1
        # Calc polarity fix
        error_flags_df.loc[float(c_id),'polarity_fix'] = positive_export - negative_export 

        #------------------------ calculate any_error_flag ------------------------
        if np.isnan(error_flags_df.loc[float(c_id),'zero_output']): 
            zero_output = 0 
        else: 
            zero_output = 1

        if np.isnan(error_flags_df.loc[float(c_id),'constant_50hz']): 
            constant_50hz = 0 
        else: 
            constant_50hz = 1

        if np.isnan(error_flags_df.loc[float(c_id),'mixed_polarity']): 
            mixed_polarity = 0 
        else: 
            mixed_polarity = 1
        
        # Check if any flags
        error_flags_df.loc[float(c_id),'any_error_flag'] = max(zero_output, constant_50hz, mixed_polarity)

    # Output error flags
    return error_flags_df


# #------------------------ Step 5: Call function and export to csv ------------------------


# # Call function
# error_flags_df = get_error_flags(REGION, TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH, DATA_DATE, FRACTION_FOR_MIXED_POLARITY, LOAD_FRACTION_FOR_MIXED_POLARITY, PV_GEN_START_HR, PV_GEN_END_HR, load_list, pv_list)

# # Print output
# print(error_flags_df)
# # print(len(error_flags_df))

# # Save to csv
# error_flags_df.to_csv('output_csv_files/error_flags_' + REGION + '_' + DATA_DATE + '_' +str(TIME_INTERVALS)+'_sec_v2.csv')

