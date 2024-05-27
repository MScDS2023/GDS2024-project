
import fastf1
import pandas as pd
import numpy as np
import folium
import geopandas as gpd
import math
from shapely.geometry import LineString
from shapely.affinity import translate
import matplotlib.pyplot as plt
import contextily as cx
import imageio.v2 as imageio
import os
import re


import warnings
warnings.filterwarnings("ignore")
# plt.switch_backend('Agg')



def find_track(directory, track):
    for filename in os.listdir(directory):
        if filename.endswith('.geojson'):  # Ensure the file is a shapefile
            track_layout = gpd.read_file(os.path.join(directory, filename))
            if track == track_layout['Location'][0]:
                # print(track_layout['Location'][0].split())  # Check if track name matches
                original_centroid = track_layout.geometry.centroid.iloc[0]
                return original_centroid
    return None



def get_laps(session, num_laps):
    telemetry_data = dict()
    drivers = session.drivers
    laps = session.laps

    for driver in drivers:
        driver_telemetry = []
        try:
            driver_laps = laps.pick_driver(driver)
            for counter, lap in enumerate(driver_laps.iterlaps()):
                if num_laps != "All Laps":
                    if counter == int(num_laps):
                        break
                telemetry = lap[1].get_telemetry()
                telemetry['LapNumber'] = lap[1]['LapNumber']
                driver_telemetry.append(telemetry)
            telemetry_data[driver] = pd.concat(driver_telemetry, ignore_index=True)
        except Exception as e:
            print(f"Error processing driver {driver}: {e}")
    
    modified_dfs = []

    for key, df in telemetry_data.items():
        df['driver'] = key
        modified_dfs.append(df)

    concatenated_df = pd.concat(telemetry_data)

    concatenated_df.reset_index(drop=True, inplace=True)
    concatenated_df['LapNumber'] = concatenated_df['LapNumber'].astype(int)
    concatenated_df = concatenated_df[(concatenated_df['Source'] == 'car') & (concatenated_df['Status'] == 'OnTrack')]
    return concatenated_df

def interpolate(df):
    df_interpolated = []
    for index, row in df.iterrows():
        df_interpolated.append([row['LapNumber'], row['driver'], row['X'], row['Y'], row['Speed'], row['RPM'], row['nGear'], row['Throttle'], row['Brake']])
        for i in range(5):
            df_interpolated.append([row['LapNumber'], row['driver'], np.nan, np.nan, np.nan, np.nan, row['nGear'], row['Throttle'], row['Brake']])

    df_interpolated = pd.DataFrame(df_interpolated, columns=['LapNumber', 'driver', 'X', 'Y', 'Speed', 'RPM', 'nGear', 'Throttle', 'Brake'])
    df_interpolated['X'] = df_interpolated['X'].interpolate(method='linear')
    df_interpolated['Y'] = df_interpolated['Y'].interpolate(method='linear')
    df_interpolated['Speed'] = df_interpolated['Speed'].interpolate(method='linear')
    df_interpolated['RPM'] = df_interpolated['RPM'].interpolate(method='linear')

    # Drop the last 5 entries
    df_interpolated = df_interpolated.iloc[:-5]

    return df_interpolated

def get_corners(session):
    circuit_info = session.get_circuit_info()
    corners_df = circuit_info.corners
    return corners_df

def filter_df_to_corner(df_to_filter, corner, index_threshold, corn_df, d_threshold):
    # Ensure corner is a valid index
    if corner < 0 or corner >= len(corn_df):
        raise ValueError("Invalid corner index")

    # Get the corner coordinates
    corner_x, corner_y = corn_df['X'].iloc[corner], corn_df['Y'].iloc[corner]

    # Create a copy of the DataFrame to avoid in-place modifications
    df_copy = df_to_filter.copy().reset_index()

    # Calculate the distance of each point to the corner
    df_copy['Distance_to_corner'] = np.sqrt((df_copy['X'] - corner_x) ** 2 + (df_copy['Y'] - corner_y) ** 2)

    # Find the index of the closest point to the corner
    closest_idx = df_copy['Distance_to_corner'].idxmin()
    # print(df_copy['Distance_to_corner'].iloc[closest_idx])

    # Determine the range of rows to select within the threshold distance
    lower_idx = max(0, closest_idx - index_threshold)
    upper_idx = min(len(df_copy), closest_idx + index_threshold)

    # Filter the DataFrame to get the rows within the threshold distance, including the closest point
    filtered = df_copy.iloc[lower_idx:upper_idx]

    # Further filter the DataFrame to keep only rows with Distance_to_corner less than d_threshold
    filtered = filtered[filtered['Distance_to_corner'] < d_threshold]

    return filtered

def coordinate_shift(original_centroid, f1_api_coords):
    """This translates the original relative coordinates into longitude and latitude
    original_centroid is the centroid computed from the downloaded track data
    """
    centroid_lon, centroid_lat = (original_centroid.x, original_centroid.y)  


      
    # conversion factors - these are approximations, adjust as necessary  
    # 1 degree of latitude is approximately 111 km, and 1 degree of longitude is approximately 111 km multiplied by the cosine of the latitude  
    #Old was 111 for both
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


def calculate_dx_dy(original_centroid, df):
    coords = [[row['Y'],row['X']] for index,row in df.iterrows()]
    test = coordinate_shift(original_centroid,coords)
    dx_all = original_centroid.x - test.centroid.x
    dy_all = original_centroid.y - test.centroid.y
    return dx_all, dy_all


def shift_centroid_new(relative_line,dx, dy):
    # Shift the LineString  
    shifted_line = translate(relative_line, xoff=dx, yoff=dy)  
    return shifted_line


def folium_plot(track_name:str,df,original_centroid,dx,dy,save_path):

    kat = folium.Map(location=[original_centroid.y, original_centroid.x], zoom_start=14, tiles='Esri.WorldImagery', attr="Esri",max_zoom=19,maxNativeZoom = 19)

    for lap in set(df['LapNumber']):
        for driver in set(df['driver']):
            data_ = df[(df['driver'] == driver) & (df['LapNumber'] == lap)]
            coords = [(row['Y'],row['X']) for index,row in data_.iterrows()]
            try:
                scaled_down = coordinate_shift(original_centroid,coords)
                shifted_line = shift_centroid_new(scaled_down,dx,dy)
            except Exception as e: 
                print(e)

            gdf_ = gpd.GeoDataFrame(geometry=[shifted_line], crs="EPSG:4326")    
            new_projected = gdf_.to_crs(epsg=32632)

            style = {'color': 'black', 'weight': 0.4}  # Adjust weight as needed

            folium.GeoJson(new_projected,style=style).add_to(kat)
    
    kat.save(os.path.join(save_path,f'{track_name}.html'))

    return None


def plot_all_drivers_for_lap(plot_data, lap,centroid,plot_type,corner,corn_df,dx,dy,save_path):
    gdfs = []

    for driver in set(plot_data['driver']):
        data = plot_data[(plot_data['driver'] == driver) & (plot_data['LapNumber'] == lap)]
        if data.empty:
            continue
        data_ = filter_df_to_corner(data,corner,100,corn_df,1000)
        coords = [(row['Y'], row['X']) for index, row in data_.iterrows()]
        try:
            scaled_down = coordinate_shift(centroid,coords)
            shifted_line = shift_centroid_new(scaled_down,dx,dy)
            data_['shifted_x'] = [x for x, y in shifted_line.coords]
            data_['shifted_y'] = [y for x, y in shifted_line.coords]
        except Exception as e: 
            print(e)
            continue

        if plot_type == 'Trajectory':

            points = list(zip(data_['shifted_x'], data_['shifted_y']))
            line = LineString(points)
            data_['geometry'] = line
            gdf = gpd.GeoDataFrame(data_, geometry='geometry', crs="EPSG:4326")
        
        elif plot_type in ['Speed','Brake','Throttle']:
            gdf = gpd.GeoDataFrame(data_, geometry=gpd.points_from_xy(data_['shifted_x'], data_['shifted_y']), crs="EPSG:4326").reset_index(drop=True)



        df_wm = gdf.to_crs(epsg=3857)
        gdfs.append(df_wm)

    # Concatenate all GeoDataFrames
    all_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))

    if plot_type == 'Trajectory':
        ax = all_gdf.plot(figsize=(10,14),color = 'black',linewidth = 0.1, alpha = 1)

        cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery, zoom=19)
        plt.title(f'Lap {lap} - All Drivers')
        plt.tight_layout()
        plt.savefig(os.path.join(save_path,f'Trajectory Lap {lap}.png'))
        plt.close()
    
    elif plot_type in ['Speed','Brake','Throttle']:
        ax = all_gdf.plot(column=plot_type, legend=True, figsize=(10, 14), cmap='OrRd', markersize=0.4, alpha=1)
        cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery, zoom=19)
        plt.title(f'Lap {lap} - All Drivers')
        plt.tight_layout()
        plt.savefig(os.path.join(save_path,f'{plot_type} Lap {lap}.png'))
        plt.close()


def plot_all_laps_all_drivers(plot_test, centroid,plot_type,corner,corn_df,dx,dy,save_path):
    # List to store GeoDataFrames for each lap and driver
    gdfs = []

    # dx,dy = calculate_dx_dy(centroid,df)

    for lap in set(plot_test['LapNumber']):
        for driver in set(plot_test['driver']):
            data = plot_test[(plot_test['driver'] == driver) & (plot_test['LapNumber'] == lap)]
            if data.empty:
                continue
            data_ = filter_df_to_corner(data,corner,100,corn_df,1000)
            coords = [(row['Y'], row['X']) for index, row in data_.iterrows()]
            try:
                scaled_down = coordinate_shift(centroid,coords)
                shifted_line = shift_centroid_new(scaled_down,dx,dy)
                data_['shifted_x'] = [x for x, y in shifted_line.coords]
                data_['shifted_y'] = [y for x, y in shifted_line.coords]
            except Exception as e: 
                print(e)
                continue

        if plot_type == 'Trajectory':

            points = list(zip(data_['shifted_x'], data_['shifted_y']))
            line = LineString(points)
            data_['geometry'] = line
            gdf = gpd.GeoDataFrame(data_, geometry='geometry', crs="EPSG:4326")
        
        elif plot_type in ['Speed','Brake','Throttle']:
            gdf = gpd.GeoDataFrame(data_, geometry=gpd.points_from_xy(data_['shifted_x'], data_['shifted_y']), crs="EPSG:4326").reset_index(drop=True)



        df_wm = gdf.to_crs(epsg=3857)
        gdfs.append(df_wm)

    # Concatenate all GeoDataFrames
    all_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))

    # Plot all laps and all drivers as points on the same plot
    # ax = all_gdf.plot(column='Speed', legend=True, figsize=(10, 14), cmap='OrRd', markersize=0.5, alpha=1)
    if plot_type == 'Trajectory':
        ax = all_gdf.plot(figsize=(10,14),color = 'black',linewidth = 0.1, alpha = 1)
        cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery, zoom=19)
        plt.title('All Laps - All Drivers')
        plt.tight_layout()
        plt.savefig(os.path.join(save_path,'Trajectory.png'))
        plt.close()

    
    elif plot_type in ['Speed','Brake','Throttle']:
        ax = all_gdf.plot(column=plot_type, legend=True, figsize=(10, 14), cmap='OrRd', markersize=0.4, alpha=1)
        cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery,zoom=19)
        plt.title('All Laps - All Drivers')
        plt.tight_layout()
        plt.savefig(os.path.join(save_path,f'{plot_type}.png'))
        plt.close()


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def create_gif(image_folder, save_path):
    images = []
    for filename in sorted(os.listdir(image_folder), key=natural_sort_key):
        if (filename.endswith('.png') or filename.endswith('.jpg')) and filename.startswith('Trajectory'):
            images.append(imageio.imread(os.path.join(image_folder, filename)))
    imageio.mimsave(save_path, images, duration=500)


def distance_func(driver1, driver2,df,lapnumber):
    dist = []
    driver1_geometries = pd.DataFrame(df[(df['driver'] == driver1) & (df['LapNumber'] == lapnumber)]['geometry'])
    driver2_geometries = pd.DataFrame(df[(df['driver'] == driver2) & (df['LapNumber'] == lapnumber)]['geometry'])
    
    for i in set(driver1_geometries['geometry']):
        for j in set(driver2_geometries['geometry']):
            distance = i.distance(j)
            if distance < 50:
                dist.append(distance)
            else:
                continue  
    if dist:
        mean_distance = np.mean(dist)
    else:
        mean_distance = float('inf')  
    
    return mean_distance


def str_to_tuple(s):
    s = s.strip('()')
    elements = s.split(', ')
    if len(elements) == 3:
        lap = int(elements[0])
        driver1 = elements[1].strip("'")
        driver2 = elements[2].strip("'")
        return (lap, driver1, driver2)
    else:
        return (None, None, None)


def clusters(df):
    set_drivers = set()
    clusters = []
    for index, row in df.iterrows():
        driver1 = row['driver1']
        driver2 = row['driver2']
        if driver1 not in set_drivers and driver2 not in set_drivers:
            clusters.append((driver1, driver2))
            set_drivers.add(driver1)
            set_drivers.add(driver2)

    # Convert clusters to a DataFrame (if needed)
    clusters_df = pd.DataFrame(clusters, columns=['Driver 1', 'Driver 2'])
    clusters_df = clusters_df.reset_index()
    clusters_df.rename(columns = {'index':'Cluster'}, inplace = True)
    return clusters_df

def runner_function(track_name:str,input_dict:dict,year:int,event_type:str,num_laps):
    directory = 'bacinger f1-circuits master circuits'
    track = track_name
    original_centroid = find_track(directory, track)
    try:
        os.mkdir(f'static/dashboard/{track}')
    except Exception as e:
        print(e)
    try:
        os.mkdir(f'static/dashboard/{track}/laps')
    except Exception as e:
        print(e)

    if original_centroid is None:
        return 'No track with this name was found, Exiting the function'

    session_load = fastf1.get_session(year, track, event_type)
    session_load.load(telemetry=True, laps=True, weather=False)        
    print("oiengouwenbgouwb")
    df = get_laps(session_load,num_laps) # long time


    interpolated_df = interpolate(df) # long time 


    print('Data loaded!')

    corners_df = get_corners(session_load)

    try:
        for j in set(corners_df.index):
            directory = f'corner{j}'
            parent_dir = f'static/dashboard/{track}'
            path = os.path.join(parent_dir, directory) 
            os.mkdir(path)
    except Exception as e:
        print(e)

    try:
        for j in set(corners_df.index):
            directory = f'corner{j}'
            parent_dir = f'static/dashboard/{track}/laps'
            path = os.path.join(parent_dir, directory) 
            os.mkdir(path)
    except Exception as e:
        print(e)
    
    dx,dy = calculate_dx_dy(original_centroid,interpolated_df) # long time
    if track_name.capitalize() in ["Monza"]:
        return dx,dy


    print('calculated dx, dy')

    if input_dict['Trajectory'] == True:
        for j in set(corners_df.index):
            directory = f'corner{j}'
            parent_dir = f'static/dashboard/{track}'
            path = os.path.join(parent_dir, directory)
            plot_all_laps_all_drivers(interpolated_df,original_centroid,'Trajectory',j,corners_df,dx,dy,path)
        
        if input_dict['Separate Laps'] == True:
            for i in set(df['LapNumber']):
                for j in set(corners_df.index):
                    directory = f'corner{j}'
                    parent_dir = f'static/dashboard/{track}/laps'
                    path = os.path.join(parent_dir, directory) 
                    plot_all_drivers_for_lap(interpolated_df,i,original_centroid,'Trajectory',j,corners_df,dx,dy,path)
                    
            for j in set(corners_df.index):
                directory = f'corner{j}'
                parent_dir_img = f'static/dashboard/{track}/laps'
                parent_dir_save = f'static/dashboard/{track}'
                img_path = os.path.join(parent_dir_img, directory)
                save_path = os.path.join(parent_dir_save, directory)
                create_gif(img_path,os.path.join(save_path,f'{track}.gif'))

    print('Trajectory DONE')

    if input_dict['Brake'] == True:
        for j in set(corners_df.index):
            directory = f'corner{j}'
            parent_dir = f'static/dashboard/{track}'
            path = os.path.join(parent_dir, directory) 
            plot_all_laps_all_drivers(interpolated_df,original_centroid,'Brake',j,corners_df,dx,dy,path)

        if input_dict['Separate Laps'] == True:
            for i in set(df['LapNumber']):
                for j in set(corners_df.index):
                    directory = f'corner{j}'
                    parent_dir = f'static/dashboard/{track}/laps'
                    path = os.path.join(parent_dir, directory) 
                    plot_all_drivers_for_lap(interpolated_df,i,original_centroid,'Brake',j,corners_df,dx,dy,path)  
    
    print('Brake DONE')

    if input_dict['Speed'] == True:
        for j in set(corners_df.index):
            directory = f'corner{j}'
            parent_dir = f'static/dashboard/{track}'
            path = os.path.join(parent_dir, directory) 
            plot_all_laps_all_drivers(interpolated_df,original_centroid,'Speed',j,corners_df,dx,dy,path)

    
        if input_dict['Separate Laps'] == True:
            for i in set(df['LapNumber']):
                for j in set(corners_df.index):
                    directory = f'corner{j}'
                    parent_dir = f'static/dashboard/{track}/laps'
                    path = os.path.join(parent_dir, directory) 
                    plot_all_drivers_for_lap(interpolated_df,i,original_centroid,'Speed',j,corners_df,dx,dy,path)
        
    print('Speed DONE')
    
    if input_dict['Throttle'] == True:
        for j in set(corners_df.index):
            directory = f'corner{j}'
            parent_dir = f'static/dashboard/{track}'
            path = os.path.join(parent_dir, directory) 
            plot_all_laps_all_drivers(interpolated_df,original_centroid,'Throttle',j,corners_df,dx,dy,path)

        if input_dict['Separate Laps'] == True:
            for i in set(df['LapNumber']):
                for j in set(corners_df.index):
                    directory = f'corner{j}'
                    parent_dir = f'static/dashboard/{track}/laps'
                    path = os.path.join(parent_dir, directory) 
                    plot_all_drivers_for_lap(interpolated_df,i,original_centroid,'Throttle',j,corners_df,dx,dy,path)
    
    print('Plots and GIFs DONE!')

    
    
    ### Creating Folium plot
    if input_dict['Folium'] == True:
        folium_dir = f'{track}'
        parent_folium_dir = f'static/dashboard/'
        folium_path = os.path.join(parent_folium_dir,folium_dir)
        folium_plot(track,interpolated_df,original_centroid,dx,dy,folium_path)

    print('Folium DONE!')


    ## Calculating distances
    if input_dict['Cluster'] == True:
        filtered_dfs = []
        for k in set(corners_df.index):
            for lap in set(interpolated_df['LapNumber']):
                for driver in set(interpolated_df['driver']):
                    data = interpolated_df[(interpolated_df['driver'] == driver) & (interpolated_df['LapNumber'] == lap)]
                    if data.empty:
                        continue
                    data_ = filter_df_to_corner(data,k,100,corners_df,1000)
                    filtered_dfs.append(data_)


            print('GOT ALL DRIVERS AND LAPS FILTERED')
            filtered_all = pd.concat(filtered_dfs, ignore_index=True)

            gdf = gpd.GeoDataFrame(filtered_all, geometry=gpd.points_from_xy(filtered_all['X'], filtered_all['Y'])).reset_index(drop=True)
            distances = {}

            print('NOW COMPUTING DISTANCES')
            for lap in set(gdf['LapNumber']):
                for i in set(gdf['driver']):
                        for j in set(gdf['driver']):
                                if i != j:
                                        distances[(lap,i,j)] = distance_func(i,j,gdf,lap)
            
            distance_df = pd.DataFrame(distances.items(), columns = ['driver-pairs', 'distance'])

            distance_save_dir = f'corner{k}'
            distance_save_parent_dir = f'static/dashboard/{track}'
            distance_save_path = os.path.join(distance_save_parent_dir, distance_save_dir)

            distance_df.to_csv(os.path.join(distance_save_path,'distances.csv'),index = False)

            print('SAVED DISTANCES')

            ### Calculating clusters
            distance_df[['lap', 'driver1', 'driver2']] = pd.DataFrame(distance_df['driver-pairs'].tolist(), index=distance_df.index)
            distance_df = distance_df.groupby(['driver1','driver2']).agg({'distance':'mean'}).reset_index()
            distance_df = distance_df.sort_values(by='distance')

            clusters_df = clusters(distance_df)
            clusters_df_melted = clusters_df.melt(id_vars=['Cluster'], value_vars=['Driver 1', 'Driver 2'], var_name='driver_type', value_name='driver')
            clusters_df_melted.to_csv(os.path.join(distance_save_path,'clusters.csv'))

            print('Clusters DONE!')
    
    return dx,dy