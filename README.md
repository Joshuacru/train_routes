# Train Route Calculator

Command line tool for calculating the shortest route between two stations.

### Usage

Invoke with ```python3 main.py --file=test_routes_1.csv```

Where routes.csv points to a csv file defining one route on each line in the following format _originName,destinationName,distance_.
Routes go only in one direction and separate routes must be defined to allow return trips along the same path.

### Testing

Run unit tests with ```python3 -m unittest discover```
