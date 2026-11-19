import math

import streamlit as st

from utils.ui import hero, note, setup

setup("Scientific Calculator")
hero("Scientific Calculator", "Standard soil, fertilizer, laboratory and irrigation calculations. "
     "Each one shows its formula, steps and assumptions.")

REF = "Standard textbook relationship. Confirm it matches the method your course, laboratory or standard specifies."


def fert_qty(v):
    q = v["area"] * v["rate"]
    return q, "kg", [f"Quantity = area × rate = {v['area']} × {v['rate']} = {q:.6g} kg"]


def fert_product(v):
    if not 0 < v["grade"] <= 100:
        raise ValueError("Nutrient content must be between 0 and 100 %.")
    nutrient = v["area"] * v["rate"]
    q = nutrient / (v["grade"] / 100)
    return q, "kg of product", [f"Nutrient needed = {v['area']} × {v['rate']} = {nutrient:.6g} kg",
                                f"Product = nutrient ÷ (grade ÷ 100) = {nutrient:.6g} ÷ {v['grade'] / 100:.4g} = {q:.6g} kg"]


def dilution(v):
    if v["c1"] <= 0 or v["c2"] > v["c1"]:
        raise ValueError("Stock concentration must be positive and at least the target concentration.")
    v1 = v["c2"] * v["v2"] / v["c1"]
    return v1, "same volume unit as final volume", [f"C1V1 = C2V2, so V1 = C2 × V2 ÷ C1 = {v['c2']} × {v['v2']} ÷ {v['c1']} = {v1:.6g}",
                                                   f"Add solvent to make up the final volume of {v['v2']}."]


def molarity(v):
    if v["mw"] <= 0 or v["vol"] <= 0:
        raise ValueError("Molar mass and volume must be positive.")
    mol = v["mass"] / v["mw"]
    m = mol / (v["vol"] / 1000)
    return m, "mol/L", [f"Moles = mass ÷ molar mass = {v['mass']} ÷ {v['mw']} = {mol:.6g} mol",
                        f"Molarity = moles ÷ volume (L) = {mol:.6g} ÷ {v['vol'] / 1000:.6g} = {m:.6g} mol/L"]


def bulk_density(v):
    if v["vol"] <= 0:
        raise ValueError("Core volume must be positive.")
    bd = v["mass"] / v["vol"]
    return bd, "g/cm³", [f"Bulk density = oven-dry mass ÷ core volume = {v['mass']} ÷ {v['vol']} = {bd:.6g} g/cm³"]


def porosity(v):
    if v["pd"] <= 0:
        raise ValueError("Particle density must be positive.")
    pr = (1 - v["bd"] / v["pd"]) * 100
    return pr, "%", [f"Porosity = (1 − BD ÷ PD) × 100 = (1 − {v['bd']} ÷ {v['pd']}) × 100 = {pr:.6g} %"]


def moisture(v):
    if v["dry"] <= 0 or v["wet"] < v["dry"]:
        raise ValueError("Dry mass must be positive and not larger than the wet mass.")
    w = (v["wet"] - v["dry"]) / v["dry"] * 100
    return w, "% (dry-weight basis)", [f"Water mass = {v['wet']} − {v['dry']} = {v['wet'] - v['dry']:.6g}",
                                      f"Moisture = water ÷ dry mass × 100 = {w:.6g} %"]


def base_sat(v):
    if v["cec"] <= 0:
        raise ValueError("CEC must be positive.")
    s = v["ca"] + v["mg"] + v["k"] + v["na"]
    bs = s / v["cec"] * 100
    return bs, "%", [f"Sum of exchangeable bases = {v['ca']} + {v['mg']} + {v['k']} + {v['na']} = {s:.6g} cmol(+)/kg",
                     f"Base saturation = sum ÷ CEC × 100 = {s:.6g} ÷ {v['cec']} × 100 = {bs:.6g} %"]


def cv(v):
    try:
        xs = [float(x) for x in v["values"].replace(",", " ").split()]
    except ValueError:
        raise ValueError("Enter numbers only, separated by spaces, commas or new lines.")
    if len(xs) < 2:
        raise ValueError("Enter at least two values.")
    mean = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1))
    if mean == 0:
        raise ValueError("The mean is zero, so CV is undefined.")
    c = sd / mean * 100
    return c, "%", [f"n = {len(xs)}, mean = {mean:.6g}", f"Sample standard deviation (n − 1) = {sd:.6g}",
                    f"CV = SD ÷ mean × 100 = {c:.6g} %"]


def pump(v):
    if not 0 < v["eff"] <= 100:
        raise ValueError("Efficiency must be between 0 and 100 %.")
    q = v["q"] / 1000
    hyd = 1000 * 9.81 * q * v["h"]
    shaft = hyd / (v["eff"] / 100) / 1000
    return shaft, "kW (shaft power)", [f"Flow = {v['q']} L/s = {q:.6g} m³/s",
                                      f"Hydraulic power = ρ g Q H = 1000 × 9.81 × {q:.6g} × {v['h']} = {hyd:.6g} W",
                                      f"Shaft power = hydraulic ÷ efficiency = {hyd:.6g} ÷ {v['eff'] / 100:.3g} = {shaft * 1000:.6g} W"]


def irr_eff(v):
    if v["applied"] <= 0 or v["used"] > v["applied"]:
        raise ValueError("Applied water must be positive and at least the water used.")
    e = v["used"] / v["applied"] * 100
    return e, "%", [f"Efficiency = beneficially used ÷ applied × 100 = {v['used']} ÷ {v['applied']} × 100 = {e:.6g} %"]


# (id, name, category, formula, inputs[(key, label, default)], fn, assumptions)
CALCS = [
    ("Fertilizer quantity", "Fertilizer", "Quantity = area × application rate",
     [("area", "Land area (ha)", 1.0), ("rate", "Application rate (kg/ha)", 200.0)], fert_qty,
     "The rate is per hectare and refers to the product, not the nutrient."),
    ("Product needed for a nutrient rate", "Fertilizer", "Product = (area × nutrient rate) ÷ (nutrient % ÷ 100)",
     [("area", "Land area (ha)", 1.0), ("rate", "Nutrient rate (kg nutrient/ha)", 60.0), ("grade", "Nutrient content of product (%)", 46.0)],
     fert_product, "Nutrient content is given on the same basis as the rate, for example N or P2O5."),
    ("Base saturation", "Soil fertility", "BS (%) = (Ca + Mg + K + Na) ÷ CEC × 100",
     [("ca", "Exchangeable Ca (cmol/kg)", 2.0), ("mg", "Exchangeable Mg (cmol/kg)", 0.8), ("k", "Exchangeable K (cmol/kg)", 0.2),
      ("na", "Exchangeable Na (cmol/kg)", 0.1), ("cec", "CEC (cmol/kg)", 8.0)], base_sat,
     "All values are in cmol(+)/kg and from the same extraction method."),
    ("Bulk density", "Soil physics", "BD = oven-dry soil mass ÷ core volume",
     [("mass", "Oven-dry soil mass (g)", 130.0), ("vol", "Core volume (cm³)", 100.0)], bulk_density,
     "Soil dried to constant mass at 105 °C. Core volume is the undisturbed sample volume."),
    ("Total porosity", "Soil physics", "Porosity (%) = (1 − BD ÷ PD) × 100",
     [("bd", "Bulk density (g/cm³)", 1.3), ("pd", "Particle density (g/cm³)", 2.65)], porosity,
     "2.65 g/cm³ is the usual default for mineral soil. Use a measured value when you have one."),
    ("Gravimetric moisture content", "Soil physics", "θg (%) = (wet mass − dry mass) ÷ dry mass × 100",
     [("wet", "Wet soil mass (g)", 120.0), ("dry", "Oven-dry soil mass (g)", 100.0)], moisture,
     "Dry-weight basis, with the soil dried to constant mass."),
    ("Dilution (C1V1 = C2V2)", "Laboratory", "V1 = C2 × V2 ÷ C1",
     [("c1", "Stock concentration C1", 1000.0), ("c2", "Target concentration C2", 10.0), ("v2", "Final volume V2", 100.0)],
     dilution, "C1 and C2 use the same unit. Volumes are additive."),
    ("Molarity of a solution", "Laboratory", "M = (mass ÷ molar mass) ÷ volume in litres",
     [("mass", "Mass of solute (g)", 5.844), ("mw", "Molar mass (g/mol)", 58.44), ("vol", "Final volume (mL)", 1000.0)], molarity,
     "Pure solute, dissolved and made up to the final volume."),
    ("Coefficient of variation", "Statistics", "CV (%) = sample SD ÷ mean × 100",
     [("values", "Values (separated by spaces, commas or new lines)", "12.1 11.8 12.5 12.0 11.9")], cv,
     "Uses the sample standard deviation (n − 1). Suitable for ratio-scale data with a mean above zero."),
    ("Pump shaft power", "Engineering", "P = ρ g Q H ÷ η",
     [("q", "Flow rate (L/s)", 10.0), ("h", "Total head (m)", 20.0), ("eff", "Pump efficiency (%)", 65.0)], pump,
     "Water at 1000 kg/m³ and g = 9.81 m/s². Total head includes friction and lift losses."),
    ("Irrigation efficiency", "Irrigation", "Efficiency (%) = water beneficially used ÷ water applied × 100",
     [("used", "Water beneficially used (mm or m³)", 40.0), ("applied", "Water applied (same unit)", 60.0)], irr_eff,
     "Both quantities use the same unit and refer to the same area and period."),
]

c1, c2 = st.columns([2, 1])
q = c1.text_input("Search calculations", placeholder="For example moisture, fertilizer, dilution")
cats = ["All"] + sorted({c[1] for c in CALCS})
cat = c2.selectbox("Category", cats)
pool = [c for c in CALCS if (cat == "All" or c[1] == cat) and q.lower() in (c[0] + " " + c[1]).lower()]
if not pool:
    st.info("No calculation matches. Clear the search or choose another category.")
    st.stop()

name = st.selectbox("Calculation", [c[0] for c in pool])
_, category, formula, inputs, fn, assumptions = next(c for c in CALCS if c[0] == name)

st.markdown(f"**Formula:** `{formula}`")
vals = {}
cols = st.columns(2)
for i, (key, label, default) in enumerate(inputs):
    with cols[i % 2]:
        if isinstance(default, str):
            vals[key] = st.text_area(label, default, key=f"{name}-{key}")
        else:
            vals[key] = st.number_input(label, value=float(default), format="%g", key=f"{name}-{key}")
sig = st.slider("Significant figures in the answer", 2, 8, 4)

try:
    result, unit, steps = fn(vals)
    st.metric("Result", f"{float(f'{result:.{sig}g}'):g} {unit}")
    with st.expander("Calculation steps", expanded=True):
        for s in steps:
            st.markdown(f"- {s}")
except ValueError as e:
    st.error(str(e))

note(f"<b>Assumptions:</b> {assumptions}<br><b>Reference:</b> {REF}")
