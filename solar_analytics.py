# Solar analytics factory module
# Throws out solar analytics data as requested.


import numpy as np
import pandas as pd
import calendar
import datetime as dt

import util

# Import CSV and store as pandas Data Frame
#-----------------------------------------------------------------------------------------------

def get_monthly_data(month_number) : 
    """Input the month number between 1 and 6. Output a tuple with two variables: a df containing the data from that CSV file and the month name as a string"""


    # Import data to pandas data frame
    month_number = int(month_number)
    
    if month_number >=1 and month_number <= 6 :
        csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/2017-07-20_Solar_Analytics_Data_Transfer/2017_0"+str(month_number)+"_naomi.csv",index_col = 't_stamp', parse_dates=True)
    else : 
        raise ValueError("Invalid month selected. Please enter a value between 1 and 6")


    # Extract the month being examined
    start_date = csv_data.index[0]
    month_name = calendar.month_name[start_date.month]
    csv_data = csv_data.sort_index()
    # Store both output in a tuple so they can be 'unpacked' by the function call
    fnct_outputs = (csv_data, month_name)

    # Return the tuple    
    return fnct_outputs



#  Test
# data, data_month = open_csv(1)

# print(data.head())

# print(data.tail())

# print(data_month)





# Import data from each csv and combine into a single df
#-----------------------------------------------------------------------------------------------

def get_all_data() : 
    """Opens all six csv files and combines in a single data frame. Deletes unamed columns."""


    # Import January
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/2017-07-20_Solar_Analytics_Data_Transfer/2017_01_naomi.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0', 'Unnamed: 0.1'], axis = 1)
    # Store in general df
    data = csv_data


    # Import February
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/2017-07-20_Solar_Analytics_Data_Transfer/2017_02_naomi.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0', 'Unnamed: 0.1'], axis = 1)
    # Concatenate with existing df in general df
    data = pd.concat([data, csv_data])


    # Import March
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/2017-07-20_Solar_Analytics_Data_Transfer/2017_03_naomi.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0'], axis = 1)
    # Concatenate with existing df in general df
    data = pd.concat([data, csv_data])


    # Import April
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/2017-07-20_Solar_Analytics_Data_Transfer/2017_04_naomi.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0'], axis = 1)
    # Concatenate with existing df in general df
    data = pd.concat([data, csv_data])


    # Import May
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/2017-07-20_Solar_Analytics_Data_Transfer/2017_05_naomi.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0'], axis = 1)
    # Concatenate with existing df in general df
    data = pd.concat([data, csv_data])


    # Import June
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/2017-07-20_Solar_Analytics_Data_Transfer/2017_06_naomi.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0'], axis = 1)
    # Concatenate with existing df in general df
    data = pd.concat([data, csv_data])

    # Too slow!! do this after filtering or before graphing only
    # Sort ascending
    data = data.sort_index()

    return data

# def get_all_data_sorted():
#     return get_all_data().sorted()

# # Test
# data_test_for_rows = get_all_data()
# print(len(data_test_for_rows))


def get_region_data(region_name_string, month_integer, time_interval):
    """ Imports 30 second data for region in particular month (i.e. Adelaide region for January) including meta data and converts time zone to NEM time (Brisbane). 
    MUST ENTER EITHER 'adelaide', 'sydney' or 'rural_qld' for region string."""

    if month_integer >=1 and month_integer <= 6 :
        # Get time series data
        time_series_data = pd.read_csv("/mnt/f/05_Solar_Analytics/Solar_Analytics_data_transfer_" + region_name_string + "_region/" + region_name_string + "_20170" + str(month_integer) + ".csv",index_col = 't_stamp', parse_dates=True)
        # Get meta data
        site_data = pd.read_csv("/mnt/f/05_Solar_Analytics/Solar_Analytics_data_transfer_" + region_name_string + "_region/" + region_name_string + "_site_data.csv")
        # Combine time series and meta data
        time_series_data = time_series_data.reset_index().merge(site_data, how = 'left', on='c_id').set_index('t_stamp')

        # Convert to NEM time (Brisbane time, i.e. no daylight savings). First make aware, then conver time zones, then convert back to niave.
        time_series_data.index = time_series_data.index.tz_localize('UTC')
        time_series_data.index = time_series_data.index.tz_convert('Australia/Brisbane').tz_localize(None)
        # See list of time zones: https://stackoverflow.com/questions/13866926/python-pytz-list-of-timezones

        # Sort index to enable slicing
        time_series_data = time_series_data.sort_index()

        # Extract data for 30sec or 5 sec sites only

    else : 
        raise ValueError("Invalid month selected. Please enter a value between 1 and 6")    

    # Extract data for time_interval specified
    # Find intervals for which 30 sec data exists (assumes all 30 sec data is on 25 and 55 intervals - may be wrong!!!)
    time_series_data['time_period_30s_flag'] = 0
    time_series_data.loc[time_series_data.index.second == 25, 'time_period_30s_flag'] = 1
    time_series_data.loc[time_series_data.index.second == 55, 'time_period_30s_flag'] = 1
    
    # Get list of cids for which there is definitely 5 sec data
    dummy_df = time_series_data[time_series_data['time_period_30s_flag'] == 0]
    list_5_sec_sites = dummy_df['c_id'].drop_duplicates()
    list_5_sec_sites = list_5_sec_sites.tolist()

    # Remove 30 sec flag col
    time_series_data = time_series_data.drop(['time_period_30s_flag'], axis = 1)

    # Slice df using list of 5 second cids
    if time_interval == 5:
        time_series_data = time_series_data[time_series_data.c_id.isin(list_5_sec_sites)]
    elif time_interval == 30:
        time_series_data = time_series_data[np.logical_not(time_series_data.c_id.isin(list_5_sec_sites))]
    else : 
        raise ValueError("Invalid time interval selected. Please enter either 5 or 30")      


    # Add inverter info
    # Get meta data
    inverter_data = pd.read_csv("/mnt/f/05_Solar_Analytics/Solar_Analytics_data_transfer_" + region_name_string + "_region/" + region_name_string + "_inverter_panel_NS_modified.csv")
    # Combine time series and meta data
    # This should NOT cause any data deletion issues since left merge uses only keys from right frame (time_series_data) and preserves key order. 
    # Note that the inverter csv has been adjusted so that each site_id is only listed once. As result,  be careful when filtering by inverter type since some sites will have inverters which are not listed. 
    time_series_data = time_series_data.reset_index().merge(inverter_data, how = 'left', on='site_id').set_index('t_stamp') 

    return time_series_data





# Import CSV and store as pandas Data Frame
#-----------------------------------------------------------------------------------------------

def get_monthly_data_v_mid_pts(month_number) : 
    """Input the month number between 1 and 6. Output a tuple with two variables: a df containing the data from that CSV file and the month name as a string"""

    # Import data to pandas data frame
    month_number = int(month_number)
    
    if month_number >=1 and month_number <= 6 :
        csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/Five_minute_data_v_mid_pts/2017_0"+str(month_number)+"_v_mid_pt_averages.csv",index_col = 't_stamp', parse_dates=True)
    else : 
        raise ValueError("Invalid month selected. Please enter a value between 1 and 6")

    # Extract the month being examined
    start_date = csv_data.index[0]
    month_name = calendar.month_name[start_date.month]
    csv_data = csv_data.sort_index()
    # Store both output in a tuple so they can be 'unpacked' by the function call
    fnct_outputs = (csv_data, month_name)

    # Return the tuple    
    return fnct_outputs

#  Test
# data, data_month = open_csv(1)
# print(data.head())
# print(data.tail())
# print(data_month)



# Import data from each csv and combine into a single df
#-----------------------------------------------------------------------------------------------

def get_all_data_v_mid_pts() : 
    """Opens all six csv files and combines in a single data frame. Deletes unamed columns."""


    # Import January
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/Five_minute_data_v_mid_pts/2017_01_v_mid_pt_averages.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0', 'Unnamed: 0.1'], axis = 1)
    # Store in general df
    data = csv_data


    # Import February
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/Five_minute_data_v_mid_pts/2017_02_v_mid_pt_averages.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0', 'Unnamed: 0.1'], axis = 1)
    # Concatenate with existing df in general df
    data = pd.concat([data, csv_data])


    # Import March
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/Five_minute_data_v_mid_pts/2017_03_v_mid_pt_averages.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0'], axis = 1)
    # Concatenate with existing df in general df
    data = pd.concat([data, csv_data])


    # Import April
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/Five_minute_data_v_mid_pts/2017_04_v_mid_pt_averages.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0'], axis = 1)
    # Concatenate with existing df in general df
    data = pd.concat([data, csv_data])


    # Import May
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/Five_minute_data_v_mid_pts/2017_05_v_mid_pt_averages.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0'], axis = 1)
    # Concatenate with existing df in general df
    data = pd.concat([data, csv_data])


    # Import June
    csv_data = pd.read_csv("/mnt/f/05_Solar_Analytics/Five_minute_data_v_mid_pts/2017_06_v_mid_pt_averages.csv",index_col = 't_stamp', parse_dates=True)
    # Clean
    csv_data = csv_data.drop(['Unnamed: 0'], axis = 1)
    # Concatenate with existing df in general df
    data = pd.concat([data, csv_data])

    # Too slow!! do this after filtering or before graphing only
    # Sort ascending
    data = data.sort_index()

    return data

# def get_all_data_sorted():
#     return get_all_data().sorted()



def get_data_using_file_path(region_name_string, time_interval, data_file_path, meta_data_file_path, inverter_data_path):
    """ Imports 30 or 5 second data for region on a particular date (i.e. Victoria region for 18 January) including meta data and converts time zone to NEM time (Brisbane). 
    REGION STRING must be either 'adelaide', 'victoria' or 'south_australia' 
    FILE PATH must start from 05_Solar_Analytics"""

    # Get time series data
    time_series_data = pd.read_csv("/mnt/f/05_Solar_Analytics/" + data_file_path,index_col = 't_stamp', parse_dates=True)
    # Get meta data
    site_data = pd.read_csv("/mnt/f/05_Solar_Analytics/" + meta_data_file_path)
    # Combine time series and meta data
    time_series_data = time_series_data.reset_index().merge(site_data, how = 'left', on='c_id').set_index('t_stamp')

    # Convert to NEM time (Brisbane time, i.e. no daylight savings). First make aware, then conver time zones, then convert back to niave.
    time_series_data.index = time_series_data.index.tz_localize('UTC')
    time_series_data.index = time_series_data.index.tz_convert('Australia/Brisbane').tz_localize(None)
    # See list of time zones: https://stackoverflow.com/questions/13866926/python-pytz-list-of-timezones

    # Sort index to enable slicing
    time_series_data = time_series_data.sort_index()

    # Extract data for 30sec or 5 sec sites only

  

    # Extract data for time_interval specified
    # Find intervals for which 30 sec data exists (assumes all 30 sec data is on 25 and 55 intervals - may be wrong!!!)
    time_series_data['time_period_30s_flag'] = 0
    time_series_data.loc[time_series_data.index.second == 25, 'time_period_30s_flag'] = 1
    time_series_data.loc[time_series_data.index.second == 55, 'time_period_30s_flag'] = 1
    
    # Get list of cids for which there is definitely 5 sec data
    dummy_df = time_series_data[time_series_data['time_period_30s_flag'] == 0]
    list_5_sec_sites = dummy_df['c_id'].drop_duplicates()
    list_5_sec_sites = list_5_sec_sites.tolist()

    # Remove 30 sec flag col
    time_series_data = time_series_data.drop(['time_period_30s_flag'], axis = 1)

    # Slice df using list of 5 second cids
    if time_interval == 5:
        time_series_data = time_series_data[time_series_data.c_id.isin(list_5_sec_sites)]
    elif time_interval == 30:
        time_series_data = time_series_data[np.logical_not(time_series_data.c_id.isin(list_5_sec_sites))]
    else : 
        raise ValueError("Invalid time interval selected. Please enter either 5 or 30")      


    # Add inverter info
    # Get meta data
    inverter_data = pd.read_csv("/mnt/f/05_Solar_Analytics/"+ inverter_data_path)
    # Combine time series and meta data
    # This should NOT cause any data deletion issues since left merge uses only keys from right frame (time_series_data) and preserves key order. 
    # Note that the inverter csv has been adjusted so that each site_id is only listed once. As result,  be careful when filtering by inverter type since some sites will have inverters which are not listed. 
    time_series_data = time_series_data.reset_index().merge(inverter_data, how = 'left', on='site_id').set_index('t_stamp') 

    # Removes colums containing 'unnamed' in the title - important for merging in tableau since may get unpredictable results when unnamed columns persist. Note that unnamed are removed from csv's (denoted '_NS')
    time_series_data = time_series_data.loc[:, ~time_series_data.columns.str.contains('^Unnamed')]

    return time_series_data

# data = get_data_using_file_path('south_australia', 5, '2018-03-05_Solar_Analytics_Data_Transfer/south_australia_2017_03_03.csv', 'Solar_Analytics_data_transfer_adelaide_region/adelaide_site_data.csv')
# print(data)






# --------------------------------------------------25 August data transfer - different format
def get_august_data_using_file_path(time_interval, data_file_path, meta_data_file_path, inverter_data_path):
    # region_name_string = 'not required' 
    # time_interval = 5 #or 60 or 30
    # data_file_path = '2018-09-03_solar_analytics_data_transfer/2018-08-25_sa_qld_naomi.csv'
    # meta_data_file_path = '2018-09-03_solar_analytics_data_transfer/circuit_details.csv'
    # inverter_data_path = '2018-09-03_solar_analytics_data_transfer/site_details.csv'

    # Get time series data
    time_series_data = pd.read_csv("/mnt/f/05_Solar_Analytics/" + data_file_path,index_col = 'ts', parse_dates=True)

    # Get meta data
    site_data = pd.read_csv("/mnt/f/05_Solar_Analytics/" + meta_data_file_path)

    # Combine time series and meta data
    time_series_data = time_series_data.reset_index().merge(site_data, how = 'left', on='c_id').set_index('ts')

    # Convert to NEM time (Brisbane time, i.e. no daylight savings). First make aware, then conver time zones, then convert back to niave.
    time_series_data.index = time_series_data.index.tz_localize('UTC')
    time_series_data.index = time_series_data.index.tz_convert('Australia/Brisbane').tz_localize(None)
    # See list of time zones: https://stackoverflow.com/questions/13866926/python-pytz-list-of-timezones

    # Filter for duration specified (i.e. time_interval). Change NaNs to 5s then just filter directly
    time_series_data.loc[time_series_data.d.isnull(),'d'] = 5
    time_series_data = time_series_data[time_series_data['d'] == time_interval]

    # Correct polarity of energy and power
    time_series_data['p_polarity'] = time_series_data['p'] * time_series_data['polarity']
    time_series_data['e_polarity'] = time_series_data['e'] * time_series_data['polarity']

    # Add inverter info
    # Get meta data
    inverter_data = pd.read_csv("/mnt/f/05_Solar_Analytics/"+ inverter_data_path)

    # Flag sites with multiple inverters then keep only the first instance
    inverter_model_count = pd.DataFrame({'inverter_model_count' : inverter_data.groupby('site_id')['model'].count()}).reset_index()
    # Find sites with multiple inverters and add to list
    multiple_inverter_sites = inverter_model_count[inverter_model_count['inverter_model_count'] > 1.0]
    multiple_inverter_sites_list = multiple_inverter_sites['site_id'].tolist()

    # Create new column for flagging sites with multiple inverters and flag using list from above
    inverter_data['multiple_inverter_models'] = np.NaN
    inverter_data.loc[inverter_data.site_id.isin(multiple_inverter_sites_list), 'multiple_inverter_models'] = 1

    # Drop sites with multiple inverters - since this list doesn't contain c_ids, can just drop duplicates on site_id
    inverter_data_cut = inverter_data.drop_duplicates(subset = 'site_id', keep = 'first')

    # Combine time series and meta data
    # This should NOT cause any data deletion issues since left merge uses only keys from right frame (time_series_data) and preserves key order. 
    # Note that the inverter csv has been adjusted so that each site_id is only listed once. As result,  be careful when filtering by inverter type since some sites will have inverters which are not listed. 
    time_series_data = time_series_data.reset_index().merge(inverter_data_cut, how = 'left', on='site_id').set_index('ts') 

    # Add power in kW col
    if time_interval == 30:
        time_series_data['power_kW'] = time_series_data['e_polarity'] * 0.12 / 3600.0
    elif time_interval == 5:
        time_series_data['power_kW'] = time_series_data['e_polarity'] * 0.72 / 3600.0
    elif time_interval == 60:
        time_series_data['power_kW'] = time_series_data['e_polarity'] * 0.06 / 3600.0
    else:
        print('ERROR - did not specify which data set for energy --> power calc')

    return time_series_data



