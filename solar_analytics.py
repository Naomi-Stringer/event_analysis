# Solar analytics factory module
# Throws out solar analytics data as requested.


import numpy as np
import pandas as pd
import calendar
import datetime as dt

import util


#-----------------------------------------------------------------------------------------------
def get_august_data_using_file_path(time_interval, data_file_path, meta_data_file_path, inverter_data_path):

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



