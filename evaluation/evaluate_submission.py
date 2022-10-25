import os
import csv
import json
import glob
import datetime
import argparse
import warnings

warnings.filterwarnings("ignore")

import numpy as np

from math import sqrt
from collections import defaultdict

from sklearn import metrics

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from shapely.ops import unary_union, cascaded_union

import geopandas as gpd

import geopy
import geopy.distance

import folium

_CACHE = {}
_FISH_ZONE_CLASS_MAPPING = {"Not available": 0}
_FAO_ZONE_CLASS_MAPPING = {"Not available": 0}

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input-path", type=str, default="../submissions")
parser.add_argument("-g", "--ground-truth-path", type=str, default="../data/gt.csv")
parser.add_argument("-f", "--fishing-zone-info-path", type=str, default="../data/zones.json")
parser.add_argument("-o", "--output-dir", type=str, default="../output")

def convert_date(datestr):
    return datetime.datetime.strptime(datestr, "%d%m%Y")

def measure_distance_between_points(lonlat1, lonlan2):
    return geopy.distance.geodesic(lonlat1, lonlan2).km

def read_json(path):
    if path not in _CACHE:
        with open(path, "r") as f:
            _CACHE[path] = json.load(f)
    return _CACHE[path]

def read_csv(path, delimiter=";", types=[convert_date, str, float, float]):
    if path in _CACHE:
        return _CACHE[path]
    data = []
    with open(path, "r") as f:
        csv_reader = csv.reader(f, delimiter=delimiter)
        header = next(csv_reader)
        assert len(header) == len(types)
        for line in csv_reader:
            new_line = []
            for val, typecast in zip(line, types):
                new_line.append(typecast(val.strip()))
            data.append(new_line)
    return data

def read_submission_csv_with_fishing_zones(catch_info_path, fishing_zone_path, scale_zones=1.0):

    print("[INFO]\tReading %s" % catch_info_path)

    fishing_zones = read_json(fishing_zone_path)
    catch_data = read_csv(catch_info_path)

    fishing_zone_polygons = {}
    fao_zone_polygons = {}
    
    fao_zone_mapping = defaultdict(list)
    data = defaultdict(dict)

    for fishing_zone_name, fishing_zone_info in fishing_zones.items():

        latitude_list = []
        longitude_list = []

        fishing_zone_fao_location = fishing_zone_info["FAOArea"]

        if fishing_zone_name not in _FISH_ZONE_CLASS_MAPPING:
            _FISH_ZONE_CLASS_MAPPING[fishing_zone_name] = len(_FISH_ZONE_CLASS_MAPPING)

        if fishing_zone_fao_location not in _FAO_ZONE_CLASS_MAPPING:
            _FAO_ZONE_CLASS_MAPPING[fishing_zone_fao_location] = len(_FAO_ZONE_CLASS_MAPPING)

        for coords in fishing_zone_info["Coordinates"]:
            latitude_list.append(coords["Latitude"])
            longitude_list.append(coords["Longitude"])

        fishing_zone_polygon_geom = Polygon(zip(longitude_list, latitude_list))
        fishing_zone_polygon = gpd.GeoDataFrame(index=[0], crs="epsg:4326", geometry=[fishing_zone_polygon_geom])

        fishing_zone_polygon = fishing_zone_polygon.scale(xfact=scale_zones,
            yfact=scale_zones, zfact=scale_zones, origin='center')

        fishing_zone_polygons[fishing_zone_name] = fishing_zone_polygon
        fao_zone_mapping[fishing_zone_fao_location].append(fishing_zone_polygon_geom)

    for fao_zone_name, list_of_polygons in fao_zone_mapping.items():
        fao_zone_polygons[fao_zone_name] = gpd.GeoSeries(unary_union(list_of_polygons), crs="epsg:4326")

    for catch_info_line in catch_data:

        catch_date = catch_info_line[0]
        catch_fish_type = catch_info_line[1]
        catch_longitude = catch_info_line[2]
        catch_latitude = catch_info_line[3]
        catch_location = "Not available"
        catch_fao_location = "Not available"
        
        point = Point(catch_longitude, catch_latitude)
        
        for fishing_zone_name, fishing_zone_polygon in fishing_zone_polygons.items():
            if fishing_zone_polygon.contains(point)[0]:
                catch_location = fishing_zone_name

        for fao_zone_name, fao_polygon in fao_zone_polygons.items():
            if fao_polygon.contains(point)[0]:
                catch_fao_location = fao_zone_name

        data[catch_date][catch_fish_type] = {
            "longitude": catch_longitude,
            "latitude": catch_latitude,
            "location": catch_location,
            "fao_zone": catch_fao_location
        }

    return data

def create_fishing_zone_map(fishing_zone_path, starting_coordinates=[50.854457, 4.377184], zoom_start=5):

    fishing_zones = read_json(fishing_zone_path)
    
    fishing_zone_map = folium.Map(starting_coordinates, zoom_start=zoom_start, tiles="cartodbpositron")
    
    for _, fishing_zone_info in fishing_zones.items():

        latitude_list = []
        longitude_list = []

        for coords in fishing_zone_info["Coordinates"]:
            latitude_list.append(coords["Latitude"])
            longitude_list.append(coords["Longitude"])

        polygon_geom = Polygon(zip(longitude_list, latitude_list))
        polygon = gpd.GeoDataFrame(index=[0], crs="epsg:4326", geometry=[polygon_geom])       

        polygon.to_file(filename="polygon.geojson", driver="GeoJSON")
        polygon.to_file(filename="polygon.shp", driver="ESRI Shapefile")

        folium.GeoJson(polygon).add_to(fishing_zone_map)
        folium.LatLngPopup().add_to(fishing_zone_map)

    return fishing_zone_map

def create_fao_map(fishing_zone_path, starting_coordinates=[50.854457, 4.377184], zoom_start=5):

    fishing_zones = read_json(fishing_zone_path)
    
    fao_zone_map = folium.Map(starting_coordinates, zoom_start=zoom_start, tiles="cartodbpositron")
    fao_zone_mapping = defaultdict(list)

    for _, fishing_zone_info in fishing_zones.items():

        latitude_list = []
        longitude_list = []

        for coords in fishing_zone_info["Coordinates"]:
            latitude_list.append(coords["Latitude"])
            longitude_list.append(coords["Longitude"])

        polygon_geom = Polygon(zip(longitude_list, latitude_list))
        fao_zone_mapping[fishing_zone_info["FAOArea"]].append(polygon_geom)

    for fao, list_of_polygons in fao_zone_mapping.items():
        fao_polygon = gpd.GeoSeries(unary_union(list_of_polygons), crs="epsg:4326")

        fao_polygon.to_file(filename="polygon.geojson", driver="GeoJSON")
        fao_polygon.to_file(filename="polygon.shp", driver="ESRI Shapefile")

        folium.GeoJson(fao_polygon).add_to(fao_zone_map)
        folium.LatLngPopup().add_to(fao_zone_map)

    return fao_zone_map

def calculate_classification_metrics(y_true, y_pred):
    assert len(y_true) == len(y_pred)
    if len(y_true) == 0 or len(y_pred) == 0:
        return {}
    return {
        "recall_micro": metrics.recall_score(y_true, y_pred, average="micro"),
        "recall_macro": metrics.recall_score(y_true, y_pred, average="macro"),
        "precision_micro": metrics.precision_score(y_true, y_pred, average="micro"),
        "precision_macro": metrics.precision_score(y_true, y_pred, average="macro"),
        "f1_micro": metrics.f1_score(y_true, y_pred, average="micro"),
        "f1_macro": metrics.f1_score(y_true, y_pred, average="macro"),
        "matthews_correlation_coefficient": metrics.matthews_corrcoef(y_true, y_pred)
    }

def calculate_regression_metrics(y_true, y_pred):
    assert len(y_true) == len(y_pred)
    if len(y_true) == 0 or len(y_pred) == 0:
        return {}
    return { 
        "mean_squared_error": metrics.mean_squared_error(y_true, y_pred),
        "raw_mean_squared_error": list(metrics.mean_squared_error(y_true, y_pred, multioutput="raw_values")),
        "mean_root_squared_error": sqrt(metrics.mean_squared_error(y_true, y_pred)),
        "raw_mean_root_squared_error": list([sqrt(val) for val in metrics.mean_squared_error(y_true, y_pred, multioutput="raw_values")]),
        "mean_absolute_error": metrics.mean_absolute_error(y_true, y_pred),
        "raw_mean_absolute_error": list(metrics.mean_absolute_error(y_true, y_pred, multioutput="raw_values")),
        "mean_absolute_percentage_error": metrics.mean_absolute_percentage_error(y_true, y_pred),
        "raw_mean_absolute_percentage_error": list(metrics.mean_absolute_percentage_error(y_true, y_pred, multioutput="raw_values")),
    }

if __name__ == "__main__":

    args = parser.parse_args()

    ground_truth = read_submission_csv_with_fishing_zones(
            args.ground_truth_path, args.fishing_zone_info_path)

    submission_paths = []

    if os.path.isdir(args.input_path):
        for path in glob.glob(os.path.join(args.input_path, "*.csv")):
            submission_paths.append(path)
    else:
        submission_paths.append(args.input_path)
    
    for submission_path in submission_paths:
        
        print("[INFO]\tEvaluating %s..." % submission_path)
        
        team_name = os.path.basename(submission_path).split("_")[0]
        team_predictions = read_submission_csv_with_fishing_zones(
                submission_path, args.fishing_zone_info_path)
        
        team_evaluation = {}

        submission_output_dir = os.path.join(args.output_dir, team_name)

        if not os.path.exists(submission_output_dir):
            os.makedirs(submission_output_dir)

        total_y_pred_coordinates = []
        total_y_true_coordinates = []

        total_y_true_fishing_zone = []
        total_y_pred_fishing_zone = []

        total_y_true_fao_zone = []
        total_y_pred_fao_zone = []

        total_distance = []
        
        for true_catch_date, true_catch_info in ground_truth.items():

            daily_y_pred_coordinates = []
            daily_y_true_coordinates = []

            daily_y_true_fishing_zone = []
            daily_y_pred_fishing_zone = []

            daily_y_true_fao_zone = []
            daily_y_pred_fao_zone = []

            daily_distance = []

            daily_detailed = {}
            
            date_str = true_catch_date.strftime("%d-%m-%Y")

            if true_catch_date not in team_predictions:
                print("[WARN]\tFound no predictions for %s..." % date_str)
                continue
            
            pred_catch_info = team_predictions[true_catch_date]

            submission_map = create_fishing_zone_map(args.fishing_zone_info_path)
            submission_fao_map = create_fao_map(args.fishing_zone_info_path)
            
            for true_catch_fish_type, true_catch_coordinates in true_catch_info.items():

                if true_catch_fish_type not in pred_catch_info:
                    print("[WARN]\tFound no predictions for %s on %s..." % (true_catch_fish_type, date_str))
                    continue

                pred_catch_coordinates = pred_catch_info[true_catch_fish_type]

                # Fish Zone Classification
                fishing_zone_true = true_catch_coordinates["location"]
                fishing_zone_pred = pred_catch_coordinates["location"] \
                    if "location" in pred_catch_coordinates else "Not available"

                true_fish_zone = _FISH_ZONE_CLASS_MAPPING[fishing_zone_true]
                pred_fish_zone = _FISH_ZONE_CLASS_MAPPING[fishing_zone_pred]

                daily_y_true_fishing_zone.append(true_fish_zone)
                daily_y_pred_fishing_zone.append(pred_fish_zone)
                
                # FAO Zone Classification
                fao_zone_true = true_catch_coordinates["fao_zone"]
                fao_zone_pred = pred_catch_coordinates["fao_zone"] \
                    if "fao_zone" in pred_catch_coordinates else "Not available"

                true_fao_zone = _FAO_ZONE_CLASS_MAPPING[fao_zone_true]
                pred_fao_zone = _FAO_ZONE_CLASS_MAPPING[fao_zone_pred]

                daily_y_true_fao_zone.append(true_fao_zone)
                daily_y_pred_fao_zone.append(pred_fao_zone)

                # Lat Lon Regression
                true_longitude = true_catch_coordinates["longitude"]
                true_latitude = true_catch_coordinates["latitude"]
                pred_longitude = pred_catch_coordinates["longitude"]
                pred_latitude = pred_catch_coordinates["latitude"]
                
                daily_y_pred_coordinates.append([true_longitude, true_latitude])
                daily_y_true_coordinates.append([pred_longitude, pred_latitude])

                try:

                    distance_true_pred = measure_distance_between_points(
                        (true_longitude, true_latitude),
                        (pred_longitude, pred_latitude))

                    daily_distance.append(distance_true_pred)

                    daily_detailed[true_catch_fish_type] = {
                        "true_coordinates": {"longitude": true_longitude, "latitude": true_latitude},
                        "true_fish_zone": true_fish_zone,
                        "predicted_coordinates": {"longitude": pred_longitude, "latitude": pred_latitude},
                        "predicted_fish_zone": pred_fish_zone,
                        "predicted_fao_zone": pred_fao_zone,
                        "prediction_distance_from_true_km": distance_true_pred
                    }

                    fish_zone_true_popup_text = "Fish: %s Fishing Zone: %s FAO Zone: %s" % (true_catch_fish_type, fishing_zone_true, fao_zone_true)
                    fish_zone_pred_popup_text = "Fish: %s Fishing Zone: %s FAO Zone: %s" % (true_catch_fish_type, fishing_zone_pred, fao_zone_pred)

                    fao_zone_true_popup_text = "Fish: %s Fishing Zone: %s FAO Zone: %s" % (true_catch_fish_type, fishing_zone_true, fao_zone_true)
                    fao_zone_pred_popup_text = "Fish: %s Fishing Zone: %s FAO Zone: %s" % (true_catch_fish_type, fishing_zone_pred, fao_zone_pred)

                    folium.Marker(location=[true_latitude, true_longitude],
                        icon=folium.Icon(color="red"), popup=fish_zone_true_popup_text).add_to(submission_map)
                    folium.Marker(location=[pred_latitude, pred_longitude],
                        icon=folium.Icon(color="blue"), popup=fish_zone_pred_popup_text).add_to(submission_map)

                    folium.Marker(location=[true_latitude, true_longitude],
                        icon=folium.Icon(color="red"), popup=fao_zone_true_popup_text).add_to(submission_fao_map)
                    folium.Marker(location=[pred_latitude, pred_longitude],
                        icon=folium.Icon(color="blue"), popup=fao_zone_pred_popup_text).add_to(submission_fao_map)
            
                except:
                    pass

            submission_map.save(os.path.join(submission_output_dir, "fish-zone-%s.html" % date_str))
            submission_fao_map.save(os.path.join(submission_output_dir, "fao-zone-%s.html" % date_str))

            daily_regression_metrics = calculate_regression_metrics(daily_y_true_coordinates,
                daily_y_pred_coordinates)

            daily_classification_metrics = calculate_classification_metrics(daily_y_true_fishing_zone,
                daily_y_pred_fishing_zone)

            daily_fao_classification_metrics = calculate_classification_metrics(daily_y_true_fao_zone,
                daily_y_pred_fao_zone)

            team_evaluation[date_str] = {
                "lat_lon_regression": daily_regression_metrics,
                "fish_zone_classification": daily_classification_metrics,
                "fao_zone_classification": daily_fao_classification_metrics,
                "distance": np.mean(daily_distance),
                "detailed": daily_detailed
            }

            total_y_true_coordinates.extend(daily_y_true_coordinates)
            total_y_pred_coordinates.extend(daily_y_pred_coordinates)

            total_y_true_fishing_zone.extend(daily_y_true_fishing_zone)
            total_y_pred_fishing_zone.extend(daily_y_pred_fishing_zone)
            
            total_y_true_fao_zone.extend(daily_y_true_fao_zone)
            total_y_pred_fao_zone.extend(daily_y_pred_fao_zone)

            total_distance.extend(daily_distance)

        total_regression_metrics = calculate_regression_metrics(total_y_true_coordinates,
            total_y_pred_coordinates)

        total_classification_metrics = calculate_classification_metrics(total_y_true_fishing_zone,
            total_y_pred_fishing_zone)

        total_fao_classification_metrics = calculate_classification_metrics(total_y_true_fao_zone,
            total_y_pred_fao_zone)

        team_evaluation["total_average"] = {
            "lat_lon_regression": total_regression_metrics,
            "fish_zone_classification": total_classification_metrics,
            "fao_zone_classification": total_fao_classification_metrics,
            "distance": np.mean(total_distance)
        }
        
        safe_team_predictions = {}

        for key, val in team_predictions.items():
            safe_team_predictions[key.strftime("%d%m%Y")] = val

        team_evaluation["submission"] = dict(safe_team_predictions)

        with open(os.path.join(submission_output_dir, "eval.json"), "w") as f:
            json.dump(team_evaluation, f, indent=4)
    