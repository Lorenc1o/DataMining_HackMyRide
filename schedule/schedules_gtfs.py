import gtfs_kit as gk
from pathlib import Path

# Compute schedule for gtfs23Sept.zip
file = Path('/home/jose/Desktop/Lorenc1o-repos/DataMining_HackMyRide/'+'gtfs23Sept.zip')
feed = (gk.read_feed(file, dist_units='km'))
feed.validate()