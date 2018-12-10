# Util module
# List of useful functions


# Import required things
import numpy as np
import pandas as pd
import calendar
import datetime

import solar_analytics

#------------------------ Add PV is X flag ------------------------

def pv_is_x_flag(input_df, x_flag) :

    input_df['pv_' + str(x_flag) + '_flag'] = np.nan
    input_df.loc[(input_df.energy == x_flag) & (input_df.con_type == 'pv_site_net'),'pv_' + str(x_flag) + '_flag'] = 1

    # Count and return the number of 'zero' events
    count_pv_x_events = input_df['pv_' + str(x_flag) + '_flag'].sum()
    print('The following number of PV generation = zero events occured:')
    print(count_pv_x_events)

    return input_df



#------------------------ Add high and low voltage excursion flags ------------------------

def high_and_low_v_flags_and_vals(input_df, v_upper_lim, v_lower_lim) : 
    """Input df, v upper and lower limits. Outputs df containing high and low voltage flags where voltage is outside limits. """
    
    # Create new empty columns
    input_df['v_max_high_voltage_flag'] = np.nan
    input_df['v_max_low_voltage_flag'] = np.nan
    input_df['v_min_high_voltage_flag'] = np.nan
    input_df['v_min_low_voltage_flag'] = np.nan

    # Find excursions in the high voltage measurements
    input_df.loc[input_df.voltage_max >= v_upper_lim, 'v_max_high_voltage_flag'] = 1
    input_df.loc[input_df.voltage_max <= v_lower_lim, 'v_max_low_voltage_flag'] = 1

    # Find excursions in the high voltage measurements
    input_df.loc[input_df.voltage_min >= v_upper_lim, 'v_min_high_voltage_flag'] = 1
    input_df.loc[input_df.voltage_min <= v_lower_lim, 'v_min_low_voltage_flag'] = 1

    # Create new columns containing zeroes where no voltage excursion has occured, and the voltage value where an excursion has occured
    # v-max first
    input_df['v_max_high_voltage_vals'] = input_df.v_max_high_voltage_flag * input_df.voltage_max
    input_df['v_max_low_voltage_vals'] = input_df.v_max_low_voltage_flag * input_df.voltage_max
    # then v-min
    input_df['v_min_high_voltage_vals'] = input_df.v_min_high_voltage_flag * input_df.voltage_min
    input_df['v_min_low_voltage_vals'] = input_df.v_min_low_voltage_flag * input_df.voltage_min

    # Count number of voltage excursions
    num_v_max_high_v_excursions = input_df['v_max_high_voltage_flag'].sum()
    num_v_max_low_v_excursions = input_df['v_max_low_voltage_flag'].sum()   
    num_v_min_high_v_excursions = input_df['v_min_high_voltage_flag'].sum() 
    num_v_min_low_v_excursions = input_df['v_min_low_voltage_flag'].sum() 


    # Store both output in a tuple so they can be 'unpacked' by the function call
    fnct_outputs = (input_df, num_v_max_high_v_excursions, num_v_max_low_v_excursions, num_v_min_high_v_excursions, num_v_min_low_v_excursions)

    # Return the tuple    
    return fnct_outputs




#------------------------ Find coincidence of two flags ------------------------

def get_coincidence_of_two_flag(input_df, flag_1_string, flag_2_string, new_flag_name_string) :
    """Finds where both flags are true and returns a new flag column. First two entries are flag strings to find coincidence of, the third entry is the new column name."""

    input_df[new_flag_name_string] = np.nan
    input_df.loc[(input_df[flag_1_string] == 1) & ( input_df[flag_2_string] == 1), new_flag_name_string] = 1

    return input_df

#------------------------ Take a df and divide into the three potential connection types ------------------------

def get_con_type_dfs(input_df) : 
    """Input a df and output there dfs, one for pv_site_net, ac_load_net, ac_load. Also a list of unique c_ids for each output df."""

    # Take subsets and define new dfs
    pv_df = input_df[input_df['con_type'] == 'pv_site_net']
    load_net_df = input_df[input_df['con_type'] == 'ac_load_net']
    load_df = input_df[input_df['con_type'] == 'ac_load']

    pv_c_ids = pv_df['c_id'].unique()
    load_net_c_ids = load_net_df['c_id'].unique()
    load_c_ids = load_df['c_id'].unique()

    # Make tuple
    fnct_outputs = (pv_df, load_net_df, load_df, pv_c_ids, load_net_c_ids, load_c_ids)

    # Return tuple
    return fnct_outputs


#------------------------ Find max value in series and round up to nearest 10 (for graphing) ------------------------

def get_max_and_roundup_ten (input_df, series_name_string) :
    max_val = input_df[series_name_string].max()
    rounded_max = round(max_val,-1) + 10
    return rounded_max

def get_max_and_roundup_one (input_df, series_name_string) :
    max_val = input_df[series_name_string].max()
    rounded_max = round(max_val,-1) + 1
    return rounded_max

#------------------------ Find max value in series and round up to nearest 10 (for graphing) ------------------------

def get_min_and_rounddown_ten (input_df, series_name_string) :
    min_val = input_df[series_name_string].min()
    rounded_min = round(min_val,-1) -10
    return rounded_min

def get_min_and_rounddown_one (input_df, series_name_string) :
    min_val = input_df[series_name_string].min()
    rounded_min = round(min_val,-1) -1
    return rounded_min
#------------------------ Remove outliers ------------------------

def remove_voltage_and_energy_outliers(df_input, voltage_upper_threshold, energy_upper_threshold, energy_lower_threshold) :
    """USE WITH EXTREME CAUTION!!!! EASY TO MIS-USE!!!! Note that thresholds are applied such that they are inclusive - i.e. values greater than the threshold are removed, whilst those equal to are kept."""

    df_input = df_input[df_input['voltage_max'] <= voltage_upper_threshold]
    df_input = df_input[df_input['voltage_min'] <= voltage_upper_threshold]
    df_input = df_input[df_input['energy'] <= energy_upper_threshold]  
    df_input = df_input[df_input['energy'] >= energy_lower_threshold]
    
    return(df_input)


#------------------------ Make pandas series (without t_stamp index!!!) out of unique values in a df col ------------------------

def get_unique_vals_as_series(input_df, col_name_string):
    """RETURNS A DF NOT A SERIES! Pass a df (with t_stamp index) and the col for which unique values are to be found. Returns a df which contains the unique vals. The index is values from 0,1,2,...)"""
    # Note: returns a pandas series with date time index and unique site_ids as a column (although the whole series name is site_id). 
    list_of_unique_vals = input_df[col_name_string].drop_duplicates()
    # This removes date time stamp from index and makes it a column instead!
    list_of_unique_vals = list_of_unique_vals.reset_index()
    # Drop time stamp column. 
    list_of_unique_vals = list_of_unique_vals.drop(['t_stamp'], axis = 1)

    return(list_of_unique_vals)



#------------------------ Make flag where energy drops between current and next interval by a certain percentage or greater ------------------------

def get_energy_drop_flags(input_df, ENERGY_CHANGE_THRESHOLD) :
    """Pass a df for a single c_id (with 'energy' col!!!) and the percentage threshold for energy change. Returns the same df with three new cols: one for energy change value, one for percentage, one with a flag where percentage is above threshold."""

    # ENERGY DROP FLAGS
    # New col - change in energy between current interval (i) and next interval (i+1). Increases shown as positive, decreases shown as negative.
    # Really slow when you use freq = '5min'. Removed: , freq = '5min'
    # For some reason, when using 'shift' function, cannot also rename the column when creating the df (just assigned nans)
    delta_energy = pd.DataFrame(input_df['energy'].shift(-1) - input_df['energy'], index = input_df.index)
    delta_energy = delta_energy.rename(columns = {'energy' : 'delta_energy'})
    input_df = pd.concat([input_df, delta_energy], axis = 1)

    # New col - percentage change, removed: columns=['fraction_change_energy']
    fraction_change_energy = pd.DataFrame(input_df['delta_energy'] / input_df['energy'], index = input_df.index, columns=['fraction_change_energy'])
    input_df = pd.concat([input_df, fraction_change_energy], axis = 1)

    # Flag cases where the percentage change is greater than the set value
    input_df['delta_energy_flag'] = np.nan
    input_df.loc[input_df.fraction_change_energy <= ENERGY_CHANGE_THRESHOLD, 'delta_energy_flag'] = 1

    return(input_df)

#------------------------ Make flag where energy drops between current and next interval by a certain percentage or greater ------------------------

def get_energy_drop_without_flags(input_df) :
    """Pass a df for a single c_id (with 'energy' col!!!) Returns the same df with two new cols: one for energy change value, one for percentage."""

    # ENERGY DROP FLAGS
    # New col - change in energy between current interval (i) and next interval (i+1). Increases shown as positive, decreases shown as negative.
    # Really slow when you use freq = '5min'. Removed: , freq = '5min'
    # For some reason, when using 'shift' function, cannot also rename the column when creating the df (just assigned nans)
    delta_energy = pd.DataFrame(input_df['energy'].shift(-1) - input_df['energy'], index = input_df.index)
    delta_energy = delta_energy.rename(columns = {'energy' : 'delta_energy'})
    input_df = pd.concat([input_df, delta_energy], axis = 1)

    # New col - percentage change, removed: columns=['fraction_change_energy']
    fraction_change_energy = pd.DataFrame(input_df['delta_energy'] / input_df['energy'], index = input_df.index, columns=['fraction_change_energy'])
    input_df = pd.concat([input_df, fraction_change_energy], axis = 1)

    return(input_df)


#------------------------ Make flag where energy drops between current and next interval by a certain percentage or greater ------------------------
def get_v_mid_pt_average_flags(df_input, VOLTAGE_LOWER_LIMIT, VOLTAGE_UPPER_LIMIT) :
    """Pass a df (with 'voltage_min' and 'voltage_max' cols!) and the upper and lower voltage thresholds. Calculated the voltage mid pt 10 min average, and flags cases outside thresholds."""

    # Make empty columns
    df_input['v_mid_pt_flag'] = np.nan
    df_input['v_mid_pt_averages_flag'] = np.nan

    # Find mid points, equal to 
    v_mid_pt = pd.DataFrame(df_input['voltage_min'] + (df_input['voltage_max'] - df_input['voltage_min'])/2, index = df_input.index, columns=['v_mid_pt'])
    df_input = pd.concat([df_input, v_mid_pt], axis = 1)

    # Calculate 10 minute averages
    v_mid_pt_averages = pd.DataFrame((df_input['v_mid_pt'] + df_input['v_mid_pt'].shift(1))/2, index = df_input.index)
    v_mid_pt_averages = v_mid_pt_averages.rename(columns = {'v_mid_pt':'v_mid_pt_averages'})
    df_input = pd.concat([df_input, v_mid_pt_averages], axis = 1)

    # Flag for mid point voltage is outside voltage range
    df_input.loc[df_input['v_mid_pt'] <= VOLTAGE_LOWER_LIMIT, 'v_mid_pt_flag'] = 1
    df_input.loc[df_input['v_mid_pt'] >= VOLTAGE_UPPER_LIMIT, 'v_mid_pt_flag'] = 1

    # Flag for mid point voltage average is outside voltage range
    df_input.loc[df_input['v_mid_pt_averages'] <= VOLTAGE_LOWER_LIMIT, 'v_mid_pt_averages_flag'] = 1
    df_input.loc[df_input['v_mid_pt_averages'] >= VOLTAGE_UPPER_LIMIT, 'v_mid_pt_averages_flag'] = 1

    return(df_input)


#------------------------ Takes state number and outputs the state name as a string ------------------------ 
def find_state_name(state_num) : 
    """Input state number as string (i.e. '2') and outputs the state name as a string (i.e. 'NSW')."""

    # NSW = 2, Vic = 3, Qld = 4, SA = 5, WA = 6, Tas = 7, NT = 8

    if state_num == '2' :
        state_name_str = 'NSW'
    
    elif state_num == '3' :
        state_name_str  = 'Vic'

    elif state_num == '4' :
        state_name_str  = 'Qld'

    elif state_num == '5' :
        state_name_str  = 'SA'

    elif state_num == '6' :
        state_name_str  = 'WA'

    elif state_num == '7' :
        state_name_str  = 'Tas'
    
    elif state_num == '8' :
        state_name_str  = 'NT'
    
    else :
        state_name_str = "State name error"

    # Return the name   
    return state_name_str


#------------------------ Create TWO and ONE (state) digit post code string columns ------------------------ 
def add_one_and_two_digit_postcode_cols(input_df) : 
    """Create two digit and one digit post code string columns. Input: a data frame containing a column called 's_postcode'. Output: a data frame with a new two digit post code column and one digit post code. Also a list of unique two digit and one digit (state) post codes."""

    # REQUIRES WORK - for now have just returned 2 dig post codes as strings rather than integers

    # First step, make new col containing four digit post code as a string
    input_df['postcode_string'] = input_df['s_postcode'].apply(str)
    input_df['postcode_string_clean'] = input_df['postcode_string'].str[:4]
    
    # Then extract first two digits
    input_df['two_digit_postcode_string'] = input_df['postcode_string'].str[:2]


    # Extract list of 2 digit post codes (as numpy ndim array)
    list_two_digits = input_df['two_digit_postcode_string'].unique()

    # Then extract first ONE digit
    input_df['one_digit_postcode_string'] = input_df['postcode_string'].str[:1]

    # Extract list of 2 digit post codes (as numpy ndim array)
    list_one_digit = input_df['one_digit_postcode_string'].unique()


    # Store both output in a tuple so they can be 'unpacked' by the function call
    fnct_outputs = (input_df, list_two_digits, list_one_digit)

    # Return the tuple    
    return fnct_outputs




#------------------------ Remove outliers ------------------------ 
def remove_v_outliers(input_df, vmax_threshold, vmin_threshold) : 
    """Accepts a df containing a voltage_max and voltage_min column, and two threshold values. Removes rows containing values above the threshold values. Returns df and number of outliers removed."""

    import numpy as np
    import pandas as pd
    import calendar
    

    # First, calc the num of outliers to be removed

    # Remove voltage max values above threshold
    input_df_vmax = input_df[input_df['voltage_max'] <= vmax_threshold]
    num_vmax_outliers = len(input_df) - len(input_df_vmax)
    
    # Remove voltage min values above threshold
    input_df_vmin = input_df[input_df['voltage_min'] <= vmin_threshold]
    num_vmin_outliers = len(input_df) - len(input_df_vmin)
    

    # Second, start with the fresh input_df and remove the vmax outliers, then the vmin outliers
    input_df = input_df[input_df['voltage_max'] <= vmax_threshold]
    input_df = input_df[input_df['voltage_min'] <= vmin_threshold]


    # Store both output in a tuple so they can be 'unpacked' by the function call
    fnct_outputs = (input_df, num_vmax_outliers, num_vmin_outliers)

    # Return the tuple    
    return fnct_outputs


#------------------------ Make column with energy scaled for 0-100% max generation in data set ------------------------ 
# Filter data for PV



#------------------------ Where the quality is poor, replace energy and voltage measurements with NaN ------------------------ 
# Note that q_score = 47 indicates poor quality data.

def remove_poor_quality_data(input_df):
    """ Takes a df containing q_score, energy, voltage_max and voltage_min. Replaces energy and voltage measurements with nan when q_score = 47."""
    input_df.loc[input_df['q_score'] == 47, 'energy'] = np.NaN
    input_df.loc[input_df['q_score'] == 47, 'voltage_max'] = np.NaN
    input_df.loc[input_df['q_score'] == 47, 'voltage_min'] = np.NaN

    if 'v_mid_pt_averages' in input_df:
        input_df.loc[input_df['q_score'] == 47, 'v_mid_pt_averages'] = np.NaN

    return input_df


def remove_poor_quality_data_not_just_replace_with_na(input_df):
    input_df = input_df[input_df['q_score'] != 47]
    return input_df


#------------------------ Calculate voltage mid point average for 5 minute vmax-vmin data ------------------------ 

def calc_v_mid_pt_10m_average(input_df):
    """Input df containing 5 minute data with v min and vmax. Outputs the same df but with a new col showing v mid pt (between min and max) and the 10 minute average."""
    # Create df to store output (i.e. data frame with all the v mid pts)
    data_output = pd.DataFrame()

    # Find unique c-ids for this site
    list_of_unique_c_ids = get_unique_vals_as_series(input_df, 'c_id')
    # get_unique_vals_as_series(input_df, 'c_id')
    # print(list_of_unique_c_ids)

    # Loop through unique cids for this site
    for cid in list_of_unique_c_ids['c_id'] :
        # Filter data set
        data_cid = input_df[input_df['c_id'] == cid]

        # Find mid points, equal to 
        v_mid_pt = pd.DataFrame(data_cid['voltage_min'] + (data_cid['voltage_max'] - data_cid['voltage_min']) * 0.5, index = data_cid.index, columns=['v_mid_pt'])
        data_cid = pd.concat([data_cid, v_mid_pt], axis = 1)

        # Calculate 10 minute averages
        v_mid_pt_averages = pd.DataFrame((data_cid['v_mid_pt'] + data_cid['v_mid_pt'].shift(1))/2, index = data_cid.index)
        v_mid_pt_averages = v_mid_pt_averages.rename(columns = {'v_mid_pt':'v_mid_pt_averages'})
        data_cid = pd.concat([data_cid, v_mid_pt_averages], axis = 1)

        # Add data_cid to end of new df
        data_output = data_output.append(data_cid)
        
    data_output = data_output.sort_index()
    return data_output

#------------------------ Gen dates in range ------------------------ 
def generate_dates_in_range(start_dt, end_dt, interval_minutes):
    """Return list of dates between start and end."""
    start_dt = start_dt.replace(second = 0, microsecond = 0)
    
    date_time_list = []
    current = start_dt
    
    while current < end_dt :
        date_time_list.append(current)
        current = current + datetime.timedelta(minutes = interval_minutes)

    return date_time_list    

#------------------------ Gen dates in range seconds ------------------------ 
def generate_dates_in_range_seconds(start_dt, end_dt, interval_seconds):
    """Return list of dates between start and end."""
    start_dt = start_dt.replace(microsecond = 0)
    
    date_time_list = []
    current = start_dt
    
    while current < end_dt :
        date_time_list.append(current)
        current = current + datetime.timedelta(seconds = interval_seconds)

    return date_time_list    



#------------------------ Filter data by DATE ------------------------ 
def get_data_by_time(input_df, start_mon, start_day, end_mon, end_day):
    
    output_df = input_df.loc[datetime.date(year = 2017, month = start_mon, day = start_day) : datetime.date(year = 2017, month = end_mon, day = end_day)]

    return output_df

#------------------------ Filter data by DATE AND TIME  -TODO DOES NOT WORK! (datetime.datetime apparently only accepts 3 args??) ------------------------ 
def get_data_by_date_and_time(input_df, start_mon, start_day, start_hour, start_minute, start_second, end_mon, end_day, end_hour, end_minute, end_second):
    
    output_df = input_df.loc[datetime.datetime(year = 2017, month = start_mon, day = start_day, hour = start_hour, minute = start_minute, second = start_second) : datetime.date(year = 2017, month = end_mon, day = end_day, hour = end_hour, minute = end_minute, second = end_second)]

    return output_df

#------------------------ calculate power from energy ------------------------ 
def calculate_power_from_energy(input_df, data_set_time_increment):
    """Takes a df containing 'energy' column, and a data set time increment (either '5_min', '30_sec' or '5_sec') and returns df with new col 'power_kW' NB the energy column contains Joules """
    if data_set_time_increment == '5_min':
        input_df['power_kW'] = input_df['energy'] * 0.012
    elif data_set_time_increment == '30_sec':
        input_df['power_kW'] = input_df['energy'] * 0.12 / 3600.0
    elif data_set_time_increment == '5_sec':
        input_df['power_kW'] = input_df['energy'] * 0.72 / 3600.0
    elif data_set_time_increment == '60_sec':
        input_df['power_kW'] = input_df['energy'] * 0.06 / 3600.0
    
    # Cases where time increments not a string
    elif data_set_time_increment == 30:
        input_df['power_kW'] = input_df['energy'] * 0.12 / 3600.0
    elif data_set_time_increment == 5:
        input_df['power_kW'] = input_df['energy'] * 0.72 / 3600.0
    elif data_set_time_increment == 60:
        input_df['power_kW'] = input_df['energy'] * 0.06 / 3600.0
    else:
        print('ERROR - did not specify which data set for energy --> power calc')
    
    return input_df

#------------------------ Calculate power drop and drop as percentage of max power ------------------------ 
def get_power_drop_and_percent_change(input_df) :
    """Pass a df for a single c_id (with 'power' col!!!) Returns the same df with two new cols: one for power change value, one for percentage of max power."""

    # POWER DROP FLAGS
    # New col - change in power between current interval (i) and next interval (i+1). Increases shown as positive, decreases shown as negative. i.e. P(t_i+1) - P(t_i)
    # Really slow when you use freq = '5min'. Removed: , freq = '5min'
    # For some reason, when using 'shift' function, cannot also rename the column when creating the df (just assigned nans)
    delta_power_kW = pd.DataFrame(input_df['power_kW'].shift(-1) - input_df['power_kW'], index = input_df.index)
    delta_power_kW = delta_power_kW.rename(columns = {'power_kW' : 'delta_power_kW'})
    input_df = pd.concat([input_df, delta_power_kW], axis = 1)

    max_power_kW = input_df['power_kW'].max()
    print(max_power_kW)

    input_df['power_drop_fraction_of_max_power'] = input_df['delta_power_kW'].apply(lambda x: x/float(max_power_kW))

    # New col - percentage change, removed: columns=['power_drop_fraction_of_max_power']
    # power_drop_fraction_of_max_power = pd.DataFrame(input_df['delta_power_kW'] / float(max_power_kW), index = input_df.index, columns=['power_drop_fraction_of_max_power'])
    # input_df = pd.concat([input_df, power_drop_fraction_of_max_power], axis = 1)

    return input_df


def get_power_drop_and_percent_change_wrt_init_condition(input_df) :

    # For some reason, when using 'shift' function, cannot also rename the column when creating the df (just assigned nans)
    delta_power_kW = pd.DataFrame(input_df['power_kW'].shift(-1) - input_df['power_kW'], index = input_df.index)
    delta_power_kW = delta_power_kW.rename(columns = {'power_kW' : 'delta_power_kW'})
    input_df = pd.concat([input_df, delta_power_kW], axis = 1)

    # Divide each power drop by initial value
    input_df['power_drop_fraction_of_init_condition'] = input_df['delta_power_kW'] /(input_df['power_kW'])

    return input_df



def flag_power_drop_to_zero(input_df):
    """Pass a df with a power_kW col for a single c_id. Returns the smae df with a new col which flags as 1 cases where power_kW(t) <> 0 and power_kW(t+1) = 0. All other cases are flagged as 0"""

    input_df['power_to_zero_flag'] = 0

    input_df.loc[(input_df['power_kW'] != 0) & (input_df['power_kW'].shift(-1) == 0), 'power_to_zero_flag'] = 1

    return input_df


def calculate_power_kW_first_and_second_derivative(input_df, power_lower_lim) :
    """Pass a df FOR A SINGLE C_ID (with 'power_kW' col!!!) Returns the same df with two new cols: power_kW_first_deriv and power_kW_second_deriv."""
    # NOTE - blanks are just non existent in the df, so it effectively skips them (i.e. compared the value before and after the blanks, which should be okay generally... may be some problem cases.)

    # First, adds zeroes in the place of very small values and multiply all power by 100 to avoid decimal issues
    # input_df['power_kW_processed'] = input_df['power_kW']*100
    input_df['power_kW_processed'] = input_df['power_kW']

    input_df.loc[input_df['power_kW_processed'] <= power_lower_lim, 'power_kW_processed'] = 0.0

    # Get power(t+1) - power(t) note that an increase is positive and a decrease is negative.
    power_kW_first_deriv = pd.DataFrame(input_df['power_kW_processed'].shift(-1) - input_df['power_kW_processed'], index = input_df.index)
    power_kW_first_deriv = power_kW_first_deriv.rename(columns = {'power_kW_processed' : 'power_kW_first_deriv'})
    input_df = pd.concat([input_df, power_kW_first_deriv], axis = 1)

    # Second derivative
    power_kW_second_deriv = pd.DataFrame(input_df['power_kW_first_deriv'].shift(-1) - input_df['power_kW_first_deriv'], index = input_df.index)
    power_kW_second_deriv = power_kW_second_deriv.rename(columns = {'power_kW_first_deriv' : 'power_kW_second_deriv'})
    input_df = pd.concat([input_df, power_kW_second_deriv], axis = 1)

    return input_df

def calculate_first_derivative_of_variable(input_df, col_name_string) :
    """Pass a df FOR A SINGLE C_ID (with 'power_kW' col!!!) Returns the same df with one new cols: power_kW_first_deriv."""
    # NOTE - blanks are just non existent in the df, so it effectively skips them (i.e. compared the value before and after the blanks, which should be okay generally... may be some problem cases.)
    new_col_name = col_name_string + '_first_deriv'

    input_df['temp'] = input_df[col_name_string]

    # Get power(t+1) - power(t) note that an increase is positive and a decrease is negative.
    power_kW_first_deriv = pd.DataFrame(input_df['temp'].shift(-1) - input_df['temp'], index = input_df.index)
    power_kW_first_deriv = power_kW_first_deriv.rename(columns = {'temp' : new_col_name})
    input_df = pd.concat([input_df, power_kW_first_deriv], axis = 1)







    # input_df['power_kW_processed'] = input_df['power_kW']

    # input_df.loc[input_df['power_kW_processed'] <= power_lower_lim, 'power_kW_processed'] = 0.0

    # # Get power(t+1) - power(t) note that an increase is positive and a decrease is negative.
    # power_kW_first_deriv = pd.DataFrame(input_df['power_kW_processed'].shift(-1) - input_df['power_kW_processed'], index = input_df.index)
    # power_kW_first_deriv = power_kW_first_deriv.rename(columns = {'power_kW_processed' : 'power_kW_first_deriv'})
    # input_df = pd.concat([input_df, power_kW_first_deriv], axis = 1)


    return input_df

def find_and_delete_duplicate_profiles(data):
    """WARNING - can remove ~15% of data!!! 
    Enter a df containing a timestamp index and 'c_id' and 'site_id' fields (site_id as well in case the c_id is just used twice by accident). Will create new column combining these two as string, then drop duplicate on first entry. Then deletes the combined string col and returns df."""

    data['comparison_string'] = data.index.map(str) + data['c_id'].map(str) + data['site_id'].map(str)

    data_output = data.drop_duplicates(subset='comparison_string')

# test1['comparison_string'] = test1.index.map(str) + test1['c_id'].map(str)

# test1_output = test1.drop_duplicates(subset = 'comparison_string')

    # Delete 'comparison_string'
    data_output = data_output.drop('comparison_string',1)


    return data_output



def get_gross_load_for_single_load_cid_sites(data, META_DATA_FILE_PATH, load_list, pv_list, data_date):
    """NOTE must now include data_date so that the function can handle 25 August 2018 data also!
    Filters input df ('data') for site_ids with no more than one c_id which records load. Then adds the PV back in for each site and returns a df containing a new con_type 'gross_load' with c_id = site_id *10 + 1"""
    
    # If date is 25 August then have to rename the columns
    if data_date == '25_august_2018':
        # Change column names for frequency and energy
        data = data.rename(columns = {'e':'energy', 'f':'frequency', 'p':'power', 'v':'vrms'})
        data.index.names = ['t_stamp']
        print(data.head())

    #------------------------ First, get a list of the requisite site_ids
    # Now a function below
    sites_with_single_load_cid_list = count_num_type_X_cids_meets_criteria_Y(META_DATA_FILE_PATH, data, load_list, 1)

    #------------------------ Calculate gross load (assume gross = sum of power across all loads)
    for site_id in sites_with_single_load_cid_list:
        # # test case
        # site_id = 27412

        # Filter for only time series data at this site
        data_site_id = data[data['site_id'] == site_id]

        # Create two separate dfs - one for load, one for pv, then merge on time and have a look at the outcome...
        # Need to check for multiple c_ids in pv data and then combine!!!
        data_site_id_pv = data_site_id[data_site_id['con_type'].isin(pv_list)]

        # Copy the index to a new column for use in groupby
        data_site_id_pv['t_stamp_copy'] = data_site_id_pv.index
        # Use groupby to calc total power/energy and average frequency/power
        data_site_id_pv_energy = pd.DataFrame({'energy' : data_site_id_pv.groupby('t_stamp_copy')['energy'].sum()}).reset_index()
        data_site_id_pv_power_kW = pd.DataFrame({'power_kW' : data_site_id_pv.groupby('t_stamp_copy')['power_kW'].sum()}).reset_index()
        data_site_id_pv_power = pd.DataFrame({'power' : data_site_id_pv.groupby('t_stamp_copy')['power'].sum()}).reset_index()
        data_site_id_pv_frequency = pd.DataFrame({'frequency' : data_site_id_pv.groupby('t_stamp_copy')['frequency'].mean()}).reset_index()
        data_site_id_pv_vrms = pd.DataFrame({'vrms' : data_site_id_pv.groupby('t_stamp_copy')['vrms'].mean()}).reset_index()

        # Merge energy and power_kW
        df_pv_merged = data_site_id_pv_energy.merge(data_site_id_pv_power_kW)
        # Merge output df with power (not kW!)
        df_pv_merged = df_pv_merged.merge(data_site_id_pv_power)
        # Merge output df with frequency
        df_pv_merged = df_pv_merged.merge(data_site_id_pv_frequency)
        # Merge output df with vrms
        df_pv_merged = df_pv_merged.merge(data_site_id_pv_vrms)
        # Sort index (just in case) and rename t_stamp_copy to t_stamp, then return it to the index
        df_pv_merged = df_pv_merged.sort_index()
        df_pv_merged = df_pv_merged.rename(index=str, columns = {'t_stamp_copy' : 't_stamp'})
        df_pv_merged = df_pv_merged.set_index('t_stamp')

        # Get load df
        data_site_id_load = data_site_id[data_site_id['con_type'].isin(load_list)]

        # Merge on index from both dfs
        df_merged = df_pv_merged.merge(data_site_id_load, left_index=True, right_index=True)
        df_merged = df_merged.sort_index()

        # Calc gross load as sum of loads, calc average vrms and frequency, change con_type to gross load
        df_merged['energy'] = df_merged['energy_x'] + df_merged['energy_y']
        df_merged['power_kW'] = df_merged['power_kW_x'] + df_merged['power_kW_y']
        df_merged['power'] = df_merged['power_x'] + df_merged['power_y']
        df_merged['frequency'] = df_merged[['frequency_x', 'frequency_y']].mean(axis=1)
        df_merged['vrms'] = df_merged[['vrms_x', 'vrms_y']].mean(axis=1)
        df_merged['con_type'] = 'gross_load'

        # Create a new c_id label for gross load, using the site_id * 10 + 1 (e.g. it should go from 1562 to 15621)
        gross_c_id = (site_id * 10) + 1
        df_merged['c_id'] = gross_c_id

        # Remove x and y columns (since these are repeated and were used to calc gross values)
        df_merged = df_merged.drop(['energy_x', 'energy_y','power_x', 'power_y', 'power_kW_x', 'power_kW_y', 'frequency_x', 'frequency_y', 'vrms_x', 'vrms_y'], axis = 1)

        # Concatenate back onto data
        data = pd.concat([data, df_merged])

    # Add flag to data which indicates sites with a single load c_id
    data['single_load_cid_flag'] = np.nan
    data.loc[data['site_id'].isin(sites_with_single_load_cid_list), 'single_load_cid_flag'] = 1

    # If data date is 25 August 2018 then change col names back again
    if data_date == '25_august_2018':
        # Change column names for frequency and energy
        data = data.rename(columns = {'energy':'e', 'frequency':'f', 'power':'p', 'vrms':'v'})
        data.index.names = ['ts']
        print(data.head())  

    print(data.head(10))
    # print(len_data_start)
    # print(len(data))

    return data


#------------------------ Get gross load characteristics ------------------------
def get_gross_load_characteristics(data, gross_list, t_0, FACTOR_KWH_TO_J):
    """Should take gross load for sites with multiple load c_ids as well... TBC"""

    # Import csv containing gross load and calculate:
    #       % change at the time of the event
    #       Peak load for each c_id and site_id
    #       Volume of load for each c_id and site_id

    # Get list of c_ids with gross load
    data_gross = data[data['con_type'].isin(gross_list)]
    list_cids_gross = data_gross['c_id'].drop_duplicates().tolist()

    # Make output df 
    output_df = pd.DataFrame(index = list_cids_gross)
    output_df.index.name = 'c_id'
    # Add columns
    output_df['t_0'] = np.nan
    # output_df['t_nadir'] = np.nan
    output_df['t_0_plus1'] = np.nan
    output_df['t_0_plus2'] = np.nan
    output_df['p_0'] = np.nan
    # output_df['p_nadir'] = np.nan
    output_df['p_0_plus1'] = np.nan
    output_df['p_0_plus2'] = np.nan

    # Peak and total gross load by c_id and site_id
    output_df['peak_c_id_gross_load_kW'] = np.nan 
    output_df['total_c_id_gross_load_kWh'] = np.nan 
    output_df['peak_site_id_gross_load_kW'] = np.nan 
    output_df['total_site_id_gross_load_kWh'] = np.nan 

    # Error codes
    # error_1: no data at t_0 (for p_0)
    output_df['error_1'] = np.nan
    # error_2: no data at t_0 or possibly t_0_plus1 (for p_0_plus1)
    output_df['error_2'] = np.nan
    # error_3: no data at t_0                or possibly t_0_plus2 (for p_0_plus2)
    output_df['error_3'] = np.nan
    # error_4: unable to calc peak load by c_id
    output_df['error_4'] = np.nan
    # error_5: unable to calc total load by c_id
    output_df['error_5'] = np.nan
    # error_6: unable to calc peak load by site_id
    output_df['error_6'] = np.nan
    # error_7: unable to calc total load by site_id
    output_df['error_7'] = np.nan

    # Calculated values
    output_df['p_diff_from_p0_to_p0_plus1'] = np.nan
    output_df['p_diff_from_p0_plus1_to_p0_plus2'] = np.nan
    output_df['percentage_drop_from_p0_to_p0_plus1'] = np.nan
    output_df['percentage_drop_from_p0_plus1_to_p0_plus2'] = np.nan

    #------------------------ First find percentage drop
    for c_id in list_cids_gross:
        # Filter data for each c_id
        c_id_data = data[data['c_id'] == c_id]

        # Add t_0 to output df
        output_df.loc[c_id, 't_0'] = t_0

        # Extract power at t_0, use exception to avoid cases with no t_0
        try:
            p_0 = c_id_data.loc[t_0,'power_kW'] # Print p_0 to output_df
            output_df.loc[c_id, 'p_0'] = p_0   
        except:
            print('no data at t_0')
            output_df.loc[c_id, 'error_1'] = 1.0 # Record error code

        # Get t_0_plus1 and power at this time, use exception to avoid cases with no t_0
        try:
            index_loc_for_t_0_plus1 = c_id_data.index.get_loc(t_0) + 1
            t_0_plus1 = c_id_data.index[index_loc_for_t_0_plus1]
            output_df.loc[c_id,'t_0_plus1'] = t_0_plus1 # Print to outputdf

            # Extract power at t_0_plus1 and print to output_df
            p_0_plus1 = c_id_data.loc[t_0_plus1,'power_kW']
            output_df.loc[c_id, 'p_0_plus1'] = p_0_plus1
        except:
            print('no data at t_0 or t_0_plus1')
            output_df.loc[c_id, 'error_2'] = 1.0 # Record error code

        # Get t_0_plus2 and power at this time, use exception to avoid cases with no t_0
        try:
            index_loc_for_t_0_plus2 = c_id_data.index.get_loc(t_0) + 2
            t_0_plus2 = c_id_data.index[index_loc_for_t_0_plus2]
            output_df.loc[c_id,'t_0_plus2'] = t_0_plus2 # Print to outputdf

            # Extract power at t_0_plus2 and print to output_df
            p_0_plus2 = c_id_data.loc[t_0_plus2,'power_kW']
            output_df.loc[c_id, 'p_0_plus2'] = p_0_plus2
        except:
            print('no data at t_0 or t_0_plus2')
            output_df.loc[c_id, 'error_3'] = 1.0 # Record error code

    #------------------------ Next find peak and total (daily if data for single day) load by c_id
        try:
            # Find peak load
            peak_c_id_gross_load = c_id_data.power_kW.abs().max()
            output_df.loc[c_id,'peak_c_id_gross_load_kW'] = peak_c_id_gross_load # Print to output_df
        except:
            print('error when finding peak load by c_id')
            output_df.loc[c_id, 'error_4'] = 1.0 # Record error code

        try:
            # Get total gross load in kWh. Multiply the total kW by the number of intervals for which there is data, and by a conversion factor from sec --> hours
            total_c_id_gross_load_kWh = c_id_data.energy.abs().sum() / FACTOR_KWH_TO_J
            output_df.loc[c_id,'total_c_id_gross_load_kWh'] = total_c_id_gross_load_kWh # Print to output_df
        except:
            print('error when finding total load by c_id')
            output_df.loc[c_id, 'error_5'] = 1.0 # Record error code

    #------------------------ Next find peak and total (daily if data for single day) load by site_id
    # NOTE this assumes that there is only one gross_load c_id per site. I.e. needs to be updated to account for multiple gross_loads per site! 
    # Get list of site_ids with gross load
    data_gross = data[data['con_type'] == 'gross_load']
    list_siteids_gross = data_gross['site_id'].drop_duplicates().tolist()

    for site_id in list_siteids_gross:
        # Filter for site_id - NOTE use gross data! 
        site_id_data = data_gross[data_gross['site_id'] == site_id]

        # Get list of c_ids in this smaller data set for use when printing results to output_df
        cid_list_for_this_siteid = site_id_data['c_id'].drop_duplicates().tolist()

        try:
            # Find peak load
            peak_site_id_gross_load = site_id_data.power_kW.abs().max()
            for site_c_id in cid_list_for_this_siteid:
                output_df.loc[site_c_id, 'peak_site_id_gross_load_kW'] = peak_site_id_gross_load # Print to output_df
        except:
            print('error when finding peak load by site_id')
            for site_c_id in cid_list_for_this_siteid:
                output_df.loc[site_c_id, 'error_6'] = 1.0 # Record error code

        try:
            # Get total gross load in kWh. Multiply the total kW by the number of intervals for which there is data, and by a conversion factor from sec --> hours
            total_site_id_gross_load_kWh = site_id_data.energy.abs().sum() / FACTOR_KWH_TO_J
            for site_c_id in cid_list_for_this_siteid:
                output_df.loc[site_c_id,'total_site_id_gross_load_kWh'] = total_site_id_gross_load_kWh # Print to output_df 
        except:
            print('error when finding total load by site_id')
            for site_c_id in cid_list_for_this_siteid:
                output_df.loc[site_c_id, 'error_7'] = 1.0 # Record error code

    # Calculate things
    output_df['p_diff_from_p0_to_p0_plus1'] = output_df['p_0_plus1'] - output_df['p_0']
    output_df['p_diff_from_p0_plus1_to_p0_plus2'] = output_df['p_0_plus2'] - output_df['p_0_plus1']
    output_df['percentage_drop_from_p0_to_p0_plus1'] = output_df['p_diff_from_p0_to_p0_plus1'] / output_df['p_0']
    output_df['percentage_drop_from_p0_plus1_to_p0_plus2'] = output_df['p_diff_from_p0_plus1_to_p0_plus2'] / output_df['p_0_plus1']

    # print(output_df)
    return output_df


def count_num_type_X_cids_meets_criteria_Y(META_DATA_FILE_PATH, data, X_list, Y_criteria):
    """Input various things to get out a list of sites where type X cids meets criteria Y. e.g. where PV cids count = 0, so, sites with only load c_ids. 
    NOTE need to input 'data' with which you're working in order to check for 30/5s sites since not all with be there!"""
    # First, get a list of the requisite site_ids
    site_data = pd.read_csv("/mnt/f/05_Solar_Analytics/" + META_DATA_FILE_PATH)
    # Get only c_ids present in data - some will not be here since 30/5sec split!!
    c_ids_data = data['c_id'].drop_duplicates().tolist()
    site_data = site_data[site_data['c_id'].isin(c_ids_data)]
    # Filter for X_list
    site_data = site_data[site_data['con_type'].isin(X_list)]
    # Then count the number of X_list c_ids per site
    sites_with_cid_count = pd.DataFrame({'cid_count' : site_data.groupby('site_id')['c_id'].count()}).reset_index()
    # Find cases where there is only a single/Y_criteria c_id for X_list
    sites_with_Y_count_of_X_type_cid_list = sites_with_cid_count[sites_with_cid_count['cid_count'] == Y_criteria]
    sites_with_Y_count_of_X_type_cid_list = sites_with_Y_count_of_X_type_cid_list['site_id'].tolist()

    return sites_with_Y_count_of_X_type_cid_list


# NOTE WHAT IS THE DIFFERENCE BETWEEN THIS FUNCTION AND THE NEXT ONE???
def get_gross_load_for_multiple_load_cid_sites(data_filtered_sites_list, data, VRMS_SUM_VARIATION_FOR_MATCH):
    """Finds the gross load for sites with multiple load type c_ids by matching c_ids with very similar voltage patterns. 
    NOTE - Assumes that these can be added!! (may not be true if two PV c_ds are on the same phase...)"""
    # For each site in site_list 
    # 1) Match load and pv c_ids using voltage 
    # 2) Sum based on matching load and pv profiles and assign a new c_id (use (site_id*10+i) where i increments with each match)
    for site in data_filtered_sites_list:
        # # Test case
        # site = 25478

        data_site = data[data['site_id'] == site]
        print(data_site.head())

        vrms_sum_df = pd.DataFrame({'vrms_sum' : data_site.groupby('c_id')['vrms'].sum()}).reset_index()
        print(vrms_sum_df)

        counter = 1
        vrms_sum_df['match'] = np.nan

        # For each row in the vrms_sum_df, check for a 'matching' vrms profile by comparing totals (sum)
        for row in vrms_sum_df.index:
            # Get sum in the current row
            current_sum = vrms_sum_df.loc[row,'vrms_sum']
            # Look in each row AFTER the current row 
            for sub_row in range(row+1, len(vrms_sum_df)):
                # Get the sum in this 'subrow'
                next_sum = vrms_sum_df.loc[sub_row,'vrms_sum']
                # Check whether the sum in this 'subrow' is within 10% of the current row
                if next_sum >= current_sum*(1-VRMS_SUM_VARIATION_FOR_MATCH) and next_sum <= current_sum*(1+VRMS_SUM_VARIATION_FOR_MATCH):
                    # If there is a match, record the counter value to both the 'current row' and 'current subrow'
                    vrms_sum_df.loc[sub_row,'match'] = counter
                    vrms_sum_df.loc[row,'match'] = counter

            counter += 1 # Increment counter before going to the next row (c_id)

        print(vrms_sum_df)

        # Now that we've got the matches, create df_gross and concatenate onto data
        # Get list of counters
        match_counter_list = vrms_sum_df['match'].drop_duplicates().tolist()
        for counter in match_counter_list:

            # counter = 1 

            # Filter data_site for match where counter = x
            match_cids = vrms_sum_df[vrms_sum_df['match'] == counter]
            match_cids = match_cids.c_id.tolist()
            # print(match_cids)
            data_site_match = data_site[data_site['c_id'].isin(match_cids)]
            # print(data_site_match.head())

            # Copy the index to a new column for use in groupby
            data_site_match['t_stamp_copy'] = data_site_match.index
            # Use groupby to calc total power/energy and average frequency/power
            data_site_match_energy = pd.DataFrame({'energy' : data_site_match.groupby('t_stamp_copy')['energy'].sum()}).reset_index()
            data_site_match_power_kW = pd.DataFrame({'power_kW' : data_site_match.groupby('t_stamp_copy')['power_kW'].sum()}).reset_index()
            data_site_match_power = pd.DataFrame({'power' : data_site_match.groupby('t_stamp_copy')['power'].sum()}).reset_index()
            data_site_match_frequency = pd.DataFrame({'frequency' : data_site_match.groupby('t_stamp_copy')['frequency'].mean()}).reset_index()
            data_site_match_vrms = pd.DataFrame({'vrms' : data_site_match.groupby('t_stamp_copy')['vrms'].mean()}).reset_index()

            # Merge energy and power_kW
            c_id_gross_load_df = data_site_match_energy.merge(data_site_match_power_kW)
            # Merge output df with power (not kW!)
            c_id_gross_load_df = c_id_gross_load_df.merge(data_site_match_power)
            # Merge output df with frequency
            c_id_gross_load_df = c_id_gross_load_df.merge(data_site_match_frequency)
            # Merge output df with vrms
            c_id_gross_load_df = c_id_gross_load_df.merge(data_site_match_vrms)
            # Sort index (just in case) and rename t_stamp_copy to t_stamp, then return it to the index
            c_id_gross_load_df = c_id_gross_load_df.sort_index()
            c_id_gross_load_df = c_id_gross_load_df.rename(index=str, columns = {'t_stamp_copy' : 't_stamp'})
            c_id_gross_load_df = c_id_gross_load_df.set_index('t_stamp')

            # Update c_id name
            c_id_gross_load_df['con_type'] = 'gross_load'

            # Create a new c_id label for gross load, using the site_id * 10 + 1 (e.g. it should go from 1562 to 15621)
            gross_c_id = (site * 10) + counter
            c_id_gross_load_df['c_id'] = gross_c_id

            # Get the site_data without energy, power, power_kW, frequency or vrms. Merge with c_id_gross_load_df, KEEPING ONLY THE INDEX FROM c_id_gross_load_df
            data_site_meta = data_site.drop(['energy', 'power_kW', 'power', 'frequency', 'vrms', 'con_type', 'c_id'], axis = 1)

            # add index as col then drop dups
            data_site_meta['t_stamp_copy'] = data_site_meta.index
            data_site_meta = data_site_meta.drop_duplicates(subset=['t_stamp_copy'])

            # Merge using only the index from c_id_gross_load_df
            c_id_gross_load_meta_df = c_id_gross_load_df.merge(data_site_meta, how='left', left_index=True, right_index=True)

            # Remove t_stamp_copy
            c_id_gross_load_meta_df = c_id_gross_load_meta_df.drop(['t_stamp_copy'], axis = 1)
            print(c_id_gross_load_meta_df.head())

            # Concatenate back onto data
            data = pd.concat([data, c_id_gross_load_meta_df])
            # print(data.tail())

        # print(data.tail(20))

    return data

def get_gross_load_using_match_on_vrms(data_filtered_sites_list, data_without_gross_loads, ALLOWABLE_VRMS_DIFF, data):
    """"""
    # 1) Match load and pv c_ids using voltage 
    # 2) Sum based on matching load and pv profiles and assign a new c_id (use (site_id*10+i) where i increments with each match)
    for site in data_filtered_sites_list:
        # Test case
        # site = 25478
        # site = 26314

        data_site = data_without_gross_loads[data_without_gross_loads['site_id'] == site]
        print(data_site.head())

        # Get df for storing results
        vrms_compare_df = pd.DataFrame({'vrms_sum' : data_site.groupby('c_id')['vrms'].sum()}).reset_index()
        print(vrms_compare_df)

        counter = 1
        vrms_compare_df['match'] = np.nan

        # Loop through the rows to check whether the voltage difference is within an allowable range - if so the it's a 'match'
        for current_row in range(0,len(vrms_compare_df)):
            current_c_id = vrms_compare_df.loc[current_row,'c_id']
            # Get data for this current_cid (for comparison below)
            data_current_cid = data_site[data_site['c_id'] == current_c_id]

            for row in range(current_row+1, len(vrms_compare_df)):
                row_c_id = vrms_compare_df.loc[row, 'c_id']
                # Filter data for this row's cid
                data_row_cid = data_site[data_site['c_id'] == row_c_id]
                # Merge the 'current_cid' and 'row_cid' dfs
                combined_df = data_current_cid.merge(data_row_cid, left_index=True, right_index=True)
                # Calc the absolute difference in each time interval NOTE this calc has been tested and should ignore times where there is nan
                combined_df['diff_vrms'] = abs(combined_df['vrms_x'] - combined_df['vrms_y']) 
                total_diffs = combined_df['diff_vrms'].sum() # Find the sum of these differences
                print(total_diffs)
                print(ALLOWABLE_VRMS_DIFF * len(combined_df))

                if total_diffs <= (ALLOWABLE_VRMS_DIFF * len(combined_df)) :
                    # If there is a match, record the counter value to both the 'current row' and 'current subrow'
                    vrms_compare_df.loc[current_row,'match'] = counter
                    vrms_compare_df.loc[row,'match'] = counter
                    # Increment counter before going to the next row (c_id)
                    counter += 1 

            print(vrms_compare_df)


        # Now that we've got the matches, create df_gross and concatenate onto data
        # Get list of counters
        match_counter_list = vrms_compare_df['match'].drop_duplicates().tolist()
        for counter in match_counter_list:

            # counter = 1 

            # Filter data_site for match where counter = x
            match_cids = vrms_compare_df[vrms_compare_df['match'] == counter]
            match_cids = match_cids.c_id.tolist()
            # print(match_cids)
            data_site_match = data_site[data_site['c_id'].isin(match_cids)]
            # print(data_site_match.head())

            # Copy the index to a new column for use in groupby
            data_site_match['t_stamp_copy'] = data_site_match.index
            # Use groupby to calc total power/energy and average frequency/power
            data_site_match_energy = pd.DataFrame({'energy' : data_site_match.groupby('t_stamp_copy')['energy'].sum()}).reset_index()
            data_site_match_power_kW = pd.DataFrame({'power_kW' : data_site_match.groupby('t_stamp_copy')['power_kW'].sum()}).reset_index()
            data_site_match_power = pd.DataFrame({'power' : data_site_match.groupby('t_stamp_copy')['power'].sum()}).reset_index()
            data_site_match_frequency = pd.DataFrame({'frequency' : data_site_match.groupby('t_stamp_copy')['frequency'].mean()}).reset_index()
            data_site_match_vrms = pd.DataFrame({'vrms' : data_site_match.groupby('t_stamp_copy')['vrms'].mean()}).reset_index()

            # Merge energy and power_kW
            c_id_gross_load_df = data_site_match_energy.merge(data_site_match_power_kW)
            # Merge output df with power (not kW!)
            c_id_gross_load_df = c_id_gross_load_df.merge(data_site_match_power)
            # Merge output df with frequency
            c_id_gross_load_df = c_id_gross_load_df.merge(data_site_match_frequency)
            # Merge output df with vrms
            c_id_gross_load_df = c_id_gross_load_df.merge(data_site_match_vrms)
            # Sort index (just in case) and rename t_stamp_copy to t_stamp, then return it to the index
            c_id_gross_load_df = c_id_gross_load_df.sort_index()
            c_id_gross_load_df = c_id_gross_load_df.rename(index=str, columns = {'t_stamp_copy' : 't_stamp'})
            c_id_gross_load_df = c_id_gross_load_df.set_index('t_stamp')

            # Update c_id name
            c_id_gross_load_df['con_type'] = 'gross_load'

            # Create a new c_id label for gross load, using the site_id * 10 + 1 (e.g. it should go from 1562 to 15621)
            gross_c_id = (site * 10) + counter
            c_id_gross_load_df['c_id'] = gross_c_id

            # Get the site_data without energy, power, power_kW, frequency or vrms. Merge with c_id_gross_load_df, KEEPING ONLY THE INDEX FROM c_id_gross_load_df
            data_site_meta = data_site.drop(['energy', 'power_kW', 'power', 'frequency', 'vrms', 'con_type', 'c_id'], axis = 1)

            # add index as col then drop dups
            data_site_meta['t_stamp_copy'] = data_site_meta.index
            data_site_meta = data_site_meta.drop_duplicates(subset=['t_stamp_copy'])

            # Merge using only the index from c_id_gross_load_df
            c_id_gross_load_meta_df = c_id_gross_load_df.merge(data_site_meta, how='left', left_index=True, right_index=True)

            # Remove t_stamp_copy
            c_id_gross_load_meta_df = c_id_gross_load_meta_df.drop(['t_stamp_copy'], axis = 1)
            print(c_id_gross_load_meta_df.head())

            # Concatenate back onto data
            data = pd.concat([data, c_id_gross_load_meta_df])
            # print(data.tail())

        # print(data.tail(20))

    return data




def ffil_on_cids(data):
    """Be very careful, only seems to work with Vic. Copied from get_data_utc_corrected_missing_data_fix.py"""

    # Add new column for counting empty rows
    data['missing_val_flag'] = np.nan


    # Get list of unique time stamps from df (assuming that every point has some data???!!!)
    index_time_stamps = data.index.unique()
    index_df = pd.DataFrame(index = index_time_stamps)
    # Also keep list for looping:
    index_time_stamps_list = index_time_stamps.tolist()


    # Get list of unique c_ids
    list_unique_cids = data['c_id'].drop_duplicates().tolist()

    # Set up outputdf
    data_output = pd.DataFrame(columns = data.columns.values.tolist())
    data_output.index.name = 't_stamp'

    for c_id in list_unique_cids:
        # # Begin loop - else test with 32711
        # c_id = 32711
        print(c_id)

        # Filter for cid only
        c_id_data = data[data['c_id'] == c_id]

        # Merge this df onto the df with index containing all time stamps 
        c_id_data_nans = index_df.merge(c_id_data, left_index=True, right_index=True, how = 'left')

        # Alt method: 
        c_id_data_nans = c_id_data_nans.fillna(method='ffill')


        # # Initial energy value for loop, will get the next one each time stamp.
        # init_energy_val = 0.0
        # init_con_type_val = 'dummy_init_val'
        # init_c_id_val = c_id
        # init_site_id_val = 0000
        # init_s_postcode_val = 0000

        # for time_stamp in index_time_stamps_list:
        #     if pd.isnull(c_id_data_nans.loc[time_stamp,'energy']):
        #         # Fill the energy, con_type, c_id, site_id  and postcode with data
        #         c_id_data_nans.loc[time_stamp, 'energy'] = init_energy_val
        #         c_id_data_nans.loc[time_stamp, 'con_type'] = init_con_type_val
        #         c_id_data_nans.loc[time_stamp, 'c_id'] = init_c_id_val
        #         c_id_data_nans.loc[time_stamp, 'site_id'] = init_site_id_val
        #         c_id_data_nans.loc[time_stamp, 's_postcode'] = init_s_postcode_val

        #         c_id_data_nans.loc[time_stamp, 'missing_val_flag'] = 1.0

        #     # Get data from current row for using if next row is blank
        #     init_energy_val = c_id_data_nans.loc[time_stamp, 'energy']
        #     init_con_type_val = c_id_data_nans.loc[time_stamp, 'con_type']
        #     init_c_id_val = c_id_data_nans.loc[time_stamp, 'c_id']
        #     init_site_id_val = c_id_data_nans.loc[time_stamp, 'site_id']
        #     init_s_postcode_val = c_id_data_nans.loc[time_stamp, 's_postcode']


        data_output = pd.concat([data_output, c_id_data_nans])

    return data_output
    # # save to csv
    # c_id_data_nans.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_UTC_corrected_' +str(TIME_INTERVALS)+'_sec_v2_single_cid_32711_test_nans_fix2.csv')

    # save to csv
    # data_output.to_csv('output_csv_files/' + REGION + '_' + DATA_DATE + '_UTC_corrected_' +str(TIME_INTERVALS)+'_sec_v2.csv')


# def ffil_data_by_cids(data):
#     """BE REALLY CAREFUL!!! NEED TO HAVE T_S FOR NEW DATA SET. Use this for missing data issues"""

#     # # Add new column for counting empty rows
#     # data['missing_val_flag'] = np.nan


#     # Get list of unique time stamps from df (assuming that every point has some data???!!!)
#     index_time_stamps = data.index.unique()
#     index_df = pd.DataFrame(index = index_time_stamps)
#     # # Also keep list for looping:
#     # index_time_stamps_list = index_time_stamps.tolist()


#     # Get list of unique c_ids
#     list_unique_cids = data['c_id'].drop_duplicates().tolist()

#     # Set up outputdf
#     data_output = pd.DataFrame(columns = data.columns.values.tolist())
#     data_output.index.name = 'ts'

#     for c_id in list_unique_cids:

#         # Filter for cid only
#         c_id_data = data[data['c_id'] == c_id]

#         # Merge this df onto the df with index containing all time stamps 
#         c_id_data_nans = index_df.merge(c_id_data, left_index=True, right_index=True, how = 'left')

#         # Forward fill data: 
#         c_id_data_nans = c_id_data_nans.fillna(method='ffill')

#         # Concatenate onto output
#         data_output = pd.concat([data_output, c_id_data_nans])
    
#     return data_output


def ffil_data_by_cids(data):
    """BE REALLY CAREFUL WITH INDEX NAME!!! (NEED TO BE CALLED TS FOR 25 August DATA SET). Use this for missing data issues"""

    # # Add new column for counting empty rows
    # data['missing_val_flag'] = np.nan


    # Get list of unique time stamps from df (assuming that every point has some data???!!!)
    index_time_stamps = data.index.unique()
    # print(index_time_stamps)
    index_df = pd.DataFrame(index = index_time_stamps)
    # print(index_df)

    # # Also keep list for looping:
    # index_time_stamps_list = index_time_stamps.tolist()


    # Get list of unique c_ids
    list_unique_cids = data['c_id'].drop_duplicates().tolist()
    print(list_unique_cids)
    print(len(list_unique_cids))

    # Set up outputdf
    data_output = pd.DataFrame(columns = data.columns.values.tolist())
    data_output.index.name = 'ts'
    print(data_output.head())

    counter = 1
    # list_unique_cids = [41363,35173]
    for c_id in list_unique_cids:
        # c_id = 41363
        print(counter)

        # Filter for cid only
        c_id_data = data[data['c_id'] == c_id]
        # print(c_id_data.head())

        # Merge this df onto the df with index containing all time stamps 
        c_id_data_nans = index_df.merge(c_id_data, left_index=True, right_index=True, how = 'left')
        # print(c_id_data_nans.head())

        # Flag nans
        # First, get list of columns for ffill below, NOTE this must be got before adding the nan_flag col, else the nan_flags will also be ffilled
        col_names = c_id_data_nans.columns.values.tolist()
        # Creat nan_flag col. Then flag where 'c_id' is nan.
        c_id_data_nans['nan_flag'] = np.nan
        c_id_data_nans.loc[c_id_data_nans['c_id'].isnull() , 'nan_flag'] = 1

        # Sort index so ffill-ing makes sense 
        c_id_data_nans = c_id_data_nans.sort_index()
        # ffill on each col
        for col in col_names:
            c_id_data_nans[col] = c_id_data_nans[col].fillna(method='ffill')

        # c_id_data_nans = c_id_data_nans.fillna(method='ffill')
        # print(c_id_data_nans.head())

        # Concatenate onto output
        data_output = pd.concat([data_output, c_id_data_nans])
        # print(data_output.head())

        counter +=1

    return data_output













































# #------------------------ Step 0: Import required packages ------------------------
# # Import packages required for program
# import numpy as np
# import pandas as pd
# pd.set_option('display.max_columns', 500)
# # pd.set_option('display.max_rows', 500)
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import calendar
# import seaborn as sns
# import itertools
# import datetime
# from time import gmtime, strftime

# import solar_analytics
# import requested_regions
# import util
# import util_plotting

# # NOTE new function file!
# import get_error_flags


# # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# # Inputs
# # REGION = 'south_australia'
# # TIME_INTERVALS = 30
# # DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_2017_03_03_v2.csv'
# # META_DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_c_id_info_v2_NS.csv'
# # INVERTER_DATA_PATH = '2018-04-05_solar_analytics_data_transfer/south_australia_site_info_v2_NS.csv'
# # DATA_DATE = '2017_03_03'
# # # NOTE don't forget the date!^

# REGION = 'victoria'
# TIME_INTERVALS = 30
# DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_2018_01_18_v2.csv'
# META_DATA_FILE_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_c_id_info_v2_NS.csv'
# INVERTER_DATA_PATH = '2018-04-05_solar_analytics_data_transfer/victoria_site_info_v2_NS.csv'
# DATA_DATE = '2018_01_18'
# # NOTE don't forget the date!^

# # Fraction of data allowed in 'other' polarity before being flagged as mixed polarity (note 0.01 = 1%)
# FRACTION_FOR_MIXED_POLARITY = 0.01
# LOAD_FRACTION_FOR_MIXED_POLARITY = 0.01
# PV_GEN_START_HR = '05:00'
# PV_GEN_END_HR = '20:00'

# load_list = ['ac_load_net', 'ac_load']
# pv_list = ['pv_site_net', 'pv_site']

# # Time at which event occurs (t_0)
# # # SA 30 sec
# # t_0 = datetime.datetime(year= 2017, month= 3, day= 3, hour= 15, minute= 3, second= 25)
# # SA 5 sec - TODO
# # # Vic 5 sec
# # t_0 = datetime.datetime(year= 2018, month= 1, day= 18, hour= 15, minute= 18, second= 50)
# # Vic 30 sec
# t_0 = datetime.datetime(year= 2018, month= 1, day= 18, hour= 15, minute= 18, second= 55)

# # Estimate of when all PV systems are back on line (from visualisation)
# # # SA 30 sec
# # T_START_T_0 = '15:03:25'
# # T_END_ESTIMATE = '15:15'
# # T_END_ESTIMATE_NADIR = '15:06'
# # # NOTE ^ the T_END_ESTIMATE_NADIR must be at least 2 time increments after T_0 (+1 and +2)
# # # SA 5 sec - TODO
# #  ...
# # Vic 30 sec
# T_START_T_0 = '15:18:55'
# T_END_ESTIMATE = '15:30:25'
# T_END_ESTIMATE_NADIR = '15:25'
# # # Vic 5 sec
# # T_START_T_0 = '15:18:50'
# # T_END_ESTIMATE = '15:30'
# # Check the below!!!
# # T_END_ESTIMATE_NADIR = '15:25'

# # Enter a value (in kW) below which will be counted as 'zero' when finding first and second order derivatives of power_kW
# POWER_KW_EFFECTIVE_ZERO_FOR_DERIVS = 0.1

# # Values to be considered zero when finding 'minimum' value for p_nadir. Need this because sometimes a slightly negative value is recorded part way through nadir and this is returned as the nadir.
# POWER_ROUND_TO_ZERO_VAL_KW = 0.1

# # 30% fairly arbritary. Help to try and capture 'soft' turning points for ramp up.
# ACCELERATION_FRACTION_CONSIDERED_SUFFICIENT_FOR_RAMP_START_OR_END = 0.1

# # For categories analysis
# RIDE_THROUGH_PERCENTAGE_DROP_MAX = 0.04
# DIP_PERCENTAGE_DROP_MAX = 0.10
# CAT_3_NADIR_DROP_MAX = 0.25
# CAT_4_NADIR_DROP_MAX = 0.50
# CAT_5_NADIR_DROP_MAX = 0.75
# # Values to be considered zero when finding 'disconnect' category.
# DISCONNECT_CAT_APPROX_ZERO_KW = 0.1

# # Percentage return val - this will be used to assess total response time, i.e. 't_to_return_within_10_percent' - default is 0.1 (i.e. 10%)
# PERCENTAGE_RETURN_MINIMUM = 0.1

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

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


    # # Calculate power NOTE - commenting out since the polarity is corrected and power_kW calculated when the data is first got by solar_analytics.py
    # data = calculate_power_from_energy(data, str(TIME_INTERVALS) + '_sec')


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
            # Sort index!
            c_id_data = c_id_data.sort_index()
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

        # Ride through if the max percentage drop between t_0 and both 1 and 2 periods later is less than the set val (~1%) NOTE changing from abs because sometimes the PV systems actually increase from event time.
        elif min(output_df.loc[c_id,'percentage_drop_to_p_0_plus1'], output_df.loc[c_id,'percentage_drop_to_p_0_plus2']) > RIDE_THROUGH_PERCENTAGE_DROP_MAX:
            output_df.loc[c_id,'cat_1_ride_through'] = 1

        # Slight dip if power two periods after t_0 has bounced back up, and the drop to that first period after t_0 is less than the set val (~5%) and cat 1 is not true
        elif (abs(output_df.loc[c_id,'p_0_plus1']) < abs(output_df.loc[c_id,'p_0_plus2'])) and abs(output_df.loc[c_id, 'percentage_drop_to_p_0_plus1']) <= DIP_PERCENTAGE_DROP_MAX and output_df.loc[c_id, 'cat_1_ride_through'] != 1:
            output_df.loc[c_id, 'cat_2_dip'] = 1

        # Curtail mild (cat 3) if percentage drop to nadir is less than set val (25%) and 'slight dip' (cat 2) is false and ride through (cat 1) is false
        elif abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) <= CAT_3_NADIR_DROP_MAX and output_df.loc[c_id, 'cat_2_dip'] != 1 and output_df.loc[c_id, 'cat_1_ride_through'] != 1:
            output_df.loc[c_id, 'cat_3_mild_curtail'] = 1

        # Curtail medium (cat 4) if percentage drop to nadir is less than set val (50%) and greater than cat 3 set val (25%)
        elif abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) <= CAT_4_NADIR_DROP_MAX and abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) > CAT_3_NADIR_DROP_MAX:
            output_df.loc[c_id, 'cat_4_medium_curtail'] = 1

        # Curtail medium (cat 5) if percentage drop to nadir is less than set val (75%) and greater than cat 3 set val (50%)
        elif abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) <= CAT_5_NADIR_DROP_MAX and abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) > CAT_4_NADIR_DROP_MAX:
            output_df.loc[c_id, 'cat_5_signiifcant_curtail'] = 1

        # Extreme curtail (cat 6) if percentage drop to nadir is greater than set val (75%) and disconnect (cat 7) is false
        elif abs(output_df.loc[c_id, 'percentage_drop_to_nadir']) > CAT_5_NADIR_DROP_MAX and output_df.loc[c_id, 'cat_7_disconnect'] != 1:
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


def get_pv_CF_by_site(output_df, pv_list, minute_now_start):
    """BE CAREFUL - the time from which CF is calculated is specifically for 25 August 2018 event using 60s data"""
    # Get PV data
    output_df = output_df[output_df['con_type'].isin(pv_list)]

    try:
        # Remove sites that have been flagged to contain issues.
        output_df = output_df[output_df['manual_check_required'] != 1]
    except:
        print("Note - no manual check required column")
        
    # Create a new df which contains site behaviour
    # Drop duplicates on site_id, but keep all other columns by using 'subset'
    site_df = output_df.drop_duplicates(subset='site_id')

    # Get sum of power for each site_id for each time stamp, this is in order to avoid missing stuff because of multiple c_ids
    # Note, it is easier to do this than to just get max etc. by c_id because the system capacity is on a site basis, so getting capacity factor has to be done on a site basis
    power_sum_df = pd.DataFrame({'site_power_kW': output_df.groupby(['ts','site_id'])['power_kW'].sum()}).reset_index('site_id') #No idea why resetting index on 'site_id' means that the index is reset to ts. It just works.
    print(power_sum_df.head())

    # Get max power_kW for each site_id over the day from power_sum_df
    max_df = pd.DataFrame({'max_power_kW': power_sum_df.groupby('site_id')['site_power_kW'].max()}).reset_index()

    # Merge these max values onto the site_df
    site_df = site_df.merge(max_df, how='left', on='site_id')

    # Initialise the first minute in which to get power
    minute_now = minute_now_start

    for counter in range(0,12):
        # Get date_time for now
        t_now = datetime.datetime(year= 2018, month= 8, day= 25, hour= 13, minute= minute_now, second= 55)

        # Filter for t_now
        filtered_df = power_sum_df.loc[t_now]
        # filtered_df = filtered_df[['power_kW', 'site_id']] #no longer required since only two columns when the groupby for site_power_kW happens above.
        column_label = 'site_power_kW_13'+ (str(0) if minute_now <10 else '') +str(minute_now)+'55'
        filtered_df = filtered_df.rename(columns = {'site_power_kW': column_label})
        print(filtered_df.head())

        # Merge these max values onto the site_df
        site_df = site_df.merge(filtered_df, how='left', on='site_id')
        print(site_df.head())

        # Go to next minute
        minute_now += 1

    # Clean out columns which we don't need / don't make sense to keep
    site_df = site_df.drop(['c_id','v','p','e','f','d', 'polarity', 'sa_ww_id', 'p_polarity','e_polarity','power_kW'], axis=1)

    return site_df


def get_power_kW_normalised_to_p0(output_df, pv_list, t_0, POWER_ASSUME_ZERO_KW_VAL):
    """Takes df containing power_kW. Finds p_0 for each c_id (MUST CONTAIN C_ID LABELS!) and then adds a new columns called power_kW_p0 which is power_kW normalised to p_0"""
    # Get PV data
    power_at_t0_df = output_df[output_df['con_type'].isin(pv_list)]
    # Filter for t_0
    power_at_t0_df = power_at_t0_df.loc[t_0]

    # Drop everything except for the power_kW and c_id
    power_at_t0_df = power_at_t0_df[['c_id', 'power_kW']]
    # Remove values close to zero
    power_at_t0_df.loc[power_at_t0_df['power_kW'] <= POWER_ASSUME_ZERO_KW_VAL,'power_kW'] = np.nan

    # Rename power_kW to power_kW_p0
    power_at_t0_df = power_at_t0_df.rename(columns = {'power_kW':'power_kW_p0'})

    # Merge onto the original df on c_id
    output_df = output_df.reset_index().merge(power_at_t0_df, how='left', on='c_id').set_index('ts')

    # Calc normalised power
    output_df['power_kW_normed_to_p0'] = output_df['power_kW'] / output_df['power_kW_p0']

    return output_df