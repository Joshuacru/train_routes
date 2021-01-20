from unittest import TestCase
import math
from main import parse_routes, StationDoesNotExistError, RouteParsingError


class TestParseRoutes(TestCase):
    def test_can_parse_valid_input_file(self):
        station_map = parse_routes("test_routes_1.csv")
        self.assertEqual(len(station_map.stations), 10)
        self.assertEqual(len(station_map.stations["A"].routes), 2)

    def test_cannot_read_input_file(self):
        with self.assertRaises(RouteParsingError) as context:
            parse_routes("this_file_does_not_exist.csv")
        self.assertTrue("Unable to open" in context.exception.message)

    def test_cannot_parse_distance(self):
        with self.assertRaises(RouteParsingError) as context:
            parse_routes("test_routes_bad_distance.csv")
        self.assertTrue("not an integer" in context.exception.message)

    def test_invalid_format(self):
        with self.assertRaises(RouteParsingError) as context:
            parse_routes("test_routes_invalid.csv")
        self.assertTrue("Invalid route format" in context.exception.message)

    def test_duplicate_route(self):
        with self.assertRaises(RouteParsingError) as context:
            parse_routes("test_routes_duplicate_route.csv")
        self.assertTrue("already exists" in context.exception.message)


class TestStationMap(TestCase):
    def setUp(self):
        self.station_map = parse_routes("test_routes_1.csv")

    def test_stops_counted_correctly(self):
        distance, stops = self.station_map.find_shortest_route("A", "B")
        self.assertEqual(stops, 0)
        distance, stops = self.station_map.find_shortest_route("A", "C")
        self.assertEqual(stops, 1)

    def test_shortest_route_always_used(self):
        distance, stops = self.station_map.find_shortest_route("A", "D")
        self.assertEqual(distance, 15)
        self.assertEqual(stops, 0)

        distance, stops = self.station_map.find_shortest_route("F", "J")
        self.assertEqual(distance, 25)
        self.assertEqual(stops, 1)

    def test_no_path_to_destination(self):
        distance, stops = self.station_map.find_shortest_route("A", "F")
        self.assertEqual(distance, math.inf)
        self.assertIsNone(stops)

    def test_station_does_not_exist(self):
        with self.assertRaises(StationDoesNotExistError):
            self.assertRaises(
                StationDoesNotExistError, self.station_map.find_shortest_route("A", "Z")
            )

        with self.assertRaises(StationDoesNotExistError):
            self.assertRaises(
                StationDoesNotExistError, self.station_map.find_shortest_route("Y", "B")
            )

    def test_origin_same_as_destination(self):
        distance, stops = self.station_map.find_shortest_route("A", "A")
        self.assertEqual(distance, 0)
        self.assertEqual(stops, 0)
