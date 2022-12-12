import pandas as pd
import os

# For each schedule_i.csv in schedules/, compute headways and save to headways/headways_i.csv
for filename in os.listdir('schedules/'):
    # Open schedule with null as NaN
    schedule = pd.read_csv('schedules/' + filename, na_values=['null'])
    # Drop first column
    schedule = schedule.drop(schedule.columns[0], axis=1)
    # Convert values with hour 24:mm:ss to hour 00::mm:ss
    schedule = schedule.apply(lambda x: x.str.replace('24:', '00:'))
    # Convert values with hour 25:mm:ss to hour 01::mm:ss
    schedule = schedule.apply(lambda x: x.str.replace('25:', '01:'))
    # Convert values with hour 26:mm:ss to hour 02::mm:ss
    schedule = schedule.apply(lambda x: x.str.replace('26:', '02:'))
    # Convert values with hour 27:mm:ss to hour 03::mm:ss
    schedule = schedule.apply(lambda x: x.str.replace('27:', '03:'))
    # Convert data to datetime
    schedule = schedule.apply(pd.to_datetime)
    # Fill empty values with previous value in column
    schedule = schedule.fillna(method='ffill')
    # Compute headways as difference between arrival times for each stop
    headways = schedule.diff(axis=1)
    # Convert headways to seconds
    headways = headways.apply(lambda x: x.dt.total_seconds())
    # Save headways to headways/headways_i.csv
    headways.to_csv('headways/headways_' + filename[9:], index=False)
