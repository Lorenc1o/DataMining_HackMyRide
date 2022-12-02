import pandas as pd

# Open routes
routes = pd.read_csv('gtfs23Sept/routes.txt')
trips = pd.read_csv('gtfs23Sept/trips.txt')
stop_times = pd.read_csv('gtfs23Sept/stop_times.txt')
stops = pd.read_csv('gtfs23Sept/stops.txt')

# Get lines from routes
lines = routes['route_id'].unique()

# Get all trip_id from trips for each line and reset index
trips_lines = {}
for line in lines:
    trips_lines[line] = trips[trips['route_id'] == line]['trip_id'].reset_index(drop=True)

# Get all stop_id from stop_times for each line and reset index
stops_lines = {}
for line in lines:
    stops_lines[line] = stop_times[stop_times['trip_id'].isin(trips_lines[line])]['stop_id'].reset_index(drop=True)

# For each line, get stop_times whose trip_id is in trips_lines[line]
stop_times_lines = {}
for line in lines:
    stop_times_lines[line] = stop_times[stop_times['trip_id'].isin(trips_lines[line])].reset_index(drop=True)

# For each line, pivot stop_times_lines[line] to get stop_id as columns and trip_id as rows, with arrival_time as values
stop_times_lines_pivot = {}
for line in lines:
    stop_times_lines_pivot[line] = stop_times_lines[line].pivot(index='trip_id', columns='stop_id', values='arrival_time')
    # Save to csv
    stop_times_lines_pivot[line].to_csv('schedules/schedule_' + str(line) + '.csv')