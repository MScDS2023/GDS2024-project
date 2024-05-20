import fastf1
import geopandas as gpd
import folium
from shapely.affinity import translate  
from shapely.geometry import LineString
import math

from typing import Callable


def pull_data(year, track, event_type):
    """Returns the session"""
    session = fastf1.get_session(year, track, event_type)

    session.load(telemetry=True, laps=True)

    return session





def create_buffered_track(geojson_path: str):

    track = gpd.read_file(geojson_path) #This is monza
    
    centroid = track.geometry.centroid.iloc[0]

    # Ensure the GeoDataFrame is in WGS84 (lat/lon)
    track = track.to_crs(epsg=4326)

    # Convert to a projected CRS suitable for buffering (e.g., UTM)
    # Note: Choose the correct UTM zone for your specific data. Here, we assume zone 32N.
    # This is something we add manually 
    track_projected = track.to_crs(epsg=32632)
    # Process the geometry to add width by buffering (buffer distance in meters)

    width_in_meters = 5  # Specify the width of the track. Adjust according to needs.
    track_buffered = track_projected.copy(deep = True)
    track_buffered['geometry'] = track_buffered.geometry.buffer(width_in_meters)

        # Create a folium map centered at the centroid
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=15)

    # Add the GeoDataFrame to the map
    folium.GeoJson(track_buffered).add_to(m)
    return m._repr_html_
    #m.save(f"html/{save_file_as}.html")


def mapping_dict(track: str):
    d = {
        "monza": "../bacinger f1-circuits master circuits/it-1922.geojson",
        "bahrain":"../bacinger f1-circuits master circuits/bh-2002.geojson"
    }
    return d[track]

def coordinate_shift(original_centroid, f1_api_coords):
    """This translates the original relative coordinates into longitude and latitude
    original_centroid is the centroid computed from the downloaded track data
    """
    centroid_lon, centroid_lat = (original_centroid.x, original_centroid.y)  
      
    # conversion factors - these are approximations, adjust as necessary  
    # 1 degree of latitude is approximately 111 km, and 1 degree of longitude is approximately 111 km multiplied by the cosine of the latitude  
    km_per_degree_lat = 1 / 111  
    km_per_degree_lon = 1 / (111 * math.cos(math.radians(centroid_lat)))  
    
    # your array of tuples  
    xy_coordinates = f1_api_coords
    
    # convert each tuple in the array  
    lonlat_coordinates = []  
    for y,x in xy_coordinates:  
        lon = centroid_lon + (x / 10000) * km_per_degree_lon  # assuming x, y are in meters  
        lat = centroid_lat + (y / 10000) * km_per_degree_lat  # assuming x, y are in meters  
        lonlat_coordinates.append((lon,lat))  
    


    relative_line = LineString(lonlat_coordinates)
    return relative_line



def shift_centroid(relative_line,original_centroid):
    """This shift the centroid computed"""
    # Calculate the distance to translate in each direction  
    dx = original_centroid.x - relative_line.centroid.x  
    dy = original_centroid.y - relative_line.centroid.y  
    #print(dx, dy)
    #dx = -0.004080352801855369
    #dy = -0.0063870841787121435
    # Shift the LineString  
    shifted_line = translate(relative_line, xoff=dx, yoff=dy)  
    return shifted_line


def create_sample_map(session, centroid):
    laps = session.laps
    lap_55_1 = laps.pick_driver('1').pick_lap(10).get_telemetry()
    f1_api_coords = list(zip(lap_55_1["Y"],lap_55_1["X"]))
    
    scaled_down = coordinate_shift(centroid, f1_api_coords)
    shifted_line = shift_centroid(scaled_down,centroid)

 
    # Update your GeoDataFrame  
    gdf = gpd.GeoDataFrame(geometry=[shifted_line], crs="EPSG:4326")    
    new_projected = gdf.to_crs(epsg=32632)  
    return new_projected


def save_api_data(year: int, track: str, event_type: str, data_function: Callable):

    file = mapping_dict(track) 

    track_coordinates = gpd.read_file(file) #This is monza
    #monza_track = gpd.read_file("bacinger f1-circuits master circuits/nl-1948.geojson")

    centroid = track_coordinates.geometry.centroid.iloc[0]

    session = pull_data(year, track, event_type)

    projection = data_function(session, centroid)
    

    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=14, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr="Esri")  
    folium.GeoJson(projection).add_to(m)  
    m.save(f"templates/created_data/{year}_{track}_{event_type}.html")

    