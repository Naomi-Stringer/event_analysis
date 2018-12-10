

#------------------------ Step 0: Import required packages ------------------------
# Import packages required for program
import numpy as np
import pandas as pd
# pd.set_option('display.max_columns', 500)
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

# NOTE new function file!
import get_error_flags

# test
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
REGION = 'victoria'
TIME_INTERVALS = 30
DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_2018_01_18_v2.csv'
META_DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_c_id_info_v2_NS.csv'
INVERTER_DATA_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_site_info_v2_NS.csv'
DATA_DATE = '2018_01_18'

# REGION = 'south_australia'
# TIME_INTERVALS = 30
# DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_2017_03_03_v2.csv'
# META_DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_c_id_info_v2_NS.csv'
# INVERTER_DATA_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_site_info_v2_NS.csv'
# DATA_DATE = '2017_03_03'

load_list = ['ac_load_net', 'ac_load']
pv_list = ['pv_site_net', 'pv_site']
gross_list = ['gross_load', 'site_gross_load']

# Fraction of data allowed in 'other' polarity before being flagged as mixed polarity (note 0.01 = 1%)
FRACTION_FOR_MIXED_POLARITY = 0.01
LOAD_FRACTION_FOR_MIXED_POLARITY = 0.01
PV_GEN_START_HR = '05:00'
PV_GEN_END_HR = '20:00'

# For calculating gross load characteristics (e.g. power at nadir):
# Time at which event occurs (t_0)
# t_0 = datetime.datetime(year= 2017, month= 3, day= 3, hour= 15, minute= 3, second= 25) # SA 30 sec
# SA 5 sec - TODO
# t_0 = datetime.datetime(year= 2018, month= 1, day= 18, hour= 15, minute= 18, second= 50) # Vic 5 sec
t_0 = datetime.datetime(year= 2018, month= 1, day= 18, hour= 15, minute= 18, second= 55) # Vic 30 sec

FACTOR_KWH_TO_J = 3600000

# Constant for checking similar voltage profiles
VRMS_SUM_VARIATION_FOR_MATCH = 0.0005
ALLOWABLE_VRMS_DIFF = 0.1 #V
NEGATIVE_ENERGY_SUM_THRESHOLD_CHECKING_GROSS_LOAD = 0.0

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#------------------------ Import data
data = solar_analytics.get_data_using_file_path(REGION, TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH)



# Add error code to 'data'
# error_1: error check A), c_id actually recording gross load for entire site. Risk of double counting.
data['error_1'] = np.nan
# error_2: error check B) check whether actually gross load rather than net
# i.e. is there zero times when load is below 0 and therefore export is occuring?) NOTE that there may be some site where load is just larger than PV so could cause issues...
data['error_2'] = np.nan
# error_3: error check C) When checking gross load, there are still negative values!
data['error_3'] = np.nan

# Fix the polarity NOTE should make this a function
# Get error flags
error_flags_df = get_error_flags.get_error_flags(REGION, TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH, DATA_DATE, FRACTION_FOR_MIXED_POLARITY, LOAD_FRACTION_FOR_MIXED_POLARITY, PV_GEN_START_HR, PV_GEN_END_HR, load_list, pv_list)
# print(error_flags_df)
# Get list of c_ids
c_ids_data = data['c_id'].drop_duplicates().tolist()
# Loop through c_ids in data and apply polarity_fix
for c_id in c_ids_data:
    
    # Get polarity
    c_id_polarity = error_flags_df.loc[c_id,'polarity_fix']

    # If the polarity is negative (-1) then *-1, else no operation required.
    if c_id_polarity == -1.0 :

        # Multiplies the values in data in the energy column for which c_id is the current c_id by -1
        data.loc[data['c_id'] == c_id, 'energy'] *= c_id_polarity
        data.loc[data['c_id'] == c_id, 'power'] *= c_id_polarity

# Calculate power
data = util.calculate_power_from_energy(data, str(TIME_INTERVALS) + '_sec')



#------------------------ Calculate gross load for sites with MORE THAN ONE single load connection id ------------------------

# Apply first two error checks A) and B) to all sites in the data set
all_site_id_in_data = data['site_id'].drop_duplicates().tolist()

# Error management: A) check for houseload and therefore potential duplication
for site in all_site_id_in_data:
    data_site = data[data['site_id'] == site]
    # Sum all energy data
    site_energy_sum = data_site['energy'].sum()
    # Sum all energy data for each c_id
    c_ids_data_site = data_site['c_id'].drop_duplicates().tolist()
    for c_id in c_ids_data_site:
        c_id_energy_sum = data_site.loc[data_site['c_id'] == c_id,'energy'].sum()
        
        # If sum of all energy data = 2* energy sum for any c_id then 
        # that c_id is house load - FLAG - and change con_type?
        # Then don't use that c_id in next steps
        if site_energy_sum == 2*c_id_energy_sum:
            # data.loc[data['c_id'] == c_id, 'con_type'] = 'site_gross_load'
            data.loc[data['c_id'] == c_id, 'error_1'] = 1.0

#------------------------ Calculate gross load for sites with single load connection id ------------------------
data = util.get_gross_load_for_single_load_cid_sites(data, META_DATA_FILE_PATH, load_list, pv_list)

# Error management: B) check whether actually gross load rather than net
# i.e. is there zero times when load is below 0 and therefore export is occuring?) NOTE that there may be some site where load is just larger than PV so could cause issues...
for site in all_site_id_in_data:
    data_site = data[data['site_id'] == site]
    data_site = data_site[data_site['con_type'].isin(load_list)]
    # Get list of c_ids since this should be considered on a c_id basis
    c_ids_data_site = data_site['c_id'].drop_duplicates().tolist()
    for c_id in c_ids_data_site:
        # Filter for c_id data
        c_id_data = data_site[data_site['c_id'] == c_id]
        # Filter for negative load only and sum negative load - will be zero if there is no negative load (and should therefore be considered gross_load). Will be some value if there is negative load.
        negative_energy_sum = abs(c_id_data.loc[c_id_data['energy'] < 0.0, 'energy'].sum())
        # If there is negative load (i.e. negative_energy_sum > 0) then okay and should be net. However if there is ZERO negative energy then should actually be gross.
        if negative_energy_sum == 0:
            data.loc[data['c_id'] == c_id, 'con_type'] = 'gross_load'
            data.loc[data['c_id'] == c_id, 'error_2'] = 1.0


# Remove sites with: 1) only a single load c_id, 2) only load c_ids, 3) only PV c_ids
sites_with_single_load_cid_list = util.count_num_type_X_cids_meets_criteria_Y(META_DATA_FILE_PATH, data, load_list, 1)
# Remove 'only a single load c_id' sites from data
data_filtered = data[data['site_id'].isin(sites_with_single_load_cid_list) == False]
print(data_filtered.head())

# 2) Remove sites with only load c_ids TODO add flag noting only load site?
sites_with_zero_pv_cid_list = util.count_num_type_X_cids_meets_criteria_Y(META_DATA_FILE_PATH, data, pv_list, 0)
# Remove sites_with_zero_pv_cid_list sites from data
data_filtered = data_filtered[data_filtered['site_id'].isin(sites_with_zero_pv_cid_list) == False]
print(data_filtered.head())

# 3) Remove sites with only pv c_ids TODO add flag noting only pv site?
sites_with_zero_load_cid_list = util.count_num_type_X_cids_meets_criteria_Y(META_DATA_FILE_PATH, data, load_list, 0)
# Remove sites_with_zero_load_cid_list sites from data
data_filtered = data_filtered[data_filtered['site_id'].isin(sites_with_zero_load_cid_list) == False]
print(data_filtered.head())

# Get list of remaining sites after removing 1) 2) 3)
data_filtered_sites_list = data_filtered['site_id'].drop_duplicates().tolist()
print(data_filtered_sites_list)

        
# Remove all data which is labelled as gross_load or site_gross_load before completing the next step, since we don't want to go adding PV back in to this data.
data_without_gross_loads = data_filtered[data_filtered['con_type'] != 'gross_load']
data_without_gross_loads = data_without_gross_loads[data_without_gross_loads['con_type'] != 'site_gross_load']
# Also remove c_ids which returned the error_1 or error_2 since these are likely to be gross load / site gross load
data_without_gross_loads = data_without_gross_loads[data_without_gross_loads['error_1'] != 1.0]
data_without_gross_loads = data_without_gross_loads[data_without_gross_loads['error_2'] != 1.0]

#------------------------ Match profiles using voltage ------------------------
data = util.get_gross_load_using_match_on_vrms(data_filtered_sites_list, data_without_gross_loads, ALLOWABLE_VRMS_DIFF, data)

# TODO Calculate site gross load - using sum of c_id gross loads? or just add all c_ids and then error check?
# Either way, label using site_id*100+10 and con_type site_gross_load (???)


# Error management: C) missing load or PV... tricky. Look for negatives in c_id gross load - there shouldn't be any!
data_gross_only = data[data['con_type'].isin(gross_list)]
c_ids_in_data_gross_only = data_gross_only['c_id'].drop_duplicates().tolist()

for c_id in c_ids_in_data_gross_only:
    # Filter for c_id data
    c_id_data = data_gross_only[data_gross_only['c_id'] == c_id]
    # Filter for negative load only and sum negative load
    negative_energy_sum = abs(c_id_data.loc[c_id_data['energy'] < 0.0, 'energy'].sum())

    # If there is negative stuff (i.e. negative_energy_sum != 0) then flag it!
    if negative_energy_sum > NEGATIVE_ENERGY_SUM_THRESHOLD_CHECKING_GROSS_LOAD:
        data.loc[data['c_id'] == c_id, 'error_3'] = 1.0


# # Remove sites with single load c_id in order to reduce file size for Tyce.
# sites_with_single_load_cid_list = util.count_num_type_X_cids_meets_criteria_Y(META_DATA_FILE_PATH, data, load_list, 1)
# data = data[data['site_id'].isin(sites_with_single_load_cid_list) == False]


# FFIL if vic
if REGION == 'victoria':
    data = util.ffil_on_cids(data)


# # ------------------------ Print to csv ------------------------
data.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_UTC_corrected_all_gross_load_' +str(TIME_INTERVALS)+'_sec_v2.csv')

#------------------------ Get gross load characteristics ------------------------
output_df = util.get_gross_load_characteristics(data, gross_list, t_0, FACTOR_KWH_TO_J)

#------------------------ Print to csv ------------------------
output_df.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_all_gross_load_characteristics_' +str(TIME_INTERVALS)+'_sec_v2.csv')

