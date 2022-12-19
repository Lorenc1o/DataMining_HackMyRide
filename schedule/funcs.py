import pandas as pd
import matplotlib.pyplot as plt
import gtfs_kit as gk
import numpy as np

# Function to compute difference of two hours in format 0 to infinity
def date_diff(df1:pd.Series, df2:pd.Series):
    diff = []
    for i in range(len(df1)):
        # Get current hours
        hour1 = df1.iloc[i]
        hour2 = df2.iloc[i]
        if hour1 is None or hour2 is None:
            diff.append(-999)
            continue
        # Compute difference in seconds
        h1 = hour1.split(':')
        h2 = hour2.split(':')
        diff.append((int(h1[0])*3600 + int(h1[1])*60 + int(h1[2])) - (int(h2[0])*3600 + int(h2[1])*60 + int(h2[2])))
    return diff
    
# Function to identify regularity or punctuality
def identify(row):
    if row['headway'] > 0 and row['headway'] < 60*12:
        return 'regularity'
    else:
        return 'punctuality'

def classify(df):
    # returns a df with column 'class':
    # if in df['candidate'] we find:
    # one 'regularity' between two 'punctuality' -> 'punctuality'
    # two 'regularity' between two 'punctuality' -> 'punctuality'
    # otherwise, same value as 'candidate'
    class_ = []
    counter = 0
    length = len(df)
    for i in range(length):
        if df.iloc[i]['candidate'] == 'punctuality':
            counter = 0
            class_.append('punctuality')
        else:
            if counter > 1:
                class_.append('regularity')
            elif counter == 1:
                if i < length - 1:
                    if df.iloc[i+1]['candidate'] == 'regularity':
                        class_.append('regularity')
                    else:
                        class_.append('punctuality')
                else:
                    class_.append('punctuality')
            else:
                if i < length - 2:
                    if df.iloc[i+1]['candidate'] == 'regularity' and df.iloc[i+2]['candidate'] == 'regularity':
                        class_.append('regularity')
                    else:
                        class_.append('punctuality')
                else:
                    class_.append('punctuality')
            counter += 1
    df['class'] = class_
    return df
        
def process_line(feed, line, day):
    timetable = gk.routes.build_route_timetable(feed,line,day)
    # Reorder timeline:
    # first by direction_id
    # then by stop
    # then by departure_time
    timetable = timetable.sort_values(by=['direction_id','stop_id','departure_time'])
    reduced_timetable = timetable[['trip_headsign','direction_id', 'stop_id','departure_time']]
    # For those stop_id with a letter at the end, remove it
    reduced_timetable['stop_id'] = reduced_timetable['stop_id'].apply(lambda x: x[:-1] if x[-1].isalpha() else x)
    # Compute the headways
    # by subtracting the departure time of the current stop to the departure time of the previous stop
    # using our function date_diff
    series = reduced_timetable['departure_time']
    series2 = reduced_timetable['departure_time'].shift(periods=1)
    reduced_timetable['headway'] = date_diff(series, series2)
    # use the identify function to create a new column
    reduced_timetable['candidate'] = reduced_timetable.apply(identify, axis=1)
    # use the classify function to create a new column
    reduced_timetable = classify(reduced_timetable)

    # now we can normalize the headways, setting the negative values to 0
    reduced_timetable['headway'] = reduced_timetable['headway'].apply(lambda x: 0 if x < 0 else x)

    return reduced_timetable[['trip_headsign','direction_id', 'stop_id','departure_time','headway','class']]

def show_headways(stop_id, timetable, direction_id=1):
    df = timetable.loc[(timetable.direction_id == direction_id) & (timetable.stop_id == stop_id)]
    # show only positive headways
    df = df[df['headway'] > 0]
    colors = df['class'].apply(lambda x: 'green' if x == 'regularity' else 'red')

    # show an horizontal line at 12*60 = 720 seconds
    plt.axhline(y=720, color='black', linestyle='--')
    # in the x axis, don't show all the hours, bin them in 10
    plt.xticks(np.arange(0, 36000, 3600))
    # Show as bar plot
    plt.bar(df['departure_time'], df['headway'], color=colors)
    # Add legend:
    # line = 12 minutes
    # green = regularity
    # red = punctuality
    handles = [plt.Rectangle((0,0),1,1, color='green'), plt.Rectangle((0,0),1,1, color='red')]
    plt.legend(handles, ['regularity', 'punctuality'])

'''
@function compute_scheduled_headways

@description
    Compute the scheduled headways for a given schedule, for all the stops in the schedule

@param schedule: pd.DataFrame with columns:
    - date: str
    - trip_headsign: str
    - direction_id: int
    - stop_id: str
    - departure_time: str
    - headway: int
    - class: str

@return: pd.DataFrame with columns:
    - date: str
    - stop_id: str
    - direction_id: int
    - interval_type: str
    - interval_id: int
    - interval_start: str
    - interval_end: str
    - avg_headway: float
    - swt: float
'''
def compute_scheduled_headways(schedule:pd.DataFrame):
    # create a new df
    df = pd.DataFrame(columns=['date','stop_id', 'trip_headsign', 'direction_id', 'interval_id', 'interval_start', 'interval_end', 'avg_headway', 'swt', 'interval_type'])
    # for each stop
    dates = schedule.date.unique()
    for date in dates:
        stops = schedule.loc[schedule.date == date].stop_id.unique()
        for stop in stops:
            for direction in [0,1]:
                for headsign in schedule.loc[(schedule.date == date) & (schedule.direction_id == direction) & (schedule.stop_id == stop)].trip_headsign.unique():
                    # get the schedule for that stop
                    stop_schedule = schedule.loc[(schedule.date == date) & (schedule.direction_id == direction) & (schedule.stop_id == stop)]
                    # make sure it is sorted by departure time
                    stop_schedule = stop_schedule.sort_values(by='departure_time')
                    current_start = -1
                    current_end = -1
                    interval_id = 0
                    sum = 0
                    square_sum = 0
                    count = 0
                    interval_type = ''
                    for i in range(len(stop_schedule)):
                        if stop_schedule.iloc[i]['class'] == 'punctuality':
                            if current_start != -1 and interval_type == 'regularity':
                                # we have reached the end of a regularity segment, compute the average headway
                                avg_headway = sum / count
                                swt = square_sum / (2*sum)
                                # add a new row to the df
                                df = df.append({'date':date,'trip_headsign': headsign,'stop_id': stop, 'direction_id':direction, 'interval_type':interval_type, 'interval_id': interval_id, 'interval_start': current_start, 'interval_end': current_end, 'avg_headway': avg_headway, 'swt': swt}, ignore_index=True)
                                # reset the variables
                                current_start = stop_schedule.iloc[i]['departure_time']
                                current_end = stop_schedule.iloc[i]['departure_time']
                                interval_id += 1
                                sum = stop_schedule.iloc[i]['headway']
                                square_sum = stop_schedule.iloc[i]['headway']**2
                                count = 1
                                interval_type = 'punctuality'
                            elif current_start != -1 and interval_type == 'punctuality':
                                # we are still in a punctuality segment
                                current_end = stop_schedule.iloc[i]['departure_time']
                                sum += stop_schedule.iloc[i]['headway']
                                square_sum += stop_schedule.iloc[i]['headway']**2
                                count += 1
                            else:
                                # we are entering a punctuality segment
                                current_start = stop_schedule.iloc[i]['departure_time']
                                current_end = stop_schedule.iloc[i]['departure_time']
                                sum = stop_schedule.iloc[i]['headway']
                                square_sum = stop_schedule.iloc[i]['headway']**2
                                count = 1
                                interval_type = 'punctuality'
                        else:
                            if current_start != -1 and interval_type == 'punctuality':
                                # we have reached the end of a punctuality segment, compute the average headway
                                avg_headway = sum / count
                                swt = square_sum / (2*sum)
                                # add a new row to the df
                                df = df.append({'date':date,'trip_headsign': headsign,'stop_id': stop, 'direction_id': direction, 'interval_type':interval_type, 'interval_id': interval_id, 'interval_start': current_start, 'interval_end': current_end, 'avg_headway': avg_headway, 'swt': swt}, ignore_index=True)
                                # reset the variables
                                current_start = stop_schedule.iloc[i]['departure_time']
                                current_end = stop_schedule.iloc[i]['departure_time']
                                interval_id += 1
                                sum = stop_schedule.iloc[i]['headway']
                                square_sum = stop_schedule.iloc[i]['headway']**2
                                count = 1
                                interval_type = 'regularity'
                            elif current_start != -1 and interval_type == 'regularity':
                                # we are still in a regularity segment
                                current_end = stop_schedule.iloc[i]['departure_time']
                                sum += stop_schedule.iloc[i]['headway']
                                square_sum += stop_schedule.iloc[i]['headway']**2
                                count += 1
                            else:
                                # we are entering a regularity segment
                                current_start = stop_schedule.iloc[i]['departure_time']
                                current_end = stop_schedule.iloc[i]['departure_time']
                                sum = stop_schedule.iloc[i]['headway']
                                square_sum = stop_schedule.iloc[i]['headway']**2
                                count = 1
                                interval_type = 'regularity'
                    # add the last segment
                    if count == 0:
                        interval_type = schedule.iloc[-1]['class']
                        current_start = schedule.iloc[-1]['departure_time']
                        current_end = schedule.iloc[-1]['departure_time']
                        sum = schedule.iloc[-1]['headway']
                        square_sum = schedule.iloc[-1]['headway']**2
                        count = 1
                    avg_headway = sum / count
                    swt = square_sum / (2*sum)
                    df = df.append({'date':date,'trip_headsign': headsign,'stop_id': stop,'direction_id': direction, 'interval_type':interval_type, 'interval_id': interval_id, 'interval_start': current_start, 'interval_end': current_end, 'avg_headway': avg_headway, 'swt': swt}, ignore_index=True)    
    return df

'''
def map_lines_to_headsigns(feed):
    # for each line, for each direction, get all possible values of headsign
    # map line to its route_short_name
    lines_short = feed.routes

    headsigns = {}
    for line in lines:
        headsigns[line] = {}
        for direction in [0,1]:
            headsigns[line][direction] = feed.trips.loc[(feed.trips.route_id == line) & (feed.trips.direction_id == direction)].trip_headsign.unique()
    return headsignsç
'''
