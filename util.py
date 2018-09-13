# Util module
# List of useful functions


# Import required things
import numpy as np
import pandas as pd
import calendar
import datetime

import solar_analytics


def get_extreme_response_characteristics(REGION, TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH, DATA_DATE, load_list, pv_list, t_0, T_START_T_0, T_END_ESTIMATE, T_END_ESTIMATE_NADIR, POWER_ROUND_TO_ZERO_VAL_KW, RIDE_THROUGH_PERCENTAGE_DROP_MAX, DIP_PERCENTAGE_DROP_MAX, CAT_3_NADIR_DROP_MAX, CAT_4_NADIR_DROP_MAX, CAT_5_NADIR_DROP_MAX, DISCONNECT_CAT_APPROX_ZERO_KW, PERCENTAGE_RETURN_MINIMUM):
    """Categorises PV response"""

    #------------------------ Step 1: Get data ------------------------
    # IF 25 August 2018 data then need to use different fnct in factory to get data
    # Change data columns names IF 25 August 2018 data (differently named)
    if DATA_DATE == '25_august_2018':
        data = solar_analytics.get_august_data_using_file_path(TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH)
        # Change column names for frequency and energy
        data = data.rename(columns = {'e':'energy', 'f':'frequency'})
        data.index.names = ['t_stamp']
        print(data.head())

    else:
        data = solar_analytics.get_data_using_file_path(REGION, TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH)
        # print(data)


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

    # #------------------------ Step 3: Apply polarity correction to data THEN calc power ------------------------
    # # Get error flags
    # error_flags_df = get_error_flags.get_error_flags(REGION, TIME_INTERVALS, DATA_FILE_PATH, META_DATA_FILE_PATH, INVERTER_DATA_PATH, DATA_DATE, FRACTION_FOR_MIXED_POLARITY, LOAD_FRACTION_FOR_MIXED_POLARITY, PV_GEN_START_HR, PV_GEN_END_HR, load_list, pv_list)
    # print(error_flags_df)
    # # Loop through c_ids in data and apply polarity_fix
    # for c_id in c_ids_data:
        
    #     # Get polarity
    #     c_id_polarity = error_flags_df.loc[c_id,'polarity_fix']
    #     # print(c_id_polarity)

    #     # If the polarity is negative (-1) then *-1, else no operation required.
    #     if c_id_polarity == -1.0 :

    #         # Multiplies the values in data in the energy column for which c_id is the current c_id by -1
    #         data.loc[data['c_id'] == c_id, 'energy'] *= c_id_polarity


    # Calculate power
    data = calculate_power_from_energy(data, str(TIME_INTERVALS) + '_sec')


    #------------------------ Step 4: Find 'easy' things ------------------------
    # The problem I've been trying to address is that the 'minimum' may not be the first point of nadir if there's a sneaky negative later on, so need to round power down. 
    # Loop through c_ids and get time, power at start (t_0)
    for c_id in c_ids_data:

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

    return output_df