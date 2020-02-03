


#------------------------ Step 0: Import required packages ------------------------
# Import packages required for program
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', 500)
# pd.set_option('display.max_rows', 500)
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
# Inputs
# REGION = 'south_australia'
# TIME_INTERVALS = 30
# DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_2017_03_03_v2.csv'
# META_DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_c_id_info_v2_NS.csv'
# INVERTER_DATA_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_site_info_v2_NS.csv'
# DATA_DATE = '2017_03_03'
# # NOTE don't forget the date!^

REGION = 'victoria'
TIME_INTERVALS = 30
DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_2018_01_18_v2.csv'
META_DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_c_id_info_v2_NS.csv'
INVERTER_DATA_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_site_info_v2_NS.csv'
DATA_DATE = '2018_01_18'
# NOTE don't forget the date!^

# Fraction of data allowed in 'other' polarity before being flagged as mixed polarity (note 0.01 = 1%)
FRACTION_FOR_MIXED_POLARITY = 0.01
LOAD_FRACTION_FOR_MIXED_POLARITY = 0.01
PV_GEN_START_HR = '05:00'
PV_GEN_END_HR = '20:00'

load_list = ['ac_load_net', 'ac_load']
pv_list = ['pv_site_net', 'pv_site']

# Time at which event occurs (t_0)
# # SA 30 sec
# t_0 = datetime.datetime(year= 2017, month= 3, day= 3, hour= 15, minute= 3, second= 25)
# SA 5 sec - TODO
# # Vic 5 sec
# t_0 = datetime.datetime(year= 2018, month= 1, day= 18, hour= 15, minute= 18, second= 50)
# Vic 30 sec
t_0 = datetime.datetime(year= 2018, month= 1, day= 18, hour= 15, minute= 18, second= 55)

# Estimate of when all PV systems are back on line (from visualisation)
# # SA 30 sec
# T_START_T_0 = '15:03:25'
# T_END_ESTIMATE = '15:15'
# T_END_ESTIMATE_NADIR = '15:06'
# # NOTE ^ the T_END_ESTIMATE_NADIR must be at least 2 time increments after T_0 (+1 and +2)
# # SA 5 sec - TODO
#  ...
# Vic 30 sec
T_START_T_0 = '15:18:55'
T_END_ESTIMATE = '15:30:25'
T_END_ESTIMATE_NADIR = '15:25'
# # Vic 5 sec
# T_START_T_0 = '15:18:50'
# T_END_ESTIMATE = '15:30'
# Check the below!!!
# T_END_ESTIMATE_NADIR = '15:25'

# Enter a value (in kW) below which will be counted as 'zero' when finding first and second order derivatives of power_kW
POWER_KW_EFFECTIVE_ZERO_FOR_DERIVS = 0.1

# Values to be considered zero when finding 'minimum' value for p_nadir. Need this because sometimes a slightly negative value is recorded part way through nadir and this is returned as the nadir.
POWER_ROUND_TO_ZERO_VAL_KW = 0.1

# 30% fairly arbritary. Help to try and capture 'soft' turning points for ramp up.
ACCELERATION_FRACTION_CONSIDERED_SUFFICIENT_FOR_RAMP_START_OR_END = 0.1

# For categories analysis
RIDE_THROUGH_PERCENTAGE_DROP_MAX = 0.04
DIP_PERCENTAGE_DROP_MAX = 0.10
CAT_3_NADIR_DROP_MAX = 0.25
CAT_4_NADIR_DROP_MAX = 0.50
CAT_5_NADIR_DROP_MAX = 0.75
# Values to be considered zero when finding 'disconnect' category.
DISCONNECT_CAT_APPROX_ZERO_KW = 0.1

# Percentage return val - this will be used to assess total response time, i.e. 't_to_return_within_10_percent' - default is 0.1 (i.e. 10%)
PERCENTAGE_RETURN_MINIMUM = 0.1

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!



#------------------------ Step 1: Get data ------------------------
data = solar_analytics.get_data_using_file_path(REGION, TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH)

# Clean: remove duplicate profiles
data = util.find_and_delete_duplicate_profiles(data)

# Get c_id_info df, this df will contain analysis output (i.e. nadir, ramp rates etc.)
output_df = pd.read_csv("/mnt/f/05_Solar_Analytics/" + META_DATA_FILE_PATH, index_col='c_id')
# NOTE Minor clean - check if ever using a different file above ^ 
output_df = output_df[['site_id', 'con_type']]


#------------------------ Step 2: Make output df ------------------------

# Filter out c_ids not in data
# NOTE - it is possible that there are c_ids in the data which are not in the meta data file - worth checking! Checked - this is fine, same number of c_ids in both.
c_ids_data = data['c_id'].drop_duplicates().tolist()
output_df = output_df.loc[c_ids_data]

# Get two separate lists of c_ids remaining which are load / PV
pv_cids = output_df[output_df['con_type'].isin(pv_list)]
pv_cids = pv_cids.index.values.tolist()
load_cids = output_df[output_df['con_type'].isin(load_list)]
load_cids = load_cids.index.values.tolist()

# Add new columns for characteristics to be found, NOTE t_x is start of ramp up, t_y is end of ramp up
output_df['t_0'] = np.nan
output_df['t_nadir'] = np.nan
output_df['p_0'] = np.nan
output_df['p_nadir'] = np.nan
output_df['t_x'] = np.nan
output_df['t_y'] = np.nan
output_df['p_x'] = np.nan
output_df['p_y'] = np.nan
output_df['t_0_plus1'] = np.nan
output_df['t_0_plus2'] = np.nan
output_df['p_0_plus1'] = np.nan
output_df['p_0_plus2'] = np.nan
output_df['t_when_p_within_10_percent'] = np.nan
# output_df['interpolated_t_when_p_within_10_percent'] = np.nan

# Calculated values
output_df['t_at_nadir'] = np.nan

output_df['t_to_ramp_down'] = np.nan
output_df['t_to_ramp_up'] = np.nan

output_df['t_to_return_within_10_percent'] = np.nan

output_df['p_diff_from_p0_to_pnadir'] = np.nan
output_df['p_diff_from_px_to_py'] = np.nan

output_df['percentage_drop_to_nadir'] = np.nan
output_df['percentage_drop_to_p_0_plus1'] = np.nan
output_df['percentage_drop_to_p_0_plus2'] = np.nan

output_df['ramp_down_rate'] = np.nan
output_df['ramp_up_rate'] = np.nan

# Categories
output_df['cat_1_ride_through'] = 0
output_df['cat_2_dip'] = 0
output_df['cat_3_mild_curtail'] = 0
output_df['cat_4_medium_curtail'] = 0
output_df['cat_5_signiifcant_curtail'] = 0
output_df['cat_6_severe_curtail'] = 0
output_df['cat_7_disconnect'] = 0
output_df['cat_3456_any_curtail'] = 0

# Error codes
# error_1: no data at t_0
output_df['error_1'] = np.nan
# error_2: no data at t_0 (for p_0)
output_df['error_2'] = np.nan
# error_3: no data at all over period - so no t_nadir possible
output_df['error_3'] = np.nan
# error_4: oh dear, the acceleration fraction thing did not work for max - have used the first (larger) maximum to get t_x
output_df['error_4'] = np.nan
# error_5: Not even able to just use the more extreme maximum!
output_df['error_5'] = np.nan
# error_6: 'oh dear, the acceleration fraction thing did not work for min - have used the first (larger) minimum to get t_y
output_df['error_6'] = np.nan
# error_7: Not even able to just use the more extreme minimum!
output_df['error_7'] = np.nan
# error_8: No data at t_x
output_df['error_8'] = np.nan
# error_9: No data at t_y
output_df['error_9'] = np.nan
# error_10: no data at t_0 when getting t_0_plus1 etc.
output_df['error_10'] = np.nan
# # error_11: could not categorise since some value or other missing - refer to other error codes!
# output_df['error_11'] = np.nan
# error_12: no data at t_0 when getting total response time
output_df['error_12'] = np.nan

#------------------------ Step 3: Apply polarity correction to data THEN calc power ------------------------
# Get error flags
error_flags_df = get_error_flags.get_error_flags(REGION, TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH, DATA_DATE, FRACTION_FOR_MIXED_POLARITY, LOAD_FRACTION_FOR_MIXED_POLARITY, PV_GEN_START_HR, PV_GEN_END_HR, load_list, pv_list)
print(error_flags_df)
# Loop through c_ids in data and apply polarity_fix
for c_id in c_ids_data:
    
    # Get polarity
    c_id_polarity = error_flags_df.loc[c_id,'polarity_fix']
    # print(c_id_polarity)

    # If the polarity is negative (-1) then *-1, else no operation required.
    if c_id_polarity == -1.0 :

        # Multiplies the values in data in the energy column for which c_id is the current c_id by -1
        data.loc[data['c_id'] == c_id, 'energy'] *= c_id_polarity


# # Export data to csv and check in tableau - the polarity check seems to be working :)
# data.to_csv('output_csv_files/TEST_DATA_' + REGION + '_' + DATA_DATE + '_' +str(TIME_INTERVALS)+'_sec_v2.csv')

# Calculate power
data = util.calculate_power_from_energy(data, str(TIME_INTERVALS) + '_sec')


#------------------------ Step 4: Find 'easy' things ------------------------
# The problem I've been trying to address is that the 'minimum' may not be the first point of nadir if there's a sneaky negative later on, so need to round power down. 
# Loop through c_ids and get time, power at start (t_0)
for c_id in c_ids_data:

    # c_id = 31176
    # print(c_id)
    # c_id = 28524
    # c_id = 22785
    # c_id = 39651

    # Print t_0 to output_df
    output_df.loc[c_id, 't_0'] = t_0
    # Get data for this c_id only
    c_id_data = data[data['c_id'] == c_id]

    # Sometimes there isn't data at t_0, so use exception to avoid errors
    try:
        # Extract power at t_0
        p_0 = c_id_data.loc[t_0,'power_kW']
        # Print p_0 to output_df
        output_df.loc[c_id, 'p_0'] = p_0   
    except:
        print('no data at t_0')
        # Record error code
        output_df.loc[c_id, 'error_1'] = 1.0


    # Filter c_id_data for limited time period - NOTE be very careful will this, now filters for SHORT time period
    c_id_data = c_id_data.between_time(T_START_T_0, T_END_ESTIMATE_NADIR)


    try:
        # Round power to zero for values smaller than POWER_ROUND_TO_ZERO_VAL_KW
        c_id_data['power_kW_round_to_zero'] = c_id_data['power_kW']
        c_id_data.loc[c_id_data['power_kW_round_to_zero'] <= POWER_ROUND_TO_ZERO_VAL_KW, 'power_kW_round_to_zero'] = 0.0
        # Find minimum power_kW value using rounded version
        p_nadir = c_id_data['power_kW_round_to_zero'].min()

        # find first time where p_nadir occurs and print to output_df
        # Sometimes there are multiple occurences of the minimum, therefore t_nadir is not a single data point, but multiple, stored in some format.
        t_nadir = c_id_data.index[c_id_data['power_kW_round_to_zero'] == p_nadir]

        # Specify the first entry since sometimes this is a list thing instead of a single data point thing...
        # The exception means that it will be skipped if there is nothing in the list to get (i.e. 'no data at t_0' from above is true too) 
        output_df.loc[c_id, 't_nadir'] = t_nadir[0]

        # Now find p_nadir_actual using t_nadir
        p_nadir_actual = c_id_data.loc[t_nadir[0],'power_kW']
        output_df.loc[c_id, 'p_nadir'] = p_nadir_actual

    except:
        print('no data')
        # Record error code
        output_df.loc[c_id, 'error_2'] = 1.0


    #------------------------ Step 5: Get t_0 + 1 and 2 interval vals ------------------------
    # Need to do this before step 6 because in step 6 the data is cut from t_nadir onwards and this may not include the values sought!
    # Need exception because for some sites data doesn't exist, therefore no t_0
    try:
        # First get the index location for t_0_plus1
        index_loc_for_t_0_plus1 = c_id_data.index.get_loc(t_0) + 1
        t_0_plus1 = c_id_data.index[index_loc_for_t_0_plus1]
        output_df.loc[c_id, 't_0_plus1'] = t_0_plus1

        # t_0_plus2
        index_loc_for_t_0_plus2 = c_id_data.index.get_loc(t_0) + 2
        t_0_plus2 = c_id_data.index[index_loc_for_t_0_plus2]
        output_df.loc[c_id, 't_0_plus2'] = t_0_plus2

        # Extract power at t_0_plus1 and print to output_df
        p_0_plus1 = c_id_data.loc[t_0_plus1,'power_kW']
        output_df.loc[c_id, 'p_0_plus1'] = p_0_plus1           

        # Extract power at t_0_plus2 and print to output_df
        p_0_plus2 = c_id_data.loc[t_0_plus2,'power_kW']
        output_df.loc[c_id, 'p_0_plus2'] = p_0_plus2  

    except:
        print('no data at t_0 when getting t_0_plus1 etc.')
        # Record error code
        output_df.loc[c_id, 'error_10'] = 1.0   


#------------------------ Step 6: Calculate things from data I ------------------------
output_df['t_to_ramp_down'] = (output_df['t_nadir'] - output_df['t_0']).astype('timedelta64[s]')
output_df['p_diff_from_p0_to_pnadir'] = output_df['p_nadir'] - output_df['p_0']

output_df['percentage_drop_to_nadir'] = output_df['p_diff_from_p0_to_pnadir'] / output_df['p_0']
output_df['percentage_drop_to_p_0_plus1'] = (output_df['p_0_plus1'] - output_df['p_0']) / output_df['p_0']
output_df['percentage_drop_to_p_0_plus2'] = (output_df['p_0_plus2'] - output_df['p_0']) / output_df['p_0']

output_df['ramp_down_rate'] = output_df['p_diff_from_p0_to_pnadir'] / output_df['t_to_ramp_down']


#------------------------ Step 7: Assigning Categories ------------------------
# Don't know whether I'm going to have to apply this to each c_id individually / row by row
# c_id = 35046
for c_id in c_ids_data:

    # Check for disconnect first - i.e. if p_nadir <= 0.1kW and p_0 > 0.1kW (or other set limit!)
    if output_df.loc[c_id,'p_nadir'] <= DISCONNECT_CAT_APPROX_ZERO_KW and output_df.loc[c_id,'p_0'] > DISCONNECT_CAT_APPROX_ZERO_KW:
        output_df.loc[c_id, 'cat_7_disconnect'] = 1

    # Ride through if the max percentage drop between t_0 and both 1 and 2 periods later is less than the set val (~1%)
    if max(abs(output_df.loc[c_id,'percentage_drop_to_p_0_plus1']), abs(output_df.loc[c_id,'percentage_drop_to_p_0_plus2'])) <= RIDE_THROUGH_PERCENTAGE_DROP_MAX:
        output_df.loc[c_id,'cat_1_ride_through'] = 1

    # Slight dip if power two periods after t_0 has bounced back up, and the drop to that first period after t_0 is less than the set val (~5%) and cat 1 is not true
    if (abs(output_df.loc[c_id,'p_0_plus1']) < abs(output_df.loc[c_id,'p_0_plus2'])) and abs(output_df.loc[c_id, 'percentage_drop_to_p_0_plus1']) <= DIP_PERCENTAGE_DROP_MAX and output_df.loc[c_id, 'cat_1_ride_through'] != 1:
        output_df.loc[c_id, 'cat_2_dip'] = 1

    # Curtail mild (cat 3) if percentage drop to nadir is less than set val (25%) and 'slight dip' (cat 2) is false and ride through (cat 1) is false
    if abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) <= CAT_3_NADIR_DROP_MAX and output_df.loc[c_id, 'cat_2_dip'] != 1 and output_df.loc[c_id, 'cat_1_ride_through'] != 1:
        output_df.loc[c_id, 'cat_3_mild_curtail'] = 1

    # Curtail medium (cat 4) if percentage drop to nadir is less than set val (50%) and greater than cat 3 set val (25%)
    if abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) <= CAT_4_NADIR_DROP_MAX and abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) > CAT_3_NADIR_DROP_MAX:
        output_df.loc[c_id, 'cat_4_medium_curtail'] = 1

    # Curtail medium (cat 5) if percentage drop to nadir is less than set val (75%) and greater than cat 3 set val (50%)
    if abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) <= CAT_5_NADIR_DROP_MAX and abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) > CAT_4_NADIR_DROP_MAX:
        output_df.loc[c_id, 'cat_5_signiifcant_curtail'] = 1

    # Extreme curtail (cat 6) if percentage drop to nadir is greater than set val (75%) and disconnect (cat 7) is false
    if abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) > CAT_5_NADIR_DROP_MAX and output_df.loc[c_id, 'cat_7_disconnect'] != 1:
        output_df.loc[c_id, 'cat_6_severe_curtail'] = 1

    # Catch all for curtail - take max of cat 3, 4, 5, 6
    output_df.loc[c_id, 'cat_3456_any_curtail'] = max(output_df.loc[c_id, 'cat_3_mild_curtail'], output_df.loc[c_id, 'cat_4_medium_curtail'], output_df.loc[c_id, 'cat_5_signiifcant_curtail'], output_df.loc[c_id, 'cat_6_severe_curtail'])


#------------------------ Step 8: Find time at which returned to within PERCENTAGE_RETURN_MINIMUM (10%) of p_0 ------------------------

# First get list of c_ids for which the percentage drop to nadir is greater than the PERCENTAGE_RETURN_MINIMUM (i.e. it needs to drop by more than 10% to return to within 10%)
# NOTE percentage_drop_to_nadir is a negative value, therefore the greater in magnitude drops will be less than negative (abs(PERCENTAGE_RETURN_MINIMUM))
output_df_10_percent_drop_min = output_df[output_df['percentage_drop_to_nadir'] < -abs(PERCENTAGE_RETURN_MINIMUM)]
print(output_df_10_percent_drop_min)

# Get unique c_ids from the filtered df to a list (noting that c_id is stored in the index!!!)
c_id_list_10_percent_drop = output_df_10_percent_drop_min.index.drop_duplicates().tolist()
print(c_id_list_10_percent_drop)


for c_id in c_id_list_10_percent_drop:

    # # Test c_id - disconnect site
    # c_id = 36013

    c_id_data = data[data['c_id'] == c_id]

    # Try / exception because not all sites will have data at t_0_plus1
    try:
        t_0_plus1 = output_df.loc[c_id, 't_0_plus1'].to_datetime()
        # Only consider from times after the t_0 has happened - this may seem like absurb code - it was a pain to write!!! between_time is finicky.
        hour_t_0_plus1 = t_0_plus1.hour
        minute_t_0_plus1 = t_0_plus1.minute
        second_t_0_plus1 = t_0_plus1.second
        # Combine into string
        time_string_t_0_plus1 = str(hour_t_0_plus1) + ':' + str(minute_t_0_plus1) + ':' + str(second_t_0_plus1)
        c_id_data = c_id_data.between_time(time_string_t_0_plus1, T_END_ESTIMATE)

        # Get p_0 from output_df and get 90% times this value
        p_0 = output_df.loc[c_id, 'p_0']
        p_within_10_percent =  p_0 * (1 - PERCENTAGE_RETURN_MINIMUM)

        # Filter data for times where power is bigger or equal to this value 
        c_id_data = c_id_data[c_id_data['power_kW'] >= p_within_10_percent]
        c_id_data = c_id_data.sort_index()

        # Get first time from index and record to output_df
        t_when_p_within_10_percent = c_id_data.index[0]
        output_df.loc[c_id, 't_when_p_within_10_percent'] = t_when_p_within_10_percent

    except:
        print('no data at t_0 when getting total response time')
        # Record error code
        output_df.loc[c_id, 'error_12'] = 1.0       

#------------------------ Step 6: Calculate things from data II ------------------------
# Proxy for total response time, the t_to_return_within_10_percent is equal to 
output_df['t_to_return_within_10_percent'] = (output_df['t_when_p_within_10_percent'] - output_df['t_0']).astype('timedelta64[s]')




# NOTE COMMENTING OUT STEPS 9 and 10 BECAUSE NOT AS ACCURATE AS I WOULD LIKE IT TO BE AND NOT NECESSARY FOR IEEE PAPER - TBC!

#------------------------ Step 9: Find points based on derivatives ------------------------

for c_id in c_ids_data:

    # Get data for this c_id only
    c_id_data = data[data['c_id'] == c_id]
    # Filter c_id_data for limited time period
    c_id_data = c_id_data.between_time(T_START_T_0, T_END_ESTIMATE)

    # Calculate first and second derivatives
    c_id_data = util.calculate_power_kW_first_and_second_derivative(c_id_data, POWER_KW_EFFECTIVE_ZERO_FOR_DERIVS)
    # print(c_id_data)

    try:
        # Need exception bcause it's possible there's no data and therefore no t_nadir

        # First get t_nadir from df_outputs
        t_nadir_val = output_df.loc[c_id,'t_nadir'].to_datetime()
        # Only consider from times after the nadir has happened - this may seem like absurb code - it was a pain to write!!! between_time is finicky.
        hour_nadir = t_nadir_val.hour
        minute_nadir = t_nadir_val.minute
        second_nadir = t_nadir_val.second
        # Combine into string
        time_string_nadir = str(hour_nadir) + ':' + str(minute_nadir) + ':' + str(second_nadir)
        # Filter data
        c_id_data = c_id_data.between_time(time_string_nadir, T_END_ESTIMATE)
        # print(c_id_data)

        # Find max 2 and min 2 values in second deriv
        two_largest_derivs = c_id_data.nlargest(2,'power_kW_second_deriv')
        two_smallest_derivs = c_id_data.nsmallest(2,'power_kW_second_deriv')

        # Combine into single df and sort index
        all_derivs = pd.concat([two_largest_derivs, two_smallest_derivs])
        all_derivs = all_derivs[['power_kW_second_deriv']]
        all_derivs = all_derivs.sort_values('power_kW_second_deriv')
        # print(all_derivs)


        try:
            # Consider maximum 2 second derivs. 
            # Calculate the ratio of acceleration A to B (to capture 'soft' turning points)
            # print(all_derivs.iloc[2])
            # print(all_derivs.iloc[3])
            max_acceleration_fraction =abs(all_derivs.iloc[2] / all_derivs.iloc[3])
            # print(max_acceleration_fraction)

            if max_acceleration_fraction.values >= ACCELERATION_FRACTION_CONSIDERED_SUFFICIENT_FOR_RAMP_START_OR_END:
                # If the less extreme max is sufficiently large, then keep it as the t_x point
                # First get the index location in c_id_data index
                index_loc_for_t_x = c_id_data.index.get_loc(all_derivs.index[2]) + 1
                # Then get the actual value of t_x
                t_x = c_id_data.index[index_loc_for_t_x]
                output_df.loc[c_id, 't_x'] = t_x
            else:
                # If the less extreme max is NOT sufficiently large, then use the larger max to find the turning point
                # First get the index location in c_id_data index
                index_loc_for_t_x = c_id_data.index.get_loc(all_derivs.index[3]) + 1
                t_x = c_id_data.index[index_loc_for_t_x]
                output_df.loc[c_id, 't_x'] = t_x    

        except:
            print('oh dear, the acceleration fraction thing did not work for max - have used the first (larger) maximum to get t_x')
            # Record error code
            output_df.loc[c_id, 'error_4'] = 1.0    
            try:
                index_loc_for_t_x = c_id_data.index.get_loc(all_derivs.index[3]) + 1
                t_x = c_id_data.index[index_loc_for_t_x]
            except:
                print('Not even able to just use the more extreme maximum!')
                # Record error code
                output_df.loc[c_id, 'error_5'] = 1.0

        # print(t_x)

        try:
            # Consider minimum 2 second derivs. 
            # Calculate the ratio of acceleration A to B (to capture 'soft' turning points)
            min_acceleration_fraction = abs(all_derivs.iloc[1] / all_derivs.iloc[0])

            if min_acceleration_fraction.values >= ACCELERATION_FRACTION_CONSIDERED_SUFFICIENT_FOR_RAMP_START_OR_END:
                # If the less extreme min is sufficiently large, then keep it as the t_y point
                # First get the index location in c_id_data index
                index_loc_for_t_y = c_id_data.index.get_loc(all_derivs.index[1]) + 1
                t_y = c_id_data.index[index_loc_for_t_y]
                output_df.loc[c_id, 't_y'] = t_y
            else:
                # If the less extreme min is NOT sufficiently large, then use the larger min to find the turning point
                index_loc_for_t_y = c_id_data.index.get_loc(all_derivs.index[0]) + 1
                t_y = c_id_data.index[index_loc_for_t_y]
                output_df.loc[c_id, 't_y'] = t_y    

        except:
            print('oh dear, the acceleration fraction thing did not work for min - have used the first (larger) minimum to get t_y')
            # Record error code
            output_df.loc[c_id, 'error_6'] = 1.0
            
            try:
                index_loc_for_t_y = c_id_data.index.get_loc(all_derivs.index[0]) + 1
                t_y = c_id_data.index[index_loc_for_t_y]
            except:
                print('Not even able to just use the more extreme minimum!')
                # Record error code
                output_df.loc[c_id, 'error_7'] = 1.0

        # print(t_y)    


    except:
        # Record error code
        output_df.loc[c_id, 'error_3'] = 1.0

    #------------------------ Step 7: Get p_x and p_y ------------------------
    try:
        # Extract power at t_x
        p_x = c_id_data.loc[t_x,'power_kW']
        # Print p_0 to output_df
        output_df.loc[c_id, 'p_x'] = p_x   
    except:
        print('no data at t_x')
        # Record error code
        output_df.loc[c_id, 'error_8'] = 1.0

    try:
        # Extract power at t_y
        p_y = c_id_data.loc[t_y,'power_kW']
        # Print p_0 to output_df
        output_df.loc[c_id, 'p_y'] = p_y   
    except:
        print('no data at t_y')
        # Record error code
        output_df.loc[c_id, 'error_9'] = 1.0    


# print(output_df)


#------------------------ Step 8: Calculate things from data III ------------------------
# Get output_df['t_at_nadir']
output_df['t_at_nadir'] = (output_df['t_x'] - output_df['t_nadir']).astype('timedelta64[s]')
output_df['t_to_ramp_up'] = (output_df['t_y'] - output_df['t_x']).astype('timedelta64[s]')
output_df['p_diff_from_px_to_py'] = output_df['p_y'] - output_df['p_x']
output_df['ramp_up_rate'] = output_df['p_diff_from_px_to_py'] / output_df['t_to_ramp_up']


#------------------------ Step 9: Merge on meta data plus error flags ------------------------
# Merge meta data (on site id) to show inverter type etc.
# Get meta data
site_data = pd.read_csv("/mnt/f/05_Solar_Analytics/" + INVERTER_DATA_PATH)
# Combine time series and meta data
output_df = output_df.reset_index().merge(site_data, how = 'left', on='site_id').set_index('c_id')

# First clean the error_flags_df to remove duplicate cols
error_flags_df = error_flags_df.drop(['site_id', 'con_type'], axis=1)
output_df = output_df.join(error_flags_df, how = 'left')

# output_df = output_df.reset_index().join(error_flags_df, how = 'left').set_index('c_id')

output_df.to_csv('output_csv_files/extreme_response_characteristics_' + REGION + '_' + DATA_DATE + '_' +str(TIME_INTERVALS)+'_sec.csv')