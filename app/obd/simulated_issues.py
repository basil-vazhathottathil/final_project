# app/obd/simulated_issues.py

SIMULATED_ISSUES = [
    {
        "name": "Engine Overheating",
        "metric": "coolant_temp_c",
        "value": 110.5,
        "message": "Engine temperature critical! Pull over immediately.",
    },
    {
        "name": "High Engine RPM",
        "metric": "rpm",
        "value": 5200,
        "message": "Engine RPM exceeding safe limits.",
    },
    {
        "name": "Excessive Speed",
        "metric": "speed_kmph",
        "value": 135.0,
        "message": "Vehicle speed above safe threshold.",
    },
    {
        "name": "High Engine Load",
        "metric": "engine_load_pct",
        "value": 92.0,
        "message": "Engine load sustained at dangerous levels.",
    },
    {
        "name": "Aggressive Throttle",
        "metric": "throttle_pct",
        "value": 98.0,
        "message": "Extreme throttle position detected.",
    }
]
