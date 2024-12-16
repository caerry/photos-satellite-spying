import requests
from skyfield.api import EarthSatellite, load, wgs84
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from datetime import datetime, timedelta

from config import *


def fetch_tle(sat_id):
    """
    Fetches the latest TLE data for a satellite using its NORAD ID from Celestrak.
    
    Parameters:
        sat_id (int): NORAD ID of the satellite
    
    Returns:
        tuple: (name, line1, line2) if found, else (None, None, None)
    """
    try:
        request_url = TLE_URL.format(
            sat_id,
            API_KEY,
        )
        response = requests.get(request_url)
        response.raise_for_status()
        data = response.json()
        
        tle_lines = data["tle"].splitlines()
        print("Tle lines for sat_id: ", sat_id, " are: ", tle_lines)
        return ( str(sat_id), tle_lines[0], tle_lines[1])

    except Exception as e:
        print(f"Error fetching TLE for satellite ID {sat_id}: {e}")
        return (None, None, None)

def generate_time_steps(start_time, days, step_minutes):
    """
    Generates a list of time steps for prediction.
    
    Parameters:
        start_time (datetime): The starting UTC time
        days (int): Number of days to predict
        step_minutes (int): Interval between steps in minutes
    
    Returns:
        list: List of Skyfield Time objects
    """
    ts = load.timescale()
    end_time = start_time + timedelta(days=days)
    total_steps = int((days * 24 * 60) / step_minutes) + 1
    times = ts.utc(start_time.year, start_time.month, start_time.day,
                  start_time.hour, start_time.minute + step_minutes * np.arange(total_steps))
    return times

# ------------------------------ Data Collection ------------------------------

def collect_satellite_data(satellites, times):
    """
    Computes the geocentric positions of satellites over specified times.
    
    Parameters:
        satellites (list): List of EarthSatellite objects
        times (list): Skyfield Time objects
    
    Returns:
        dict: Dictionary containing positions for each satellite
    """
    data = {}
    for sat in satellites:
        geocentric = sat.at(times)
        subpoint = geocentric.subpoint()
        data[sat.name] = {
            'latitude': subpoint.latitude.degrees,
            'longitude': subpoint.longitude.degrees,
            'elevation_m': subpoint.elevation.m,
            'altitude_km': subpoint.elevation.km
        }
    return data

# ------------------------------ Visualization ------------------------------

def plot_satellite_paths(data, map_extent, center_lat, center_lon):
    """
    Plots satellite paths on a map.
    
    Parameters:
        data (dict): Satellite data with latitudes and longitudes
        map_extent (list): [West, East, South, North] in degrees
        center_lat (float): Center latitude for the map
        center_lon (float): Center longitude for the map
    """
    plt.figure(figsize=(15, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent(map_extent, crs=ccrs.PlateCarree())
    
    # map features
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS)
    
    # observer location
    ax.plot(OBSERVER_LON, OBSERVER_LAT, marker='^', color='red', markersize=12,
            transform=ccrs.PlateCarree(), label='Observer')
    
    colors = ['blue', 'green', 'orange', 'purple', 'cyan']
    
    for idx, (sat_name, sat_data) in enumerate(data.items()):
        latitudes = sat_data['latitude']
        longitudes = sat_data['longitude']
        alts = sat_data['altitude_km']
        
        ax.plot(longitudes, latitudes, color=colors[idx % len(colors)], label=sat_name, alpha=0.7)
        ax.scatter(longitudes, latitudes, s=10, color=colors[idx % len(colors)], alpha=0.7)
    
    plt.title(f'Legion Satellites Orbits - Next {PREDICTION_DAYS} Days')
    plt.legend(loc='upper right')
    plt.savefig(OUTPUT_IMAGE, dpi=300, bbox_inches='tight')
    plt.show()


def main():
    ts = load.timescale()
    
    start_time = datetime.utcnow()
    
    # Generate time steps
    print(f"Generating time steps from {start_time} for next {PREDICTION_DAYS} days...")
    times = generate_time_steps(start_time, PREDICTION_DAYS, TIME_STEP_MINUTES)
    
    # Fetch TLEs and create EarthSatellite objects
    satellites = []
    print("Fetching TLE data...")
    for sat_id in SATELLITE_IDS:
        name, line1, line2 = fetch_tle(sat_id)
        if line1 and line2:
            sat = EarthSatellite(line1, line2, name, ts)
            satellites.append(sat)
            print(f"Fetched TLE for {name} (NORAD ID: {sat_id})")
        else:
            print(f"Skipping satellite ID {sat_id} due to missing TLE.")
    
    if not satellites:
        print("No satellites to track. Exiting.")
        return
    
    # Collect satellite data
    print("Computing satellite positions...")
    satellite_data = collect_satellite_data(satellites, times)
    
    # Plot satellite orbits
    print("Plotting satellite orbits...")
    plot_satellite_paths(satellite_data, MAP_EXTENT, CENTER_LAT, CENTER_LON)
    print(f"Visualization saved as '{OUTPUT_IMAGE}'.")

if __name__ == "__main__":
    main()
