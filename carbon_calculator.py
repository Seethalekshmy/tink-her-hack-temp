# services/carbon_calculator.py — Estimates carbon emissions from email storage
#
# 📊 Formula basis:
# - Data centers consume roughly 0.00000007 kWh per MB per day to store data
# - The average carbon intensity of electricity is ~0.233 kg CO2 per kWh (global average)
# - So: CO2 (kg) = storage_MB × days × 0.00000007 kWh/MB/day × 0.233 kg/kWh
#
# Sources: The Shift Project, IEA, Mike Berners-Lee "How Bad Are Bananas?"
# Note: These are simplified estimates — real figures vary by data center location & energy mix.

# Energy used per MB of data stored per day (kWh)
KWH_PER_MB_PER_DAY = 0.00000007

# Carbon intensity of average global electricity (kg CO2 per kWh)
# Use 0.233 for global average; use 0.049 for renewable-heavy grids (e.g., France)
KG_CO2_PER_KWH = 0.233

# How many days per year email is stored
DAYS_PER_YEAR = 365

# For comparison, a typical car emits ~0.21 kg CO2 per mile driven
KG_CO2_PER_CAR_MILE = 0.21

# A tree absorbs roughly 21 kg of CO2 per year
KG_CO2_ABSORBED_PER_TREE_PER_YEAR = 21


def calculate_carbon(total_size_mb: float) -> dict:
    """
    Estimates the annual carbon footprint of storing email data.
    
    Args:
        total_size_mb: Total size of analyzed emails in megabytes
    
    Returns:
        A dictionary with carbon estimates and relatable comparisons
    """

    # --- Core calculation ---
    # Annual CO2 from storing this email data for one year
    annual_co2_kg = total_size_mb * DAYS_PER_YEAR * KWH_PER_MB_PER_DAY * KG_CO2_PER_KWH

    # Convert to grams for smaller values (easier to read if < 1 kg)
    annual_co2_grams = annual_co2_kg * 1000

    # --- Relatable comparisons ---
    # How many car miles does this equal?
    equivalent_car_miles = annual_co2_kg / KG_CO2_PER_CAR_MILE

    # How many trees would need to absorb this?
    trees_needed = annual_co2_kg / KG_CO2_ABSORBED_PER_TREE_PER_YEAR

    # --- Savings potential ---
    # If the user deleted their old emails (assume 30% are deletable), how much CO2 saved?
    deletable_fraction = 0.30  # Conservative estimate
    potential_savings_kg = annual_co2_kg * deletable_fraction

    # --- Severity label ---
    # Give users a simple label to understand their footprint level
    if annual_co2_kg < 0.01:
        severity = "🟢 Very Low"
        tip = "Great job! Your email footprint is minimal."
    elif annual_co2_kg < 0.1:
        severity = "🟡 Low"
        tip = "Not bad! Deleting old emails could reduce this further."
    elif annual_co2_kg < 1.0:
        severity = "🟠 Moderate"
        tip = "Consider unsubscribing from newsletters and deleting emails older than 1 year."
    else:
        severity = "🔴 High"
        tip = "Your email storage has a significant footprint. A regular email cleanup could help a lot!"

    return {
        "total_storage_analyzed_mb": round(total_size_mb, 2),
        "annual_co2_kg": round(annual_co2_kg, 6),
        "annual_co2_grams": round(annual_co2_grams, 4),
        "severity": severity,
        "tip": tip,
        "comparisons": {
            "equivalent_car_miles": round(equivalent_car_miles, 4),
            "trees_needed_to_offset": round(trees_needed, 6),
        },
        "potential_savings": {
            "if_deleted_30_percent_kg": round(potential_savings_kg, 6),
            "description": "Estimated CO2 saved if you deleted 30% of your emails"
        },
        "formula_note": (
            f"Formula: {total_size_mb:.2f} MB × {DAYS_PER_YEAR} days × "
            f"{KWH_PER_MB_PER_DAY} kWh/MB/day × {KG_CO2_PER_KWH} kg CO2/kWh"
        )
    }
