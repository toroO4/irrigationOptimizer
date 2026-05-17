"""
SAR Irrigation Scheduling System — System-Wide Constants.

Contains all domain-specific constants used across modules:
- Crop coefficients (Kc)
- Soil texture parameters
- Irrigation system efficiencies
- SAR processing defaults
- Scheduling thresholds
"""

# ============================================================
# CROP COEFFICIENTS (Kc) — FAO-56 standard values
# ============================================================
# Kc values by crop type and growth stage:
#   initial, mid-season, late-season
CROP_COEFFICIENTS = {
    "wheat": {"initial": 0.30, "mid": 1.15, "late": 0.40},
    "rice": {"initial": 1.05, "mid": 1.20, "late": 0.90},
    "maize": {"initial": 0.30, "mid": 1.20, "late": 0.60},
    "cotton": {"initial": 0.35, "mid": 1.15, "late": 0.70},
    "sugarcane": {"initial": 0.40, "mid": 1.25, "late": 0.75},
    "soybean": {"initial": 0.40, "mid": 1.15, "late": 0.50},
    "groundnut": {"initial": 0.40, "mid": 1.15, "late": 0.60},
    "sunflower": {"initial": 0.35, "mid": 1.10, "late": 0.35},
    "chickpea": {"initial": 0.40, "mid": 1.00, "late": 0.35},
    "mustard": {"initial": 0.35, "mid": 1.10, "late": 0.30},
    "potato": {"initial": 0.50, "mid": 1.15, "late": 0.75},
    "tomato": {"initial": 0.60, "mid": 1.15, "late": 0.80},
    "onion": {"initial": 0.70, "mid": 1.05, "late": 0.75},
    "default": {"initial": 0.40, "mid": 1.10, "late": 0.50},
}

# ============================================================
# SOIL TEXTURE PARAMETERS — USDA classification
# ============================================================
# fc_range: field capacity range (cm³/cm³)
# wp_range: wilting point range (cm³/cm³)
# sat_range: saturation range (cm³/cm³)
# ksat: saturated hydraulic conductivity (mm/hr)
SOIL_TEXTURE_PARAMS = {
    "sand": {
        "fc_range": (0.06, 0.12),
        "wp_range": (0.02, 0.04),
        "sat_range": (0.36, 0.46),
        "ksat": 210.0,
    },
    "loamy_sand": {
        "fc_range": (0.10, 0.18),
        "wp_range": (0.03, 0.06),
        "sat_range": (0.38, 0.48),
        "ksat": 61.0,
    },
    "sandy_loam": {
        "fc_range": (0.12, 0.22),
        "wp_range": (0.05, 0.10),
        "sat_range": (0.38, 0.50),
        "ksat": 25.0,
    },
    "loam": {
        "fc_range": (0.18, 0.27),
        "wp_range": (0.07, 0.13),
        "sat_range": (0.40, 0.52),
        "ksat": 13.0,
    },
    "silt_loam": {
        "fc_range": (0.22, 0.36),
        "wp_range": (0.09, 0.15),
        "sat_range": (0.42, 0.54),
        "ksat": 6.8,
    },
    "silt": {
        "fc_range": (0.28, 0.38),
        "wp_range": (0.06, 0.12),
        "sat_range": (0.44, 0.56),
        "ksat": 3.4,
    },
    "sandy_clay_loam": {
        "fc_range": (0.20, 0.30),
        "wp_range": (0.10, 0.17),
        "sat_range": (0.38, 0.48),
        "ksat": 4.3,
    },
    "clay_loam": {
        "fc_range": (0.24, 0.36),
        "wp_range": (0.13, 0.20),
        "sat_range": (0.40, 0.52),
        "ksat": 2.3,
    },
    "silty_clay_loam": {
        "fc_range": (0.30, 0.42),
        "wp_range": (0.15, 0.22),
        "sat_range": (0.42, 0.56),
        "ksat": 1.5,
    },
    "sandy_clay": {
        "fc_range": (0.22, 0.34),
        "wp_range": (0.15, 0.24),
        "sat_range": (0.38, 0.48),
        "ksat": 1.2,
    },
    "silty_clay": {
        "fc_range": (0.30, 0.44),
        "wp_range": (0.17, 0.26),
        "sat_range": (0.42, 0.56),
        "ksat": 0.9,
    },
    "clay": {
        "fc_range": (0.32, 0.46),
        "wp_range": (0.20, 0.28),
        "sat_range": (0.44, 0.58),
        "ksat": 0.6,
    },
}

# ============================================================
# IRRIGATION SYSTEM EFFICIENCY
# ============================================================
# Efficiency as a fraction (0–1)
IRRIGATION_EFFICIENCY = {
    "drip": 0.90,
    "sprinkler": 0.75,
    "center_pivot": 0.80,
    "flood": 0.50,
    "furrow": 0.55,
    "micro_sprinkler": 0.85,
}

# ============================================================
# SAR PROCESSING DEFAULTS
# ============================================================
# Sentinel-1 C-band frequency (GHz)
SAR_FREQUENCY_GHZ = 5.405

# Default speckle filter window size (pixels)
SPECKLE_FILTER_WINDOW = 7

# Terrain correction DEM source
TERRAIN_DEM_SOURCE = "SRTM_30m"

# Water Cloud Model default parameters
# A, B, C, D are empirical coefficients calibrated per region
WCM_DEFAULT_PARAMS = {
    "A": 0.0018,   # Vegetation descriptor coefficient
    "B": 0.138,    # Vegetation attenuation coefficient
    "C": -0.028,   # Soil moisture sensitivity coefficient
    "D": -17.5,    # Soil backscatter offset (dB)
}

# ============================================================
# SCHEDULING THRESHOLDS
# ============================================================
# Management Allowable Depletion (MAD) — fraction of AWC
# Below this, irrigation is triggered
MAD_THRESHOLD = 0.50

# Urgency levels based on moisture relative to thresholds
URGENCY_LEVELS = {
    "critical": 0.20,    # Below 20% of AWC → immediate irrigation
    "high": 0.35,        # Below 35% of AWC → irrigate within 6 hours
    "moderate": 0.50,    # Below 50% of AWC → irrigate within 24 hours
    "low": 0.65,         # Below 65% of AWC → optional irrigation
    "none": 1.00,        # Adequate moisture → no irrigation needed
}

# Default pump specifications
DEFAULT_PUMP_FLOW_RATE_LPH = 5000.0    # Liters per hour
DEFAULT_PUMP_POWER_KW = 3.7            # Kilowatts
DEFAULT_PIPE_LOSS_FRACTION = 0.05      # 5% conveyance loss

# Preferred electricity windows (24-hour format)
ELECTRICITY_WINDOWS = [
    {"start": "06:00", "end": "10:00", "tariff": "low"},
    {"start": "10:00", "end": "18:00", "tariff": "high"},
    {"start": "18:00", "end": "22:00", "tariff": "medium"},
    {"start": "22:00", "end": "06:00", "tariff": "low"},
]

# ============================================================
# FEATURE NAMES — for ML model input
# ============================================================
SOIL_FEATURES = [
    "soil_type",
    "soil_ph",
    "soil_moisture",
    "organic_carbon",
    "electrical_conductivity",
]

WEATHER_FEATURES = [
    "temperature_c",
    "humidity",
    "rainfall_mm",
    "sunlight_hours",
    "wind_speed_kmh",
]

CROP_FEATURES = [
    "crop_type",
    "crop_growth_stage",
    "season",
]

IRRIGATION_FEATURES = [
    "irrigation_type",
    "water_source",
    "field_area_hectare",
    "mulching_used",
    "previous_irrigation_mm",
    "region",
]

# Complete feature list in expected order for ML models
ALL_FEATURES = (
    SOIL_FEATURES + WEATHER_FEATURES + CROP_FEATURES + IRRIGATION_FEATURES
)

# ============================================================
# NDVI PHENOLOGY THRESHOLDS
# ============================================================
NDVI_THRESHOLDS = {
    "bare_soil": 0.15,
    "sparse_vegetation": 0.25,
    "moderate_vegetation": 0.45,
    "dense_vegetation": 0.65,
    "peak_vegetation": 0.80,
}

# ============================================================
# DROUGHT SEVERITY CLASSIFICATION
# ============================================================
DROUGHT_CLASSES = {
    "D0": {"label": "Abnormally Dry", "moisture_pct": 30},
    "D1": {"label": "Moderate Drought", "moisture_pct": 20},
    "D2": {"label": "Severe Drought", "moisture_pct": 10},
    "D3": {"label": "Extreme Drought", "moisture_pct": 5},
    "D4": {"label": "Exceptional Drought", "moisture_pct": 2},
}

# ============================================================
# DATA VALIDATION BOUNDS
# ============================================================
VALID_RANGES = {
    "soil_ph": (0.0, 14.0),
    "soil_moisture": (0.0, 100.0),        # %
    "organic_carbon": (0.0, 10.0),
    "electrical_conductivity": (0.0, 20.0),
    "temperature_c": (-10.0, 55.0),       # °C
    "humidity": (0.0, 100.0),             # %
    "rainfall_mm": (0.0, 5000.0),         # mm
    "sunlight_hours": (0.0, 24.0),        # hours
    "wind_speed_kmh": (0.0, 150.0),       # km/h
    "field_area_hectare": (0.0, 1000.0),
    "previous_irrigation_mm": (0.0, 1000.0),
}
