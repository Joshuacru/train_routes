from __future__ import annotations
import argparse
import csv
import sys
import math
from heapq import heappush, heappop
from typing import Tuple


class DuplicateRouteError(Exception):
    pass


class RouteParsingError(Exception):
    def __init__(self, message: str, line: int = None):
        preface = "Route parsing failed"
        if line:
            self.message = f"{preface} on line {line}: {message}"
        else:
            self.message = f"{preface}: {message}"
        super().__init__(self.message)


class StationDoesNotExistError(Exception):
    def __init__(self, station_name: str):
        self.message = f"Station: '{station_name}' does not exist."
        super().__init__(self.message)


class StationMap:
    """Holds complete station map and calculates the shortest route."""

    def __init__(self):
        self.stations: dict[str, Station] = {}

    def _add_station(self, station_name: str):
        if station_name not in self.stations:
            self.stations[station_name] = Station(station_name)

    def add_route(self, origin_name: str, destination_name: str, distance: int):
        """Adds a new route to the station map and adds new stations as necessary."""
        self._add_station(origin_name)
        self._add_station(destination_name)
        self.stations[origin_name].add_route(self.stations[destination_name], distance)

    @staticmethod
    def _count_stops(
        destination: Station, origin: Station, previous_stations: dict[Station, Station]
    ) -> int:
        # follow the path backwords and count the number of stops.
        stops = 0
        while previous_stations[destination] != origin:
            destination = previous_stations[destination]
            stops += 1
        return stops

    def find_shortest_route(
        self, origin_name: str, destination_name: str
    ) -> Tuple[int | float, int | None]:
        """Finds the shortest route between two stations.

        Uses modified Dijkstra's algorithm to support stations that are not connected.

        Args:
            origin: Name of origin station.
            destination: Name of destination station.

        Returns:
            A tuple representing the total distance of the shortest path and the total number of stops along the path.

            Total distance is infinite (math.inf) of no path exists.

        """

        if origin_name not in self.stations:
            raise StationDoesNotExistError(origin_name)
        if destination_name not in self.stations:
            raise StationDoesNotExistError(destination_name)

        if origin_name == destination_name:
            return 0, 0

        origin = self.stations[origin_name]
        destination = self.stations[destination_name]

        unvisited_stations: list[Tuple[int | float, Station]] = []
        visited: set[
            Station
        ] = set()  # we have to track this separately in order to support unconnected
        # stations which is also why we cant add all stations to unvisited stations at the start.
        dist: dict[Station, int | float] = {}
        prev: dict[Station, Station] = {}

        for station in self.stations.values():
            if station == origin:
                dist[station] = 0
            else:
                # Unvisited stations start with infinite distance.
                dist[station] = math.inf

        heappush(
            unvisited_stations, (0, origin)
        )  # start at the origin station with distance 0

        while len(unvisited_stations) > 0:
            current_station = heappop(unvisited_stations)[
                1
            ]  # pop off the nearest unvisited station

            if current_station == destination:
                return dist[current_station], self._count_stops(
                    current_station, origin, prev
                )

            for connected_station in current_station.routes:
                if connected_station not in visited:
                    route_total = (
                        dist[current_station]
                        + current_station.routes[connected_station]
                    )  # calculate the total distance of this route from the origin.
                    if route_total < dist[connected_station]:
                        dist[connected_station] = route_total
                        prev[connected_station] = current_station
                        heappush(unvisited_stations, (route_total, connected_station))

            visited.add(current_station)

        return math.inf, None  # no route


class Station:
    """A Train station and its connected routes."""

    def __init__(self, name: str):
        self.name: str = name
        self.routes: dict[Station, int] = {}

    def add_route(self, destination: Station, distance: int):
        """Adds a new route between this station and another.

        Raises:
            DuplicateRouteError: Only one route for each direction between stations is allowed.
        """
        if destination in self.routes:
            raise DuplicateRouteError(
                f"Route from {self.name} to {destination.name} already exists."
            )

        self.routes[destination] = distance

    def __gt__(self, *args) -> bool:
        # this method is required by heappush as a tie breaker when distances are equal.
        return False

    def __repr__(self) -> str:
        return f"{{Station: {self.name}}}"


def parse_routes(path: str) -> StationMap:
    """Parse route definition file.

    Reads a csv file at provided path containing a list of train routes and creates a StationMap.

    Each line of the input file should have the following format:
        origin_name, destination_name, distance

    """

    station_map = StationMap()

    try:
        with open(path) as csvfile:
            reader = csv.DictReader(
                csvfile, fieldnames=["origin", "destination", "distance"]
            )

            for row in reader:
                try:
                    distance = int(row["distance"])
                except TypeError:
                    raise RouteParsingError(
                        f"Invalid route format. Expected format: origin_name, destination_name, distance.",
                        reader.line_num,
                    )
                except ValueError:
                    raise RouteParsingError(
                        f"'{row['distance']}' is not an integer", reader.line_num
                    )

                try:
                    station_map.add_route(row["origin"], row["destination"], distance)
                except DuplicateRouteError as e:
                    raise RouteParsingError(
                        f"Route parsing failed: {e}", reader.line_num
                    )
    except OSError as e:
        raise RouteParsingError(f"Unable to open route file: {e}")

    if len(station_map.stations) == 0:
        RouteParsingError("Input file has no route definitions.")

    return station_map


def parse_arguments(arguments: list[str]) -> str:
    """Parses command line arguments.

    The code challenge specification requires that the input file be provided via keyword argument
    which makes argparse list it as optional in the help text when its actually required.
    """

    parser = argparse.ArgumentParser(
        description="Tool for finding the shortest train route between two stations."
    )
    parser.add_argument(
        "--file",
        help="Path to csv file containing a list of train routes in the following format: origin_name,destination_name,distance.",
    )

    args = parser.parse_args(arguments)
    return args.file


def main():
    route_file_path = parse_arguments(sys.argv[1:])

    if not route_file_path:
        print("You must specify an input file.")
        exit()

    try:
        station_map = parse_routes(route_file_path)
    except RouteParsingError as e:
        print(e)
        exit()

    origin = input("What station are you getting on the train?: ")
    destination = input("What station are you getting off the train?: ")

    try:
        distance, stops = station_map.find_shortest_route(origin, destination)
    except StationDoesNotExistError as e:
        print(e)
        print("Valid station names are: " + ", ".join(station_map.stations))
        exit()

    if distance == math.inf:
        print(f"\nThere are no routes from {origin} to {destination}.")
    else:
        stop = "stops"
        if stops == 1:
            stop = "stop"

        print(
            f"\nYour trip from {origin} to {destination} includes {stops} {stop} and will take {distance} minutes."
        )


if __name__ == "__main__":
    main()
