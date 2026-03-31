import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000/api/latest")


THRESHOLDS = {
    
    "pm10": [20, 50],
    "pm25": [10, 25],
    "o3": [100, 180],
    "no2": [40, 200],
    "so2": [100, 350],
    "nox": [100, 200],
    "co": [5, 10],
    "benzen": [2, 5]
}

# WHO Air Quality Guidelines 2021 (stricter than EU legal limits)
WHO_THRESHOLDS = {
    "pm10":  [15, 45],
    "pm25":  [5,  15],
    "o3":    [60, 100],
    "no2":   [10, 25],
    "so2":   [40, 125],
    "co":    [4,  7],
    "benzen": [1,  2],
}