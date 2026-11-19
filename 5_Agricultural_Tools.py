from utils.ui import coming_soon, hero, setup

setup("Agricultural Tools")
hero("Agricultural Tools", "Engineering calculators and practical tools for crops, water, soil and machinery.")

coming_soon(
    "This section is being built, one tool at a time. Below is what is planned.",
    {
        "Irrigation engineering": ["Crop water requirement", "Irrigation scheduling", "Drip and sprinkler design"],
        "Fertilizer management": ["Recommendations", "Blending", "Nutrient balance"],
        "Climate and weather": ["Rainfall and temperature analysis", "Evapotranspiration", "Drought monitoring"],
        "GIS and remote sensing": ["Land-use mapping", "NDVI analysis", "Soil nutrient mapping"],
        "Farm machinery": ["Tractor power", "Field capacity", "Fuel consumption"],
        "Greenhouse and hydroponics": ["Nutrient solutions", "EC and pH management", "Ventilation"],
        "Soil and water conservation": ["Erosion estimation", "Runoff", "Drainage design"],
        "Crop production": ["Yield estimation", "Growth monitoring", "Harvest planning"],
        "Renewable energy": ["Solar irrigation", "Biogas", "Biomass estimation"],
        "Post-harvest engineering": ["Drying", "Storage", "Post-harvest loss"],
    },
)
