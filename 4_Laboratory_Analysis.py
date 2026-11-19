from utils.ui import coming_soon, hero, setup

setup("Laboratory Analysis")
hero("Laboratory Analysis", "Soil and water procedures with chemicals, equipment, steps and quality control.")

coming_soon(
    "This section is being built. Each procedure will be added only after it is checked against the published "
    "method it cites, so no chemical quantities or steps are invented. Below is what is planned.",
    {
        "Soil: physical and moisture": ["Texture", "Bulk and particle density", "Porosity", "Gravimetric moisture"],
        "Soil: chemical": ["pH and EC", "Organic carbon and matter", "Total N, available P, exchangeable K", "Ca, Mg, S"],
        "Soil: micronutrients and CEC": ["Fe, Mn, Zn, Cu, B", "CEC and exchangeable acidity", "Base saturation", "Heavy metals"],
        "Water: physical and basic chemistry": ["Temperature, turbidity, colour, TSS", "pH, EC, TDS", "Hardness and alkalinity"],
        "Water: ions and nutrients": ["Chloride, sulphate, nitrate", "Phosphate, ammonia, total nitrogen"],
        "Water: oxygen, metals, microbiology": ["DO, BOD, COD", "Fe, Mn, Pb, Cd, As", "Total coliforms and E. coli"],
    },
)
