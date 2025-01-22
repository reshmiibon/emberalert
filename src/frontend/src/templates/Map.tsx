import {
  GoogleMap,
  InfoWindowF,
  MarkerF,
  PolygonF,
  useLoadScript,
} from '@react-google-maps/api';

import { useCallback, useState, useEffect } from 'react';

const API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string;
const MAP_BOUNDS = {
  north: 74.3475,
  south: 12.5606,
  west: -170.0927,
  east: -51.4404,
}

const containerStyle = { width: '99vw', height: '100vh' };
const defaultCenter = { lat: 39.8283, lng: -98.5795 };
const defaultZoom = 5;

// Visual-related options for fire masks
const trueOptions = {
  strokeColor: '#FF0000',
  strokeOpacity: 0.6,
  strokeWeight: 2,
  fillColor: '#FF0000',
  fillOpacity: 0.35,
  zIndex: 1000,
};
const predictedOptions = {
  strokeColor: '#FFFF00',
  strokeOpacity: 0.6,
  strokeWeight: 2,
  fillColor: '#FFFF00',
  fillOpacity: 0.35,
  zIndex: 1,
};

const libraries = ["places"];
const Map = () => {
  const [map, setMap] = useState(null);
  const [fires, setFires] = useState([]);
  const [activeMarker, setActiveMarker] = useState(null);
  const [regionData, setRegionData] = useState(null);

  const { isLoaded } = useLoadScript({
    googleMapsApiKey: API_KEY,
    libraries: libraries, // Add google places library for maps search bar 
  });

  // Fetch fire data from the backend, get fire ID and middle point
  useEffect(() => {
    (async () => {
      try {
        // Make an HTTP request to fetch fire data from backend API
        const response = await fetch('/api/map/get-fires'); 
        const data = await response.json();
        console.log('Fetched fire data:', data); // Log the fetched data
        
        // Save data from response
        setFires(data);
 
      } catch (error) {
        console.error('Error fetching fire data:', error);
      }
    })();
  }, []);

  const handleActiveMarker = async (fire_id, position) => {
    // Set the active marker ID when a marker is clicked
    setActiveMarker(fire_id);

    // Make an API request to fetch fire mask for the given fire_id
    fetch(`/api/map/get-fire-mask/${fire_id}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {

        // Handle the response data
        console.log('Fire mask data:', data);
        
        try {
          // Adjust map bounds based on the fire ID
          adjustMapBounds(fire_id, position);
        } catch (error) {
          console.error('Error adjusting map bounds:', error);
        }

        renderPolygons(data);
      })
      
      .catch(error => {
        console.error('Error fetching fire mask:', error);
      });
  };
  const adjustMapBounds = async (fireId, position) => {
    try {
      // Make a request to fetch the min and max coordinates for the given fire ID
      const response = await fetch(`/api/map/get-min-max/${fireId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch fire bounds data');
      }

      const data = await response.json();
      if (data.length > 0) {
        // If min and max coordinates are received, adjust the map bounds accordingly
        const bounds = new window.google.maps.LatLngBounds();
        data.forEach(point => {
          const latLng = new window.google.maps.LatLng(point.lat, point.lng);
          bounds.extend(latLng);
        });
  
        // Add padding to the map bounds 
        const padding = 5; 
        map.fitBounds(bounds, padding);
  
        const center = new google.maps.LatLng(position.lat, position.lng);
        map.setCenter(center);
      } else {
        throw new Error('Invalid fire bounds data received');
      }
    } catch (error) {
      console.error('Error fetching or processing fire bounds data:', error);
    }
  };

  const handleLegend = () => {
    // Legend configuration
    var leg = document.getElementById('legend');
    leg!.innerHTML = '';

    var heading = document.createElement('h3');
    heading.className = 'font-bold text-lg mb-2';
    heading.innerHTML = 'Legend';
    leg?.appendChild(heading);

    const entry = ((props: any) => {
      var div = document.createElement('div');
      div.className = 'flex justify-between items-center text-base';

      var img = document.createElement('img');
      img.className = 'm-2';
      img.src = props.imageSource;
      div.appendChild(img);

      var p = document.createElement('p');
      p.innerHTML = props.iconName;
      div.appendChild(p);

      return div;
    });

    var div = document.createElement('div');

    div.appendChild(entry({ imageSource: '/fire.png', iconName: 'Wildfire' }));
    div.appendChild(entry({ imageSource: '/trueMask.png', iconName: 'True' }));
    div.appendChild(entry({ imageSource: '/predMask.png', iconName: 'Predicted' }));

    leg?.appendChild(div);
  };

  // Initialize an array to store existing polygons
  let existingPolygons = [];
 
 // Drawing mask for fire that was clicked on (both predicted and active)
  const renderPolygons = (fireMaskData) => {
    // Check if fire mask data is available
    if (!fireMaskData || fireMaskData.length === 0) {
      //console.log('No fire mask data available');
      return;
    }

    // Loop through each fire mask
    fireMaskData.forEach(mask => {
      const { mask_id, points } = mask;
      if (!points || points.length === 0) {
        //console.log(`No points available for mask ${mask_id}`);
        return;
      }

      // Extract active and predicted points
      const activePoints = points.filter(point => {
        return point.fire_status === 'ACTIVE';
      });
      const predictedPoints = points.filter(point => {
        return point.fire_status === 'PREDICTION';
      });

      // Add the mask ID to the set of drawn mask IDs
    
      //console.log(`Mask ${mask_id}: Active Points`, activePoints);
      //console.log(`Mask ${mask_id}: Predicted Points`, predictedPoints);

      // Render polygons for active points
      if (activePoints.length > 0) {
        const activePolygon = new google.maps.Polygon({
          paths: activePoints.map(point => ({
            lat: parseFloat(point.latitude),
            lng: parseFloat(point.longitude)
          })),
          ...trueOptions,
          map: map
        });

        existingPolygons.push(activePolygon)
      }

      // Render polygons for predicted points
      if (predictedPoints.length > 0) {
        const predictedPolygon = new google.maps.Polygon({
          paths: predictedPoints.map(point => ({
            lat: parseFloat(point.latitude),
            lng: parseFloat(point.longitude)
          })), 
          ...predictedOptions, 
          map: map
        });

        existingPolygons.push(predictedPolygon)
      }

    });
  };

  const fetchRegionData = async (fire_id) => {
    try {
      const response = await fetch(`/api/map/get-region-data/${fire_id}`);
      if (response.ok) {
        const data = await response.json();
        console.log('Fetched region data:', data); 
        setRegionData(data);
        console.log('Region data set:', data); 
      } else {
        console.error('Failed to fetch region data:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching region data:', error);
    }
  };

  const renderInfoWindowContent = (regionData) => {
    if (!regionData) {
      return <div>Loading...</div>;
    }

    const data = regionData[0]; 
    const minTempCelsius = (data.min_temp - 273.15).toFixed(2); // Convert min temp to Celsius
    const maxTempCelsius = (data.max_temp - 273.15).toFixed(2); // Convert max temp to Celsius
    const getWindDirection = (degrees) => {
      const directions = ['North', 'North-East', 'East', 'South-East', 'South', 'South-West', 'West', 'North-West'];
      const index = Math.round(degrees / 45) % 8;
      return directions[index];
    };
    return (
      <div>
        <p className="font-bold text-lg mb-2">Region Data</p>
        <ul>
          <li>
            <strong>Generation Date:</strong> {new Date(data.generation_date).toLocaleString()}<br />
            <strong>Wind:</strong> {data.wind_speed} meter/sec {getWindDirection(data.wind_direction)}<br />
            <strong>Min Temp:</strong> {minTempCelsius} °C<br />
            <strong>Max Temp:</strong> {maxTempCelsius} °C<br />
            <strong>Humidity:</strong> {data.humidity} %<br />
            <strong>Precipitation:</strong> {data.precipitation} mm<br />
          </li>
        </ul>
      </div>
    );
  };

  // Related to wildfire locations
  // <a href="https://www.flaticon.com/free-icons/fire" title="fire icons">Fire icons created by Vectors Market - Flaticon</a>
  const renderMarkers = () => {
    if (!fires || fires.length === 0) {
      return null; // Return early if fires data is not available or empty
    }
  
    return fires.map((fire, i) => {
      if (!fire || !fire.lat || !fire.lng) {
        console.log('Invalid fire data:', fire);
        console.log('Invalid fire data:', fire.lng);
        console.log('Invalid fire data:', fire.lat);
        return null; // Skip rendering if fire data is not available
      }
  
      const position = { lat: fire.lat, lng: fire.lng };
  
      return (
        <MarkerF
          key={fire.id}
          position={position}
          icon={{
            url: '/fire.png',
            //scaledSize: new window.google.maps.Size(25, 25), // Adjust the size as needed
        }}
        onClick={() => {
          handleActiveMarker(fire.id, position);
          fetchRegionData(fire.id);
        }}
        >
          {activeMarker === fire.id && 
            <>
              <InfoWindowF position={position}>
                {renderInfoWindowContent(regionData)}
              </InfoWindowF>
              {renderPolygons(fire.masks)}
            </>
          }
        </MarkerF>
      );
    });
  };

  const onLoad = useCallback(function callback(m: any) {
    const bounds = new window.google.maps.LatLngBounds();
    bounds.extend(new window.google.maps.LatLng(defaultCenter.lat, defaultCenter.lng));
    m.setCenter(defaultCenter); // Set the map center to the default center
    m.setZoom(defaultZoom); // Set the map zoom to the default zoom level

    // Setup the legend
    handleLegend();
    m.controls[google.maps.ControlPosition.RIGHT_CENTER].push(document.getElementById('legend'));

    // Start of code for search box
    const input = document.getElementById('searchbox-input') as HTMLInputElement;
    const searchBox = new google.maps.places.SearchBox(input);
    m.controls[google.maps.ControlPosition.TOP_CENTER].push(input);

    searchBox.addListener('places_changed', () => {
      const places = searchBox.getPlaces();
      if (places?.length === 0) {
        return;
      }
      // For each place, get the icon, name, and location.
      const bounds = new google.maps.LatLngBounds();
      places?.forEach((place) => {
        if (!place.geometry || !place.geometry.location) {
          console.log("Returned place contains no geometry");
          return;
        }
        if (place.geometry.viewport) {
          // Only geocodes have viewport.
          bounds.union(place.geometry.viewport);
        } else {
          bounds.extend(place.geometry.location);
        }
      });
      m.fitBounds(bounds);
      m.setZoom(9); // Set the map zoom to the default zoom level
    });
    //end of search bar code
    setMap(m);
  }, []);

  const onUnmount = useCallback(function callback() {
    setMap(null);
  }, []);

  const handleDebugDetails = (e : google.maps.MapMouseEvent) => {
    if (e !== undefined) {
      console.log(e.latLng?.lat());
      console.log(e.latLng?.lng());
    }
  };

  return isLoaded ? (
    <>
    <div id="search-box" style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)', zIndex: 10, width: '50%', marginTop: '10px' }}>
      <input
        id="searchbox-input" 
        className="controls"
        type="text"
        placeholder="Enter Address"
        style={{ width: '50%', padding: '5px', top: '15px', fontFamily: 'Roboto', fontSize: '15px', fontWeight: '300' , border: '1px solid black', margin: '10px' }}
      />
    </div>
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={defaultCenter}
      zoom={defaultZoom}
      onLoad={onLoad}
      onUnmount={onUnmount}
      onClick={(e) => handleDebugDetails(e)}
      options={{
        restriction: {
          latLngBounds: MAP_BOUNDS,
          strictBounds: false,
        }
      }}
    >
      {renderMarkers()}
    </GoogleMap>
    </>
  ) : (
    <></>
  );
};

export default Map;
