import requests
from skyfield.api import EarthSatellite, load, wgs84
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from datetime import datetime, timedelta
from matplotlib.colors import Normalize
import matplotlib.cm as cm

from config import *


# ------------------------------ Helper Functions ------------------------------

def fetch_tle(sat_id):
    """
    Fetches the latest TLE data for a satellite using its NORAD ID from N2YO.

    Parameters:
        sat_id (int): NORAD ID of the satellite

    Returns:
        tuple: (name, line1, line2) if found, else (None, None, None)
    """
    try:
        request_url = TLE_URL.format(sat_id=sat_id, api_key=API_KEY)
        response = requests.get(request_url)
        response.raise_for_status()
        data = response.json()

        if 'tle' in data and data['tle']:
            tle_lines = data["tle"].splitlines()
            if len(tle_lines) >= 2:
                print(f"TLE lines for SAT_ID {sat_id}:\n{tle_lines[0]}\n{tle_lines[1]}")
                return (str(sat_id), tle_lines[0], tle_lines[1])
            else:
                print(f"Incomplete TLE data for SAT_ID {sat_id}.")
        else:
            print(f"No TLE data found for SAT_ID {sat_id}.")
        return (None, None, None)

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
        tuple: (Skyfield Time objects, corresponding datetime objects)
    """
    ts = load.timescale()
    end_time = start_time + timedelta(days=days)
    total_steps = int((days * 24 * 60) / step_minutes) + 1
    # Generate array of minutes to add
    minutes_array = step_minutes * np.arange(total_steps)
    # Calculate the corresponding datetime objects
    times_datetime = [start_time + timedelta(minutes=int(m)) for m in minutes_array]
    # Convert to Skyfield Time objects
    times = ts.utc([dt.year for dt in times_datetime],
                  [dt.month for dt in times_datetime],
                  [dt.day for dt in times_datetime],
                  [dt.hour for dt in times_datetime],
                  [dt.minute for dt in times_datetime],
                  [dt.second for dt in times_datetime])
    return times, times_datetime  # Return both Skyfield and datetime objects

# ------------------------------ Data Collection ------------------------------

def collect_satellite_data(satellites, times, times_datetime, filter_altitude=False):
    """
    Computes the geocentric positions of satellites over specified times
    and optionally filters out positions with altitude_km > MAX_ALTITUDE_KM.

    Parameters:
        satellites (list): List of EarthSatellite objects
        times (list): Skyfield Time objects
        times_datetime (list): Corresponding list of datetime objects
        filter_altitude (bool): Whether to filter positions with altitude_km > MAX_ALTITUDE_KM

    Returns:
        dict: Dictionary containing positions for each satellite
    """
    data = {}
    for sat in satellites:
        geocentric = sat.at(times)
        subpoint = geocentric.subpoint()
        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        alt_km = subpoint.elevation.km

        if filter_altitude:
            # Create a mask for altitudes <= MAX_ALTITUDE_KM
            mask = alt_km <= MAX_ALTITUDE_KM
            if np.any(mask):
                filtered_times = [times_datetime[i] for i, m in enumerate(mask) if m]
                data[sat.name] = {
                    'latitude': lat[mask],
                    'longitude': lon[mask],
                    'elevation_m': subpoint.elevation.m[mask],
                    'altitude_km': alt_km[mask],
                    'times': filtered_times
                }
                print(f"Satellite {sat.name}: {np.sum(mask)} points below {MAX_ALTITUDE_KM} km.")
            else:
                print(f"Satellite {sat.name} has no points below {MAX_ALTITUDE_KM} km.")
        else:
            # No filtering
            data[sat.name] = {
                'latitude': lat,
                'longitude': lon,
                'elevation_m': subpoint.elevation.m,
                'altitude_km': alt_km,
                'times': times_datetime  # All times
            }
            print(f"Satellite {sat.name}: {len(lat)} total points collected.")
    return data

# ------------------------------ Visualization ------------------------------

def plot_filtered_orbits(filtered_data, map_extent, center_lat, center_lon):
    """
    Plots filtered satellite paths on a map, color-coded based on altitude.

    Parameters:
        filtered_data (dict): Filtered satellite data with latitudes, longitudes, and altitudes
        map_extent (list): [West, East, South, North] in degrees
        center_lat (float): Center latitude for the map
        center_lon (float): Center longitude for the map
    """
    plt.figure(figsize=(15, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent(map_extent, crs=ccrs.PlateCarree())

    # Map features
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS)

    # Observer location
    ax.plot(OBSERVER_LON, OBSERVER_LAT, marker='^', color='red', markersize=12,
             transform=ccrs.PlateCarree(), label='Observer')

    # Prepare colormap
    cmap = cm.viridis
    norm = Normalize(vmin=0, vmax=MAX_ALTITUDE_KM)

    # Plot each satellite's data
    for sat_name, sat_data in filtered_data.items():
        latitudes = sat_data['latitude']
        longitudes = sat_data['longitude']
        alts = sat_data['altitude_km']

        scatter = ax.scatter(longitudes, latitudes, c=alts, cmap=cmap, norm=norm,
                             s=10, alpha=0.7, transform=ccrs.PlateCarree(), label=sat_name)

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, orientation='vertical', pad=0.02, shrink=0.7)
    cbar.set_label('Altitude (km)', fontsize=12)

    plt.title(f'Legion Satellites Orbits - Next {PREDICTION_DAYS} Days\n'
              f'Filtered to Altitudes ≤ {MAX_ALTITUDE_KM} km', fontsize=14)
    plt.legend(loc='upper right')
    plt.savefig(OUTPUT_IMAGE_FILTERED, dpi=300, bbox_inches='tight')
    plt.show()

def plot_all_orbits(all_data, map_extent, center_lat, center_lon):
    """
    Plots all satellite trajectories on a map without altitude filtering.

    Parameters:
        all_data (dict): All satellite data with latitudes and longitudes
        map_extent (list): [West, East, South, North] in degrees
        center_lat (float): Center latitude for the map
        center_lon (float): Center longitude for the map
    """
    plt.figure(figsize=(15, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent(map_extent, crs=ccrs.PlateCarree())

    # Map features
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS)

    # Observer location
    ax.plot(OBSERVER_LON, OBSERVER_LAT, marker='^', color='red', markersize=12,
             transform=ccrs.PlateCarree(), label='Observer')

    # Plot each satellite's trajectory
    for sat_name, sat_data in all_data.items():
        latitudes = sat_data['latitude']
        longitudes = sat_data['longitude']

        ax.plot(longitudes, latitudes, label=sat_name, alpha=0.5)
        ax.scatter(longitudes, latitudes, s=5, color='blue', alpha=0.3)

    plt.title(f'Legion Satellites Orbits - Next {PREDICTION_DAYS} Days\n'
              f'All Altitudes', fontsize=14)
    plt.legend(loc='upper right')
    plt.savefig(OUTPUT_IMAGE_ALL, dpi=300, bbox_inches='tight')
    plt.show()

# ------------------------------ Main Execution ------------------------------

def main():
    ts = load.timescale()

    start_time = datetime.utcnow()

    # Generate time steps
    print(f"Generating time steps from {start_time} for next {PREDICTION_DAYS} days...")
    times, times_datetime = generate_time_steps(start_time, PREDICTION_DAYS, TIME_STEP_MINUTES)

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

    # Collect satellite data with filtering
    print("Computing and filtering satellite positions...")
    filtered_satellite_data = collect_satellite_data(satellites, times, times_datetime, filter_altitude=True)

    # Collect all satellite data without filtering
    print("Collecting all satellite positions without filtering...")
    all_satellite_data = collect_satellite_data(satellites, times, times_datetime, filter_altitude=False)

    if not filtered_satellite_data:
        print(f"No satellite positions found below {MAX_ALTITUDE_KM} km.")

    # Plot filtered satellite orbits
    if filtered_satellite_data:
        print("Plotting filtered satellite orbits...")
        plot_filtered_orbits(filtered_satellite_data, MAP_EXTENT, CENTER_LAT, CENTER_LON)
        print(f"Filtered visualization saved as '{OUTPUT_IMAGE_FILTERED}'.")
    else:
        print("No filtered data to plot.")

    # Plot all satellite orbits
    print("Plotting all satellite orbits...")
    plot_all_orbits(all_satellite_data, MAP_EXTENT, CENTER_LAT, CENTER_LON)
    print(f"All orbits visualization saved as '{OUTPUT_IMAGE_ALL}'.")

if __name__ == "__main__":
    main()




