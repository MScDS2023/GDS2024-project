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
        "Monza": "bacinger f1-circuits master circuits/it-1922.geojson",
        "Sakhir":"bacinger f1-circuits master circuits/bh-2002.geojson",
        "Spielberg": "bacinger f1-circuits master circuits/at-1969.geojson",
        "Spa Francorchamps": "bacinger f1-circuits master circuits/be-1925.geojson",
        "Monaco":"bacinger f1-circuits master circuits/mc-1929.geojson",
        "Melbourne":"bacinger f1-circuits master circuits/au-1953.geojson",
        "Silverstone":"bacinger f1-circuits master circuits/gb-1948.geojson",
        "Zandvoort":"bacinger f1-circuits master circuits/nl-1948.geojson"

    }
    return d[track]

def coordinate_shift(original_centroid, f1_api_coords):
    """This translates the original relative coordinates into longitude and latitude
    original_centroid is the centroid computed from the downloaded track data
    """
    centroid_lon, centroid_lat = (original_centroid.x, original_centroid.y)  
      
    # conversion factors - these are approximations, adjust as necessary  
    # 1 degree of latitude is approximately 111 km, and 1 degree of longitude is approximately 111 km multiplied by the cosine of the latitude  
    km_per_degree_lat = 1 / 110.574  
    km_per_degree_lon = 1 / (111.320 * math.cos(math.radians(centroid_lat)))  
    
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
    #dx = -0.004080352801855369
    #dy = -0.0063870841787121435
    # Shift the LineString  
    shifted_line = translate(relative_line, xoff=dx, yoff=dy)  
    return shifted_line

def shift_centroid_monza(relative_line):
    dx = -0.004080352801855369
    dy = -0.0063870841787121435
    # Shift the LineString  
    shifted_line = translate(relative_line, xoff=dx, yoff=dy)  
    return shifted_line

def shift_centroid_redbull_ring(relative_line):
    dx = 0.0029447601749765795
    dy = -0.001912651777622898
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

    centroid = track_coordinates.geometry.centroid.iloc[0]

    session = pull_data(year, track, event_type)

    projection = data_function(session, centroid)
    

    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=14, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr="Esri")  
    folium.GeoJson(projection).add_to(m)  
    m.save(f"templates/created_data/{year}_{track}_{event_type}.html")

    

def get_corners(session):
    circuit_info = session.get_circuit_info()
    corners_df = circuit_info.corners
    return corners_df


def shift_centroid_new(relative_line,dx, dy):
    # Shift the LineString  
    shifted_line = translate(relative_line, xoff=dx, yoff=dy)  
    return shifted_line



def get_corners_transformed(session,centroid, track_name,dx_dy):
    data = get_corners(session)
    coords = [(row['Y'],row['X']) for index,row in data.iterrows()]

    scaled_down = coordinate_shift(centroid, coords)
    if track_name == "Monza":
        shifted_line = shift_centroid_monza(scaled_down)
    elif track_name == "Spielberg":
        shifted_line = shift_centroid_redbull_ring(scaled_down)
    else:
        print(dx_dy,"hejsa")
        dx, dy = dx_dy
        shifted_line = shift_centroid_new(scaled_down,dx,dy)


    data['shifted_x'] = [x for x, y in shifted_line.coords]
    data['shifted_y'] = [y for x, y in shifted_line.coords]
    gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data['shifted_x'], data['shifted_y']), crs="EPSG:4326").reset_index(drop=True)
    return gdf.geometry


def create_track_buffered(track_geojson):
    # Load the GeoDataFrame
    monza_track = gpd.read_file(track_geojson) #This is monza

    monza_track_projected = monza_track.to_crs(epsg=32632)

    # Process the geometry to add width by buffering (buffer distance in meters)
    width_in_meters = 5  # Specify the width of the track. Adjust according to needs.
    track_buffered = monza_track_projected.copy(deep = True)
    track_buffered['geometry'] = track_buffered.geometry.buffer(width_in_meters)
    return track_buffered



def add_marker(map, centroid, track_name, index):
    # Add a red marker with a click event to redirect to dashboard with track_name and index as query parameters
    red_marker = folium.CircleMarker(
        location=(centroid.y, centroid.x),
        radius=7,
        color="black",
        fill=True,
        fill_color='black'
    )
    red_marker.add_child(folium.Popup(f'<a href="/dashboard?track_name={track_name}&index={index}" target="_blank">Go to corner {index}</a>'))
    red_marker.add_to(map)



def folium_with_corners(year, track_name, event_type,dx_dy):
    track_geojson = mapping_dict(track_name)

    session = pull_data(year, track_name, event_type)

    track_buffered = create_track_buffered(track_geojson)
    track = gpd.read_file(track_geojson) #This is monza
    
    centroid = track.geometry.centroid.iloc[0]


    all_centroids = get_corners_transformed(session,centroid, track_name, dx_dy)
    # Create a folium map centered at the centroid
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=15)

    # Add the GeoDataFrame to the map
    folium.GeoJson(track_buffered).add_to(m)


    for  counter, point in enumerate(all_centroids):
        add_marker(m,point, track_name, counter)
    m.save(f"templates/created_data/{year}_{track_name}_{event_type}.html")
    #return m._repr_html_()


    