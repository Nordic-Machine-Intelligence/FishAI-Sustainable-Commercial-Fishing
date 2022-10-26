# FishAI: Sustainable Commercial Fishing

With a fishing zone of 2.1 million square meters, Norway is considered Europe's largest fishing and aquaculture nation. Every year,  commercial vessels land fish to a total value of around NOK 20 billion in Norway. At an overall level, the migration patterns of a variety of fish species are relatively predictable. A fisherman knows, for example, that the mackerel season starts in mid-September and plans accordingly. On a daily basis however, fish can move over large distances, and with the main decision-making tool being the captain´s experience and intuition, boats typically search for days, even weeks, before making a catch. In other words, there are great environmental benefits and opportunities in optimizing commercial fishing activities by reducing unnecessary transport distances. We believe that smarter use of publicly available data is key to transforming one of the oldest industries in the world.

# Tasks

**Task 1:** Build a model that can predict which coordinates a vessel should prioritize in order to maximize the likelihood of catching a type of fish of your choosing (haddock or mackerel is most valuable for our industry partners). The prediction can be based on historical data.

**Task 2:** Create a report of your analysis that can be read by experienced fishermen; an user-friendly visualization that a captain can read to make a assessment of where the vessel should search for fish the next day

**Task 3:** Make a Sustainable Fishing Plan; a weekly plan that suggests the routes the fisherman should follow to optimize fish caught and fuel consumption 

# Evaluation
The evaluation script located in `evaluation` produces a directory containing the evaluation files associated with a submission. This includes an `eval.json` file that contains all quantitative metrics and several HTML files that show the predictions with the ground truth on an interactive map. There are several approaches to calculating the metrics, namely, from a classification perspective and a regression perspective. For the classification perspective, we treat the predictions as predicting a marker within a specific fishing zone or FAO zone. FAO zones comprise several fishing zones, making them much easier to predict. Please note that predictions made on the border of any zone will be counted as undefined. The regression metrics are calculated based on the predicted longitude and latitude measured against the actual longitude and latitude values. We also include the average distance in kilometers from the ground truth. The metrics included in the `eval.json` file are calculated for each day (`dd-mm-yyyy`) and also include an average calculation across all days (`total_average`) in the submission.


<details>
  <summary>See example</summary>

```
{
    "10-10-2022": {
        "lat_lon_regression": {
            "mean_squared_error": 0.0,
            "raw_mean_squared_error": [
                0.0,
                0.0
            ],
            "mean_root_squared_error": 0.0,
            "raw_mean_root_squared_error": [
                0.0,
                0.0
            ],
            "mean_absolute_error": 0.0,
            "raw_mean_absolute_error": [
                0.0,
                0.0
            ],
            "mean_absolute_percentage_error": 0.0,
            "raw_mean_absolute_percentage_error": [
                0.0,
                0.0
            ]
        },
        "fish_zone_classification": {
            "recall_micro": 0.0,
            "recall_macro": 0.0,
            "precision_micro": 0.0,
            "precision_macro": 0.0,
            "f1_micro": 0.0,
            "f1_macro": 0.0,
            "matthews_correlation_coefficient": 0.0
        },
        "fao_zone_classification": {
            "recall_micro": 0.0,
            "recall_macro": 0.0,
            "precision_micro": 0.0,
            "precision_macro": 0.0,
            "f1_micro": 0.0,
            "f1_macro": 0.0,
            "matthews_correlation_coefficient": 0.0
        },
        "distance": 0.0,
        "detailed": {
            "Berggylt": {
                "true_coordinates": {
                    "longitude": 0.0,
                    "latitude": 0.0
                },
                "true_fish_zone": 232,
                "predicted_coordinates": {
                    "longitude": 0.0,
                    "latitude": 0.0
                },
                "predicted_fish_zone": 0,
                "predicted_fao_zone": 3,
                "prediction_distance_from_true_km": 0.0
            },
            ...
        },
        ...
    },
    "total_average": {
        "lat_lon_regression": {
            "mean_squared_error": 0.0,
            ...
        },
        ...
    },
    "submission": {
        "10102022": {
            "Berggylt": {
                "longitude": 0.0,
                "latitude": 0.0,
                "location": "Not available",
                "fao_zone": "27.4.A"
            },
            ...
        },
    ...
    }
}
```
  
</details>

The HTML files included in the produce evaluation directory plot the predicted markers (blue) against the ground truth (red). See example below.

![map](https://raw.githubusercontent.com/Nordic-Machine-Intelligence/FishAI-Sustainable-Commercial-Fishing/main/static/images/map.png)

# Data
The following data is provided to complete the aforementioned tasks.

### Catch Notes Data
The data contains catch notes collected by the Norwegian Fishing Directorate from 2000 to today for vessels larger than 15 meters. The notes consist of information about the catch that is manually logged during landing, e.g., when it was caught, where it was caught, what equipment was used, the species distribution of the catch etc. There are approximately 130~data fields and around one million notes each year.

### Salinity Data
Monthly averages of salinity data from 2015 to present day is provided from the SMAP Salinity V4 dataset. Salinity (in combination with temperature) affects the growth rate of microalgae. This can potentially affect the migration patterns of fish. Eight-day running averages are also possible to obtain if needed (https://salinity.oceansciences.org/data-smap-v4.htm).

### Moon Phase Data
The moon phase data consists of dates and exact times of full moon from 1900 to 2050. Lunar phases affect the migration and behaviour of fish due to water levels changing. Therefore, it is potentially possible to use this data source for modelling of the movement of fish. The dataset is published at https://www.kaggle.com/datasets/lsind18/full-moon-calendar-1900-2050.

### Temperature Data
Sea surface temperature (SST) from 1981 to present has been collected by National Oceanic and Atmospheric Administration (US). It contains daily estimates of SST globally. The data was collected from satellite observations, and consists of daily data at 0.25 degree latitude x 0.25 degree longitude resolution. We have included the subset of data from 2000 to present day. The dataset is published at: https://www.psl.noaa.gov/data/gridded/data.noaa.oisst.v2.highres.

# Important Dates
| Date                   | Event                                            |
|----------------------- | -----------------------------------------------------|
| May 9th, 2022          | Competition launch and dataset release. |
| June 16th, 2022        | Digital Kick off and Q&A for registered teams. |
| September 25th, 2022   | Deadline for submitting results. |
| ~~October 14th, 2022~~ | ~~Jury evaluation of results.~~|
| October 24th, 2022     | Jury evaluation of results.|
| ~~October 24th, 2022~~ | ~~Deadline for submitting method description paper.~~ |
| October 31st, 2022     | Deadline for submitting method description paper. |
| November 14th, 2022    | Presentation and winner announcement! |
