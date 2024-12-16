
import os 

API_KEY = os.getenv("N2YO_API_KEY") 

# Satellite NORAD IDs for Maxar Legion satellites
SATELLITE_IDS = [ 59625, 60453, 59626, 60452, 40115  ]

# Observer location 
OBSERVER_LAT = float(os.getenv("LAT"))   # Latitude
OBSERVER_LON = float(os.getenv("LON"))    # Longitude
OBSERVER_ALT = 200        # Altitude in meters

# Prediction settings
PREDICTION_DAYS = 10        # Predict for next 10 days
TIME_STEP_MINUTES = 10      # Time interval between predictions (e.g., every 10 minutes)

# Map settings
CENTER_LAT = 55.0
CENTER_LON = 30.0
MAP_EXTENT = [-25, 45, 30, 75]  # [West, East, South, North]

# TLE Source URL: N2YO API for satellite TLE
TLE_URL = "https://api.n2yo.com/rest/v1/satellite/tle/{sat_id}&apiKey={api_key}"

# Output Images
OUTPUT_IMAGE_FILTERED = "satellite_orbits_filtered.png"
OUTPUT_IMAGE_ALL = "satellite_orbits_all.png"
OUTPUT_IMAGE = "satellite_orbits.png"

# Maximum Altitude for Filtering
MAX_ALTITUDE_KM = 800  # Maximum altitude in kilometers
