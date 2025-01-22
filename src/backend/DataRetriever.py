import constants, DataManager
from datetime import datetime, timedelta
from enum import Enum
from math import atan2, cos, radians, sin, sqrt
from PIL import Image, ImageDraw
from scipy.interpolate import griddata, interp1d
from scipy.spatial import ConvexHull
from tensorflow.keras.models import load_model

import ee
import hdbscan
import numpy as np
import pandas as pd
import requests
import time
import tensorflow as tf
import xmltodict


class LimitAPI:
    """
    Constructor

    Args:
      call_limit: Maximum number of calls
      interval: Interval in seconds until number of calls is refreshed
    """
    def __init__(self, call_limit, interval):
        self.call_limit = call_limit
        self.interval = interval
        self.calls = 0
        self.start_time = time.time()

    def can_call(self):
        if time.time() - self.start_time > self.interval:
            self.calls = 0
            self.start_time = time.time()

        return self.calls < self.call_limit

    def call(self):
        if (self.calls >= self.call_limit):
            # Wait until refresh
            cushion = 5
            time.sleep(max(0, self.interval - (time.time() - self.start_time) + cushion))
            print('Currently waiting...', flush=True)

        # Refresh number of calls if possible
        if (time.time() - self.start_time > self.interval):
            self.calls = 0
            self.start_time = time.time()

        self.calls += 1


Feature = Enum('Feature', 
               [
                   'ELEVATION', 
                   'WIND_DIRECTION', 
                   'WIND_SPEED', 
                   'TEMP_MIN', 
                   'TEMP_MAX', 
                   'HUMIDITY', 
                   'PRECIPITATION', 
                   'DROUGHT', 
                   'VEGETATION', 
                   'POPULATION', 
                   'ERC', 
                   'PREV_MASK', 
                   'NEW_MASK'
                ], 
                start=0)


DATA_STATS = {
    # Elevation in m.
    # 0.1 percentile, 99.9 percentile
    Feature.ELEVATION: (0.0, 3141.0, 657.3003, 649.0147),
    
    # Drought Index (Palmer Drought Severity Index)
    # 0.1 percentile, 99.9 percentile
    Feature.DROUGHT: (-6.12974870967865, 7.876040384292651, -0.0052714925, 2.6823447),
    
    #Vegetation index (times 10,000 maybe, since it's supposed to be b/w -1 and 1?)
    Feature.VEGETATION: (-9821.0, 9996.0, 5157.625, 2466.6677),  # min, max
   
    # Precipitation in mm.
    # Negative values do not make sense, so min is set to 0.
    # 0., 99.9 percentile
    Feature.PRECIPITATION: (0.0, 44.53038024902344, 1.7398051, 4.482833),
   
    # Specific humidity.
    # Negative values do not make sense, so min is set to 0.
    # The range of specific humidity is up to 100% so max is 1.
    Feature.HUMIDITY: (0., 1., 0.0071658953, 0.0042835088),
    
    # Wind direction in degrees clockwise from north.
    # Thus min set to 0 and max set to 360.
    Feature.WIND_DIRECTION: (0., 360.0, 190.32976, 72.59854),
    
    # Min/max temperature in Kelvin.
    
    #Min temp
    # -20 degree C, 99.9 percentile
    Feature.TEMP_MIN: (253.15, 298.94891357421875, 281.08768, 8.982386),
    
    #Max temp
    # -20 degree C, 99.9 percentile
    Feature.TEMP_MAX: (253.15, 315.09228515625, 295.17383, 9.815496),
    
    # Wind speed in m/s.
    # Negative values do not make sense, given there is a wind direction.
    # 0., 99.9 percentile
    Feature.WIND_SPEED: (0.0, 10.024310074806237, 3.8500874, 1.4109988),
    
    # NFDRS fire danger index energy release component expressed in BTU's per
    # square foot.
    # Negative values do not make sense. Thus min set to zero.
    # 0., 99.9 percentile
    Feature.ERC: (0.0, 106.24891662597656, 37.326267, 20.846027),
    
    # Population density
    # min, 99.9 percentile
    Feature.POPULATION: (0., 2534.06298828125, 25.531384, 154.72331), 
    
    # We don't want to normalize the FireMasks.
    # 1 indicates fire, 0 no fire, -1 unlabeled data
    Feature.PREV_MASK: (-1., 1., 0., 1.),
    Feature.NEW_MASK: (-1., 1., 0., 1.)
}

# Declare variables & constants
generation_time = datetime.now()
end_date = f'{generation_time.strftime("%Y-%m-%d")}'
start_date = f'{(generation_time - timedelta(days=30)).strftime("%Y-%m-%d")}'

FIRMS_API_KEY = constants.FIRMS_API_KEY
FIRMS_AREA_COORDS = '-125,25,-65,50'    # America
FIRMS_DAY_RANGE = f'{1}'

BLOCK_SIZE = 32
ARC_DEGREE_DISTANCE = 111.32
SCALING_FACTOR = 40

OPENWEATHERMAP_API_KEY = constants.OPENWEATHERMAP_API_KEY

# OpenWeatherMap API limiter
weather_limiter = LimitAPI(60, 60)

try:
    # Earth Engine setup
    ee.Authenticate()
    ee.Initialize(project=constants.EE_PROJECT_NAME)
except Exception:
    print('There was an issue initializing the Google Earth Engine API', flush=True)
    raise

# Load the prediction model
model = load_model('assets/fire_predict_50.h5')

run_id = -1

def haversine(coord1: tuple[float, float], coord2: tuple[float, float]) -> dict[str, float]:
    """
    Compute the haversine distance between two coordinate points

    Args:
      coord1: Coordinate point
      coord2: Coordinate point

    Returns:
      Dictionary with keys 'lat', 'lng', and 'dst' for latitudinal distance, longitudinal distance, and distance respectively.
    """
    lat1, lng1, lat2, lng2 = map(radians, [coord1[0], coord1[1], coord2[0], coord2[1]])

    return {
        "lat": _haversine(lat1, (lng1 + lng2) / 2.0, lat2, (lng1 + lng2) / 2.0), 
        "lng": _haversine((lat1 + lat2) / 2.0, lng1, (lat1 + lat2) / 2.0, lng2), 
        "dst": _haversine(lat1, lng1, lat2, lng2)
    }


def _haversine(lat1: float=0.0, lng1: float=0.0, lat2: float=0.0, lng2: float=0.0) -> float:
    """
    Auxiliary function to compute the haversine distance
    """
    lat = lat2 - lat1
    lng = lng2 - lng1

    a = sin(lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return c * 6371


def _adjust_latitude(coordinate: tuple[float, float], distance: float) -> float:
    """
    Compute the necessary change in latitude at a particular coordinate to account for kilometer distance adjustment
    """
    return distance / ARC_DEGREE_DISTANCE


def _adjust_longitude(coordinate: tuple[float, float], distance: float) -> float:
    """
    Compute the necessary change in longitude at a particular coordinate to account for kilometer distance adjustment
    """
    return distance / (cos(radians(coordinate[0])) * ARC_DEGREE_DISTANCE)


def adjusted_coordinate(coordinate: tuple[float, float], lat_adj: float, lng_adj: float) -> tuple[float, float]:
    """
    Compute coordinate after a km adjustment to the latitude and/or longitude

    Args:
      coordinate: Coordinate point to adjust
      lat_adj: Kilometer adjustment to latitude, with positive adjustment relating to North
      lng_adj: Kilometer adjustment to longitude, with positive adjustment relating to East

    Returns:
      Coordinate point with latitude and/or longitude adjusted
    """
    return (
        coordinate[0] + _adjust_latitude(coordinate, lat_adj), 
        coordinate[1] + _adjust_longitude(coordinate, lng_adj)
    )


def pad_region(coord_min: tuple[float, float], coord_max: tuple[float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Pad region by adjusting its identifying coordinate points

    Args:
      coord_min: South-west point identifying region
      coord_max: North-east point identifying region

    Returns:
      Minimum and maximum coordinate point identifying the region
    """
    d_lat = haversine(coord_min, coord_max)['lat']  # Latitudinal distance
    d_lng = haversine(coord_min, coord_max)['lng']  # Longitudinal distance

    lat_pad = (float(BLOCK_SIZE) - (d_lat % BLOCK_SIZE)) / 2.0
    lng_pad = (float(BLOCK_SIZE) - (d_lng % BLOCK_SIZE)) / 2.0

    padded_coord_min = adjusted_coordinate(coord_min, -lat_pad, -lng_pad)
    padded_coord_max = adjusted_coordinate(coord_max, lat_pad, lng_pad)

    return padded_coord_min, padded_coord_max


def get_clusters(firms_date: str) -> pd.DataFrame:
    """
    Retrieve data from FIRMS and cluster points

    Args:
      firms_date: String representing the FIRMS date

    Returns:
      Dataframe containing cluster data

    Raises:
      Error if there are no clusters retrieved
    """
    firms_sources = [
        # 'LANDSAT_NRT', 
        'MODIS_NRT', 
        'VIIRS_NOAA20_NRT', 
        'VIIRS_NOAA21_NRT', 
        'VIIRS_SNPP_NRT'
    ]

    dfs = []

    try:
        for source in firms_sources:
            # Read API endpoint CSV response
            temp_df = pd.read_csv(f'https://firms.modaps.eosdis.nasa.gov/usfs/api/area/csv/{FIRMS_API_KEY}/{source}/{FIRMS_AREA_COORDS}/{FIRMS_DAY_RANGE}/{firms_date}', sep=',')

            if 'MODIS' in source:
                # Refer to: https://www.earthdata.nasa.gov/learn/find-data/near-real-time/firms/mcd14dl-nrt#ed-firms-attributes
                temp_df = temp_df[temp_df['confidence'] >= 50]
            elif 'VIIRS' in source:
                # 'l' : low; 'n' : nominal; 'h' : high
                # Refer to: https://www.earthdata.nasa.gov/learn/find-data/near-real-time/firms/vj114imgtdlnrt
                # temp_df = temp_df[(temp_df['confidence'] == 'l') | (temp_df['confidence'] == 'n') | (temp_df['confidence'] == 'h')]
                temp_df = temp_df[(temp_df['confidence'] == 'h')]
            # elif 'LANDSAT' in source:
            #     # 'L' : low, 'M' : medium, 'H' : high
            #     temp_df = temp_df[(temp_df['confidence'] == 'H')]
            else:
                raise Exception("Unexpected FIRMS source found.")

            temp_df[['latitude', 'longitude']]
            temp_df['source'] = source

            dfs.append(temp_df)
    except Exception:
        print(f'There was an issue retrieving data from FIRMS.', flush=True)
        raise

    df = pd.concat(dfs, ignore_index=True)

    min_cluster_size = 3

    # There is an abnormally low number of points
    if len(df) < min_cluster_size:
        return pd.DataFrame()

    clustering = hdbscan.HDBSCAN(
        metric='haversine',
        min_cluster_size=min_cluster_size, 
        gen_min_span_tree=True
    ).fit(np.radians(df[['latitude', 'longitude']]))

    labels = clustering.labels_
    df['cluster'] = labels

    # Retrieve number of clusters
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f'Identified {n_clusters} clusters.', flush=True)

    if (n_clusters == 0):
        raise Exception('There are no clusters')

    return df


def _process_weather(dict: dict[str, any], feature: Feature) -> str:
    """
    Retrieve feature from XML response

    Args:
      dict: Dictionary-converted XML response
      feature: Weather feature to parse
    
    Returns:
      Feature value (as string) or 'None' if not found
    """
    try:
        match feature:
            case Feature.WIND_SPEED:
                return dict['current']['wind']['speed']['@value']
            case Feature.WIND_DIRECTION:
                return dict['current']['wind']['direction']['@value']
            case Feature.TEMP_MIN:
                return dict['current']['temperature']['@min']
            case Feature.TEMP_MAX:
                return dict['current']['temperature']['@max']
            case Feature.HUMIDITY:
                return dict['current']['humidity']['@value']
            case Feature.PRECIPITATION:
                return 0.0 if dict['current']['precipitation']['@mode'] == 'no' else dict['current']['precipitation']['@value']
            case _:
                return None
    except Exception:
        return None


def get_current_mask(d_lat: int, d_lng: int, origin: tuple[float, float], points: pd.DataFrame) -> np.ndarray:
    """
    Get the current fire mask

    Args:
      d_lat: Latitudinal distance
      d_lng: Longitudinal distance
      origin: North-west point
      points: Cluster points

    Returns:
      Array representing presence of fire in region with bit values
    """
    # Image voodoo
    # Make sure scaling factor is divisible by 8 so we can represent 375m (3/8)

    width = d_lng * SCALING_FACTOR
    height = d_lat * SCALING_FACTOR

    img = Image.new('1', (width, height))

    draw = ImageDraw.Draw(img)
    for _, row in points.iterrows():
        point = (row['latitude'], row['longitude'])
        # print(f"Lat: {row['latitude']} ; Lng: {row['longitude']}", flush=True)

        offsets = haversine(origin, point)
        # print(f"Latitudinal offset is {offsets['lat']}; Longitudinal offset is {offsets['lng']}", flush=True)

        offset_y = offsets['lat'] * SCALING_FACTOR
        offset_x = offsets['lng'] * SCALING_FACTOR

        scale = -1
        if 'MODIS' in row['source']:
            scale = 1
        elif 'VIIRS' in row['source']:
            # VIIRS has 375m spatial resolution so adjust accordingly
            scale = 0.375
        # elif 'LANDSAT' in row['source']:
        #     # LANDSAT has 30m spatial resolution so adjust accordingly
        #     scale = 0.03
        else:
            raise Exception("Unexpected FIRMS source found.")

        adjustment = scale * SCALING_FACTOR
        square = [
            (offset_x - adjustment, offset_y - adjustment), 
            (offset_x + adjustment, offset_y + adjustment)
        ]

        draw.rectangle(square, fill=1)
    
    # Downsample the array and get the bit matrix
    return np.array(
        img.resize(
            (
                round(width / SCALING_FACTOR), 
                round(height / SCALING_FACTOR)
            )
        )
    )


def get_weather_data(coord: tuple[float, float], dict: dict[str, float]):
    """
    Get relevant weather data from OpenWeatherMap API

    Args:
      coord: Coordinate point to get weather data at
      dict: Dictionary to populate
    """

    retrieval_start = time.time()

    while True:
        try:
            weather_limiter.call()
            response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?lat={coord[0]}&lon={coord[1]}&appid={OPENWEATHERMAP_API_KEY}&mode=xml')
            break
        except Exception as e:
            print(f'Failed to get weather data. Details: {e}', flush=True)
            
            if time.time() - retrieval_start > 300:
                print(f'Time to retrieve weather data has exceeded 5 minutes.', flush=True)
                raise

            time.sleep(30)

    if response.status_code != 200:
        raise Exception('Could not access OpenWeatherMap.')

    # assumptions about units (wind speed, temperature, humidity, precipitation in mm)
    # Refer to "https://openweathermap.org/current"
    weather_dict = xmltodict.parse(response.content)

    dict[Feature.WIND_SPEED] = _process_weather(weather_dict, Feature.WIND_SPEED)
    dict[Feature.WIND_DIRECTION] = _process_weather(weather_dict, Feature.WIND_DIRECTION)
    dict[Feature.TEMP_MIN] = _process_weather(weather_dict, Feature.TEMP_MIN)
    dict[Feature.TEMP_MAX] = _process_weather(weather_dict, Feature.TEMP_MAX)
    dict[Feature.HUMIDITY] = _process_weather(weather_dict, Feature.HUMIDITY)
    dict[Feature.PRECIPITATION] = _process_weather(weather_dict, Feature.PRECIPITATION)


def get_gee_data(coord: tuple[float, float], bounding_coords: list[float], dict: dict[str, float]):
    """
    Get relevant feature data from Google Earth Engine

    Args:
      coord: Coordinate point to get feature data at
      bounding_coords: Coordinates identifying cluster region
      dict: Dictionary to populate
    """
    point = ee.Geometry.Point(coord[1], coord[0])
    bounding_box = ee.Geometry.Rectangle(bounding_coords)

    # Elevation
    elevation = ee.Image('CGIAR/SRTM90_V4')
    elevation_clipped = elevation.clip(bounding_box)
    dict[Feature.ELEVATION] = elevation_clipped.reduceRegion(reducer = ee.Reducer.mean(), geometry = point.buffer(500).bounds(), scale = 1000).get('elevation').getInfo()

    # Drought
    drought = ee.ImageCollection('GRIDMET/DROUGHT').filterDate(start_date, end_date).filterBounds(bounding_box).sort('system:time_start', False).first().select('pdsi')
    dict[Feature.DROUGHT] = drought.reduceRegion(reducer = ee.Reducer.mean(), geometry = point.buffer(1000).bounds(), scale = 1000).get('pdsi').getInfo()

    # Vegetation
    veg = ee.ImageCollection('NOAA/VIIRS/001/VNP13A1').filterDate(start_date, end_date).filterBounds(bounding_box).select('NDVI').mean()
    dict[Feature.VEGETATION] = veg.reduceRegion(reducer = ee.Reducer.mean(), geometry = point.buffer(1000).bounds(), scale = 1000).get('NDVI').getInfo()

    # Population Density
    pop_dens = ee.ImageCollection("CIESIN/GPWv411/GPW_Population_Density").sort('system:time_start', False).first().select('population_density')
    dict[Feature.POPULATION] = pop_dens.reduceRegion(reducer = ee.Reducer.mean(), geometry = point.buffer(1000).bounds(), scale = 1000).get('population_density').getInfo()

    # Energy Release Component
    erc = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").filterDate(start_date, end_date).filterBounds(bounding_box).sort('system:time_start', False).first().select('erc')
    dict[Feature.ERC] = erc.reduceRegion(reducer = ee.Reducer.mean(), geometry = point.buffer(1000).bounds(), scale = 1000).get('erc').getInfo()


def get_interpolated_data(dict: dict[tuple[float, float], dict[str, float]], d_lat: int, d_lng: int) -> dict[str, np.ndarray]:
    coords = list(dict.keys())
    data = list(dict.values())
    attributes = list(data[0].keys())

    xv, yv = np.meshgrid(
        np.arange(0, d_lng), 
        np.arange(0, d_lat)
    )

    interpolated_data = {}
    try:
        for attribute in attributes:
            values = [float(datum[attribute]) if datum[attribute] is not None else np.nan for datum in data]

            valid_indices = ~np.isnan(np.array(values))

            valid_coords = np.array(coords)[valid_indices]
            valid_values = np.array(values)[valid_indices]

            # if sum(valid_indices) < 3:
            #     print(f'There were not enough points for interpolation. Cluster will not be included.', flush=True)
            #     return {}

            interpolated = griddata(valid_coords, valid_values, (xv, yv), method='linear', fill_value=np.mean(valid_values))
            interpolated_data[attribute] = interpolated.tolist()
    except Exception as e:
        print(f'Issue occurred during interpolation. Fire will be ignored.', flush=True)
        interpolated_data.clear()
    
    return interpolated_data


def get_mask_coords(data: np.ndarray, origin: tuple[float,float], predicted: bool=False) -> list[tuple[float, float]]:
    """
    Get the points that identify the mask

    Args:
      data: Array with entries identifying fire
      origin: North-west point
      predicted: Boolean value identifying if mask is a predicted mask

    Returns:
      Ordered coordinates identifying mask, or empty array if there are not enough points to create the mask
    """
    threshold = np.nanpercentile(data, 99) if predicted else 0

    rows, cols = np.where(data > threshold)

    if len(rows) < 3:
        return []

    fire_indices = np.column_stack((rows, cols))

    hull = ConvexHull(points=fire_indices, qhull_options='QJ')

    # Clockwise ordering of points
    centroid = np.mean(fire_indices[hull.vertices], axis = 0)
    angles = np.arctan2(
        fire_indices[hull.vertices, 1] - centroid[1], 
        fire_indices[hull.vertices, 0] - centroid[0]
    )

    ordering = hull.vertices[np.argsort(angles)]

    return [adjusted_coordinate(origin, -lat_adj, lng_adj) for lat_adj, lng_adj in fire_indices[ordering]]


def process_clusters(run_id: int, df: pd.DataFrame):
    """
    Process each cluster by retrieving data from APIs and running the AI model to generate a predicted fire mask

    Args:
      run_id: Engine run identifier
      df: DataFrame containing cluster data
    """
    # Filter unique clusters
    clusters = df[df['cluster'] >= 0]['cluster'].unique()

    for i, cluster in enumerate(clusters):
        # Retrieve points in this cluster
        cluster_points = df[df['cluster'] == cluster]

        # Retrieve minimum and maximum coordinates identifying cluster region
        coord_min = (cluster_points['latitude'].min(), cluster_points['longitude'].min())
        coord_max = (cluster_points['latitude'].max(), cluster_points['longitude'].max())

        # Retrieve coordinates identifying the padded cluster region
        padded_coord_min, padded_coord_max = pad_region(coord_min, coord_max)
        padded_lat_min, padded_lng_min = padded_coord_min[0], padded_coord_min[1]
        padded_lat_max, padded_lng_max = padded_coord_max[0], padded_coord_max[1]

        # North-west origin point
        origin = (padded_lat_max, padded_lng_min)

        # Get distance metrics
        distances = haversine(padded_coord_min, padded_coord_max)
        d_lat = round(distances['lat'])
        d_lng = round(distances['lng'])

        print(f'Cluster {i}; Origin: {origin}; Lat Dist: {d_lat}; Long Dist: {d_lng}', flush=True)


        # Call APIs on every point separated by 32km
        api_data = {}
        for i in [BLOCK_SIZE * m for m in range(round(d_lat / BLOCK_SIZE)+1)]:
            for j in [BLOCK_SIZE * n for n in range(round(d_lng / BLOCK_SIZE)+1)]:
                coord = adjusted_coordinate(origin, -i, j)
                
                api_data[(j, i)] = {}

                # Populate dictionary with weather data
                get_weather_data(
                    coord, 
                    api_data[(j, i)]
                )

                # Populate dictionary with gee data
                get_gee_data(
                    coord, 
                    [padded_lng_min, padded_lat_min, padded_lng_max, padded_lat_max], 
                    api_data[(j, i)]
                )

        # Interpolate the API data
        interpolated_data = get_interpolated_data(api_data, d_lat, d_lng)

        # Something went wrong and an empty dictionary was returned
        # Proceed to next cluster
        if len(interpolated_data) == 0:
            continue

        # Assign the previous fire mask
        interpolated_data[Feature.PREV_MASK] = get_current_mask(d_lat, d_lng, origin, cluster_points)

        # clip and normalize data
        clipped_and_normalized = {
            key: (tf.clip_by_value(tf.convert_to_tensor(value, dtype=tf.float32), DATA_STATS[key][0], DATA_STATS[key][1]) - DATA_STATS[key][2]) / DATA_STATS[key][3]
            for key, value in interpolated_data.items()
        }

        if tf.reduce_any([tf.reduce_any(tf.math.is_nan(tensor)) for key, tensor in clipped_and_normalized.items()]):
            print('There was found to be a null. This cluster will not be evaluated', flush=True)
            continue


        # Generate 32x32km predicted fire masks
        predicted_masks = []
        for i in range(round(d_lat / BLOCK_SIZE)):
            for j in range(round(d_lng / BLOCK_SIZE)):
                num_features = len(clipped_and_normalized)
                blocks = np.zeros((BLOCK_SIZE, BLOCK_SIZE, num_features))

                # Transform into shape (1, BLOCK_SIZE, BLOCK_SIZE, NUM_FEATURES) for model
                for k, feature in enumerate([Feature.ELEVATION, Feature.WIND_DIRECTION, Feature.WIND_SPEED, Feature.TEMP_MIN, Feature.TEMP_MAX, Feature.HUMIDITY, Feature.PRECIPITATION, Feature.DROUGHT, Feature.VEGETATION, Feature.POPULATION, Feature.ERC, Feature.PREV_MASK]):
                    blocks[:, :, k] = clipped_and_normalized[feature][(i)*BLOCK_SIZE:(i+1)*BLOCK_SIZE, (j)*BLOCK_SIZE:(j+1)*BLOCK_SIZE]

                x = np.expand_dims(blocks, axis=0)
                y = model.predict(x)

                predicted_masks.append(y[0,:,:,0])

        # Combine masks
        interpolated_data[Feature.NEW_MASK] = np.stack(predicted_masks, axis=0).reshape(d_lat, d_lng)



        # Get coordinates identifying previous and predicted fire masks
        prev_mask_coords = get_mask_coords(interpolated_data[Feature.PREV_MASK], origin)
        pred_mask_coords = get_mask_coords(interpolated_data[Feature.NEW_MASK], origin, True)

        if len(prev_mask_coords) == 0 or len(pred_mask_coords) == 0:
            print(f'There were not enough coordinates to create a mask. Cluster will not be included.', flush=True)
            continue

        # Fire table
        fire_id = -1
        try:
            point = tuple(np.mean(np.array(prev_mask_coords), axis=0))

            fire_id = DataManager.execute_write_stored_procedure("add_fire", [point[0], point[1], generation_time])[0][0][0]
        except Exception as e:
            print('There was an issue adding a fire to the database', flush=True)
            raise

        # Region table
        try:
            DataManager.execute_write_stored_procedure(
                "add_region", 
                [
                    fire_id, 
                    run_id, 
                    padded_lat_min, 
                    padded_lng_min, 
                    padded_lat_max, 
                    padded_lng_max, 
                    np.mean(interpolated_data[Feature.WIND_DIRECTION]).item(), 
                    np.mean(interpolated_data[Feature.WIND_SPEED]).item(), 
                    np.mean(interpolated_data[Feature.TEMP_MIN]).item(), 
                    np.mean(interpolated_data[Feature.TEMP_MAX]).item(), 
                    np.mean(interpolated_data[Feature.HUMIDITY]).item(), 
                    np.mean(interpolated_data[Feature.PRECIPITATION]).item()
                ]
            )
        except Exception as e:
            print('There was an issue adding a region to the database', flush=True)
            raise
        
        # Process previous mask (& points)
        prev_mask_id = -1
        try:
            prev_mask_id = DataManager.execute_write_stored_procedure("add_mask", [1, fire_id, run_id])[0][0][0]
        except Exception as e:
            print('Issue saving previous fire mask to database.', flush=True)
            raise

        for i, coord in enumerate(prev_mask_coords):
            try:
                DataManager.execute_write_stored_procedure('add_mask_point', [prev_mask_id, i, coord[0], coord[1]])
            except Exception as e:
                print('Issue saving previous fire mask point to database.', flush=True)
                raise

        # Process predicted mask (& points)
        pred_mask_id = -1
        try:
            pred_mask_id = DataManager.execute_write_stored_procedure("add_mask", [2, fire_id, run_id])[0][0][0]
        except Exception as e:
            print('Issue saving predicted fire mask to database.', flush=True)
            raise

        for i, coord in enumerate(pred_mask_coords):
            try:
                DataManager.execute_write_stored_procedure('add_mask_point', [pred_mask_id, i, coord[0], coord[1]])
            except Exception as e:
                print('Issue saving predicted fire mask point to database.', flush=True)
                raise


def run(id: int):
    """
    Execute the retrieval process

    Args:
      id: Engine run identifier provided by the engine
    """

    if (id == -1):
        return
    
    run_id = id

    # Perform clustering
    df = get_clusters(f'{(generation_time - timedelta(days=0)).strftime("%Y-%m-%d")}')

    print(f'Found {len(df)} clusters...', flush=True)

    # Perform clustering with latest data from yesterday if there is no present day data
    if len(df) == 0:
        df = get_clusters(f'{(generation_time - timedelta(days=1)).strftime("%Y-%m-%d")}')

    start = datetime.now()

    # Process clusters
    process_clusters(id, df)

    end = datetime.now()

    print(f'Cluster processing complete in {(end-start).total_seconds()} seconds.', flush=True)
