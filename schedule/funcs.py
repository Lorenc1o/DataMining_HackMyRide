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
        
def process_line(feed, line='65', day=['20210906']):
    #timetable = gk.routes.build_route_timetable(feed3s,line,day)
    timetable = gk.routes.build_route_timetable(feed,line,day)
    # Reorder timeline:
    # first by direction_id
    # then by stop
    # then by departure_time
    timetable = timetable.sort_values(by=['direction_id','stop_id','departure_time'])
    reduced_timetable = timetable[['trip_headsign','direction_id', 'stop_id','departure_time']]
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

    return reduced_timetable

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