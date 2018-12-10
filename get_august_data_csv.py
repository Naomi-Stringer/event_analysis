# Gets data from 25 August 2018 data transfer, filters and exports csv

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


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
REGION = 'QLD'
TIME_INTERVAL = 60 #5 or 30 or 60
DATA_FILE_PATH = '2018-09-03_solar_analytics_data_transfer/2018-08-25_sa_qld_naomi.csv'
META_DATA_FILE_PATH = '2018-09-03_solar_analytics_data_transfer/circuit_details_TB_V9.csv'
INVERTER_DATA_PATH = '2018-09-03_solar_analytics_data_transfer/site_details_multiples_summarised_NS_v2.csv'

# REGION = 'ACT' #'TAS' or 'ACT' are stored in separate file
# TIME_INTERVAL = 60 #5 or 30 or 60
# DATA_FILE_PATH = '2018-09-03_solar_analytics_data_transfer/2018-05-25_act_tas_fault_aemo.csv'
# META_DATA_FILE_PATH = '2018-09-03_solar_analytics_data_transfer/act_tas_circuit_details_NS_v1.csv'
# INVERTER_DATA_PATH = '2018-09-03_solar_analytics_data_transfer/act_tas_sites_details_multiples_summarised_NS_v2.csv'

FREQUENCY_DATA_PATH = 'Solar_Analytics_data_25_august_2018_event/' + REGION + '_1min_ideal_profile_no_ramp_up.csv'

DATA_DATE = '25_august_2018'

# For getting error flags
FRACTION_FOR_MIXED_POLARITY = 0.01
LOAD_FRACTION_FOR_MIXED_POLARITY = 0.01
PV_GEN_START_HR = '05:00'
PV_GEN_END_HR = '20:00'
load_list = ['ac_load_net', 'ac_load']
pv_list = ['pv_site_net', 'pv_site', 'pv_inverter_net']
load_list_extended = ['ac_load', 'ac_load_net', 'battery_storage', 'load_air_conditioner', 'load_common_area', 'load_ev_charger', 'load_garage', 'load_generator', 'load_hot_water', 'load_hot_water_solar', 'load_kitchen', 'load_laundry', 'load_lighting', 'load_machine', 'load_office', 'load_other', 'load_pool', 'load_powerpoint', 'load_refrigerator', 'load_shed', 'load_spa', 'load_stove', 'load_studio', 'load_subboard', 'load_tenant', 'load_washer']



# For getting extreme response characteristics (categories analysis)
t_0 = datetime.datetime(year= 2018, month= 8, day= 25, hour= 13, minute= 10, second= 55) #NOTE this is now used to get normalised profiles
T_START_T_0 = '13:10:55'
T_END_ESTIMATE = '13:30:55'
T_END_ESTIMATE_NADIR = '13:16:55' #NOTE this will also be used to get p0+1 and p0+2, so cannot set too close to t0. Be very careful with it.
POWER_ROUND_TO_ZERO_VAL_KW = 0.1
RIDE_THROUGH_PERCENTAGE_DROP_MAX = 0.04
DIP_PERCENTAGE_DROP_MAX = 0.10
CAT_3_NADIR_DROP_MAX = 0.25
CAT_4_NADIR_DROP_MAX = 0.50
CAT_5_NADIR_DROP_MAX = 0.75
DISCONNECT_CAT_APPROX_ZERO_KW = 0.1
PERCENTAGE_RETURN_MINIMUM = 0.1

# For getting site capacity factor, indicates the minute past 1pm on 25 August from which CF will be calculated and returned
MINUTE_NOW_START = 5

# For getting normalised power. Sites where power is < this threshold at t0 will be excluded.
POWER_ASSUME_ZERO_KW_VAL = POWER_ROUND_TO_ZERO_VAL_KW 

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# region_list = ['QLD', 'SA', 'NSW', 'VIC']
# time_interval_list = [60,30,5]

# for REGION in region_list:

#     for TIME_INTERVAL in time_interval_list:

#------------------------ Import data ------------------------
data = solar_analytics.get_august_data_using_file_path(TIME_INTERVAL, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH)


#------------------------ Filter ------------------------
output_df = data[data['s_state'] == REGION]
# print(output_df)

# #------------------------ Forward fill to remove missing data issues ------------------------
if REGION == 'VIC':
    output_df = util.ffil_data_by_cids(output_df)

# # Checking for missing data. Look at the number of data points, compared with the total expected number of data points (count of unique c_ids * number of time stamps)
# print(len(output_df))

# count_cids = len(output_df['c_id'].drop_duplicates().tolist())
# print(count_cids)
# count_time_stamps = len(output_df.index.drop_duplicates().tolist())
# print(count_time_stamps)
# print(count_cids*count_time_stamps)

# # count_nan = len(output_df) - output_df.count()
# # print(count_nan)


# #------------------------ Get site capacity factor for PV gen ------------------------
# site_df = util.get_pv_CF_by_site(output_df, pv_list, MINUTE_NOW_START)
# # Print outcome to csv
# site_df.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_approx_cap_factor_by_site_id_' +str(TIME_INTERVAL)+'_sec_v4.csv')


#------------------------ Get c_id profiles normalised to P at t_0 ------------------------
output_df = util.get_power_kW_normalised_to_p0(output_df, pv_list, t_0, POWER_ASSUME_ZERO_KW_VAL)


#------------------------ Get ideal AS4777 vs actual error metric ------------------------
# Simple approach 
# NOTE not yet functional for any state other than QLD !!!!!!!!!!!!!! 
# NOTE must run the get_power_kW_normalised_to_p0 code first.

# Get ideal 1min average profile 
freq_data = pd.read_csv("/mnt/f/05_Solar_Analytics/" + FREQUENCY_DATA_PATH,index_col = 'ts', parse_dates=True)
print(freq_data)

# Filter output_df for just the time stamps listed in freq_data and PV sites
date_times_from_freq_data = freq_data.index.tolist()
output_df_subset = output_df.loc[output_df.index.isin(date_times_from_freq_data)]
output_df_subset = output_df_subset[output_df_subset['con_type'].isin(pv_list)]

# Merge freq_data onto output_df LEFT - i.e. keep all data in output_df
output_df_subset = output_df_subset.merge(freq_data, how='left', left_index=True, right_index = True)

# Calc the difference AND abs difference between normed power and ideal 1min average. Will use the abs diff for sites that are mixed above/below
output_df_subset['abs_diff_actual_cf_ideal'] = (output_df_subset['power_kW_normed_to_p0'] - output_df_subset['ideal_1min_profile']).abs()
output_df_subset['diff_actual_cf_ideal'] = output_df_subset['power_kW_normed_to_p0'] - output_df_subset['ideal_1min_profile']

# # Groupby average of difference and c_id
# ave_abs_diff_df = pd.DataFrame({'abs_diff_actual_cf_ideal' : output_df_subset.groupby('c_id')['abs_diff_actual_cf_ideal'].mean()}).reset_index()
# ave_diff_df = pd.DataFrame({'diff_actual_cf_ideal' : output_df_subset.groupby('c_id')['diff_actual_cf_ideal'].mean()}).reset_index()
# # Combine into a df 
# error_metric = ave_abs_diff_df.merge(ave_diff_df)

# Calc the percentage difference
output_df_subset['abs_percent_diff_actual_cf_ideal'] = output_df_subset['abs_diff_actual_cf_ideal'] / output_df_subset['ideal_1min_profile']
output_df_subset['percent_diff_actual_cf_ideal'] = output_df_subset['diff_actual_cf_ideal'] / output_df_subset['ideal_1min_profile']

# Groupby average of percentage difference and c_id
percentage_ave_abs_diff_df = pd.DataFrame({'abs_percent_diff_actual_cf_ideal' : output_df_subset.groupby('c_id')['abs_percent_diff_actual_cf_ideal'].mean()}).reset_index()
percentage_ave_diff_df = pd.DataFrame({'percent_diff_actual_cf_ideal' : output_df_subset.groupby('c_id')['percent_diff_actual_cf_ideal'].mean()}).reset_index()

# Combine into a df 
error_metric = percentage_ave_abs_diff_df.merge(percentage_ave_diff_df)
# error_metric = error_metric.merge(percentage_ave_abs_diff_df)
# error_metric = error_metric.merge(percentage_ave_diff_df)

# Add flag columns to output df 'error_metric'
error_metric['below_spec'] = 0
error_metric['above_spec'] = 0
error_metric['mixed_wrt_spec'] = 1

# Groupby for min, max. 
min_diff_df = pd.DataFrame({'min_diff' : output_df_subset.groupby('c_id')['diff_actual_cf_ideal'].min()}).reset_index()
max_diff_df = pd.DataFrame({'max_diff' : output_df_subset.groupby('c_id')['diff_actual_cf_ideal'].max()}).reset_index()
# Add to error_metric then get flags (below)
error_metric = error_metric.merge(min_diff_df)
error_metric = error_metric.merge(max_diff_df)

# Determine whether all points are 'above' the specified response (or 'below' or 'mixed') and flag accordingly
error_metric.loc[error_metric['max_diff']<=0, 'below_spec'] = 1
error_metric.loc[error_metric['min_diff']>=0, 'above_spec'] = 1
error_metric['mixed_wrt_spec'] = error_metric['mixed_wrt_spec'] - error_metric['below_spec'] - error_metric['above_spec']

# Get final error metric, taking into account whether above/below or mixed wrt spec
error_metric['combined_error_metric'] = (error_metric['below_spec'] + error_metric['above_spec']) * error_metric['percent_diff_actual_cf_ideal'] + error_metric['mixed_wrt_spec'] * error_metric['abs_percent_diff_actual_cf_ideal']

# Print to csv
output_df_subset.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_getting_c_id_error_metric_' +str(TIME_INTERVAL)+'_sec_v6.csv')
error_metric.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_c_id_error_metric_' +str(TIME_INTERVAL)+'_sec_v6.csv')



# # ------------------------ Print to csv ------------------------
# output_df.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_utc_corrected_' +str(TIME_INTERVAL)+'_sec_v13.csv')


# #------------------------ Get error flags to catch additional polarity issues ------------------------
# error_flags = get_error_flags.get_error_flags(REGION, TIME_INTERVAL, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH, DATA_DATE, FRACTION_FOR_MIXED_POLARITY, LOAD_FRACTION_FOR_MIXED_POLARITY, PV_GEN_START_HR, PV_GEN_END_HR, load_list, pv_list)
# # Print to csv
# error_flags.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_error_flags_TEST_' +str(TIME_INTERVAL)+'_sec_v0.csv')

# #------------------------ Get categories ananlysis (SLOW!) ------------------------
# extreme_response_characteristics = util.get_extreme_response_characteristics(REGION, TIME_INTERVAL, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH, DATA_DATE, load_list, pv_list, t_0, T_START_T_0, T_END_ESTIMATE, T_END_ESTIMATE_NADIR, POWER_ROUND_TO_ZERO_VAL_KW, RIDE_THROUGH_PERCENTAGE_DROP_MAX, DIP_PERCENTAGE_DROP_MAX, CAT_3_NADIR_DROP_MAX, CAT_4_NADIR_DROP_MAX, CAT_5_NADIR_DROP_MAX, DISCONNECT_CAT_APPROX_ZERO_KW, PERCENTAGE_RETURN_MINIMUM)
# # Print to csv
# extreme_response_characteristics.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_cats_' +str(TIME_INTERVAL)+'_sec_v14.csv')


# #------------------------ Get gross load for single load c_id sites ------------------------
# # NOTE need to add code to remove sites with a flag for gross load issues. Tyce has flagged the load profile for each site with single load c_id that has issues with the gross load 
# # IMPORTANTLY this does not capture any information about what is wrong with the gross load profile - it should not be excluded from initial calcs that look for gross load in net_load_ac (etc.)
# # Therefore, be very careful about when this removal of sites occurs.

# # Remove sites that have been flagged to contain issues.
# output_df = output_df[output_df['manual_check_required'] != 1]
# # output_df = output_df[output_df['issue_with_gross_load'] != 1]
# print('yay progressed past removing erroneous data')

# # Run code to get load for single load cids
# output_df = util.get_gross_load_for_single_load_cid_sites(output_df, META_DATA_FILE_PATH, load_list_extended, pv_list, DATA_DATE)

# # Print to csv
# output_df.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_singles_gross_load_' +str(TIME_INTERVAL)+'_sec_v3.csv')