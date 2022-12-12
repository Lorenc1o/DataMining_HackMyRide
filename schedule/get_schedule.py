import pandas as pd

# Open routes
routes = pd.read_csv('gtfs23Sept/routes.txt')
trips = pd.read_csv('gtfs23Sept/trips.txt')
stop_times = pd.read_csv('gtfs23Sept/stop_times.txt')
stops = pd.read_csv('gtfs23Sept/stops.txt')

# Get lines from routes
lines = routes['route_id'].unique()

# Get lines short_name from routes for each line
lines_short_name = {}
for line in lines:
    lines_short_name[line] = routes[routes['route_id'] == line]['route_short_name'].unique()[0]

# Get all trip_id from trips for each line and reset index
trips_lines = {}
for line in lines:
    trips_lines[line] = trips[trips['route_id'] == line]['trip_id'].reset_index(drop=True)

# Get all stop_id from stop_times for each line and reset index
#stops_lines = {}
#for line in lines:
#    stops_lines[line] = stop_times[stop_times['trip_id'].isin(trips_lines[line])]['stop_id'].reset_index(drop=True)

# Get all stop_id and stop_sequence from stop_times for each line and reset index
# Create stop_lines as pd.dataframe with columns departure_time, stop_id and stop_sequence
stops_lines = {}
for line in lines:
    stops_lines[line] = pd.DataFrame(columns=['trip_id', 'departure_time', 'stop_id', 'stop_sequence'])
    stops_lines[line] = stops_lines[line].append(stop_times[stop_times['trip_id'].isin(trips_lines[line])][['trip_id','departure_time', 'stop_id', 'stop_sequence']]).reset_index(drop=True)

# Add new column direction_id to stops_lines
for line in lines:
    stops_lines[line]['direction_id'] = 0

# For each consecutive sequence of stop_sequence, 
# add the stop_id of the last stop_sequence in the sequence to the direction_id column
# for all stop_id in the sequence
for line in lines:
    for i in range(len(stops_lines[line])-1):
        if stops_lines[line]['stop_sequence'][i] > stops_lines[line]['stop_sequence'][i+1]:
            for j in range(0, stops_lines[line]['stop_sequence'][i]):
                stops_lines[line]['direction_id'][i-j] = stops_lines[line]['stop_id'][i]

# For each line, divide stops_lines in as many dataframes as there are directions
# and add the direction_id to the name of the dataframe
stops_lines_directions = {}
for line in lines:
    stops_lines_directions[line] = {}
    for direction in stops_lines[line]['direction_id'].unique():
        stops_lines_directions[line][direction] = stops_lines[line][stops_lines[line]['direction_id'] == direction].reset_index(drop=True)

# For each line, for each direction, create a dataframe with the stop_id and departure_time
# for each trip_id
stops_lines_directions_departure = {}
for line in lines:
    stops_lines_directions_departure[line] = {}
    for direction in stops_lines_directions[line]:
        stops_lines_directions_departure[line][direction] = pd.DataFrame(columns=['trip_id', 'stop_id', 'departure_time'])
        for trip_id in stops_lines_directions[line][direction]['trip_id'].unique():
            stops_lines_directions_departure[line][direction] = stops_lines_directions_departure[line][direction].append(stops_lines_directions[line][direction][stops_lines_directions[line][direction]['trip_id'] == trip_id][['trip_id', 'stop_id', 'departure_time']]).reset_index(drop=True)

# For each line, for each direction, pivot the dataframe to have the trip_id as index,
# the stop_id as columns and the departure_time as values
stops_lines_directions_departure_pivot = {}
for line in lines:
    stops_lines_directions_departure_pivot[line] = {}
    for direction in stops_lines_directions_departure[line]:
        stops_lines_directions_departure_pivot[line][direction] = stops_lines_directions_departure[line][direction].pivot(index='trip_id', columns='stop_id', values='departure_time').reset_index(drop=True)
        # Save it as csv
        stops_lines_directions_departure_pivot[line][direction].to_csv('schedules/schedule_'+str(lines_short_name[line])+'_'+str(direction)+'.csv', index=False)

