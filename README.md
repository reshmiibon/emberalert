## EmberAlert
## GROUP 13
- Reshmii Bondili
- Kyle Carnrite
- Jerica Dias
- Andy Le
- Travis Moore
- Komal Naeem

## Description
The purpose of this system is to help revolutionize wildfire management by predicting wildfire progressions and
providing timely alerts to those in at-risk areas. This project arose from Canada and America’s escalating frequency
and intensity of wildfires where relying on locals to report wildfires results in delayed awareness, missed evacuation
opportunities, and lost lives.

By integrating geospatial data, current weather metrics, and satellite-derived imagery, the goal is to develop a
comprehensive model that can predict wildfire progressions. Through a web application, the aim is to offer residents
and first responders a clear visualization forecast of anticipated wildfire spreads, complimented by a notification
system for prompt alerts. With this project, the hope is to work towards a future where communities are better
informed, prepared, and protected against the unpredictable nature of wildfires

## Prerequisites:
- [Docker](https://docs.docker.com/get-docker/) 
- [gcloud cli](https://cloud.google.com/sdk/docs/install)
- [node](https://nodejs.org/en)
- A key for:
    - Twillio
    - Google Maps Platform
    - FIRMS
    - OpenWeather Map API
- A Google Cloud Project


## Installation / Running instructions
- Pull the repo
- Create a file in ./src/backend/ called `constants.py`, in this file you will need to provide the following keys:
```
# COMMENT / UNCOMMENT DEPENDING ON WHERE YOU'RE WORKING / TESTING FROM. Docker container = database, local = localhost
#DATABASE_HOST_NAME = 'localhost'
DATABASE_HOST_NAME = 'database'


FIRMS_API_KEY = 'FIRMS_API_KEY'

OPENWEATHERMAP_API_KEY = 'OPEN_WEATHER_MAP_API_KEY'

EE_PROJECT_NAME = 'EE_PROJECT_NAME'

TWILLIO_ACCOUNT_SID = 'YOUR_ACCOUNT_SID'
TWILLIO_ACCOUNT_AUTH_TOKEN = 'YOUR ACCOUNT AUTH TOKEN'
```
- Create a file in ./src/frontend called `.env` with the following keys:
```
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = 'YOUR_KEY'
```
- Setup your gcloud authentication file by running ``gcloud auth application-default login``
- Navigate to ``src/`` and run ``docker compose up -d``
- Navigate to ``src/frontend`` and run ``npm install``. Then run ``npm run dev``.

When you are finished using the app:
- Press ``Ctrl+C`` to stop the terminal and run ``docker compose down``


## License
MIT License

Copyright (c) 2024 Capstone Group 13 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.