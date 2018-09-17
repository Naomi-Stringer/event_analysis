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
import util


# Inputs
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
REGION = 'QLD'
TIME_INTERVAL = 60 #5 or 30 or 60
DATA_FILE_PATH = '2018-09-03_solar_analytics_data_transfer/2018-08-25_sa_qld_naomi.csv'
META_DATA_FILE_PATH = '2018-09-03_solar_analytics_data_transfer/circuit_details_TB_V6.csv'
INVERTER_DATA_PATH = '2018-09-03_solar_analytics_data_transfer/site_details.csv'

DATA_DATE = '25_august_2018'

# For getting error flags
FRACTION_FOR_MIXED_POLARITY = 0.01
LOAD_FRACTION_FOR_MIXED_POLARITY = 0.01
PV_GEN_START_HR = '05:00'
PV_GEN_END_HR = '20:00'
load_list = ['ac_load_net', 'ac_load']
pv_list = ['pv_site_net', 'pv_site']


# For getting extreme response characteristics (categories analysis)
t_0 = datetime.datetime(year= 2018, month= 8, day= 25, hour= 13, minute= 11, second= 55)
T_START_T_0 = '13:11:55'
T_END_ESTIMATE = '13:30:55'
T_END_ESTIMATE_NADIR = '13:13:55'
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

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


#------------------------ Import data ------------------------
data = solar_analytics.get_august_data_using_file_path(TIME_INTERVAL, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH)

#------------------------ Filter ------------------------
output_df = data[data['s_state'] == REGION]

#------------------------ Print to csv ------------------------
# NOTE - you will need to set up an 'output_csv_files' folder in the same folder where you save this python file. The output csv will be saved to this folder.
output_df.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_utc_corrected_' +str(TIME_INTERVAL)+'_sec_v8.csv')


# #------------------------ Get site capacity factor for PV gen ------------------------
# site_df = util.get_pv_CF_by_site(output_df, pv_list, MINUTE_NOW_START)
# # Print outcome to csv
# site_df.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_approx_cap_factor_by_site_id_' +str(TIME_INTERVAL)+'_sec_v4.csv')


# #------------------------ Get categories ananlysis - SLOW TO RUN! ------------------------
# extreme_response_characteristics = util.get_extreme_response_characteristics(REGION, TIME_INTERVAL, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH, DATA_DATE, load_list, pv_list, t_0, T_START_T_0, T_END_ESTIMATE, T_END_ESTIMATE_NADIR, POWER_ROUND_TO_ZERO_VAL_KW, RIDE_THROUGH_PERCENTAGE_DROP_MAX, DIP_PERCENTAGE_DROP_MAX, CAT_3_NADIR_DROP_MAX, CAT_4_NADIR_DROP_MAX, CAT_5_NADIR_DROP_MAX, DISCONNECT_CAT_APPROX_ZERO_KW, PERCENTAGE_RETURN_MINIMUM)
# # Print to csv
# extreme_response_characteristics.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_cats_' +str(TIME_INTERVAL)+'_sec_v8.csv')