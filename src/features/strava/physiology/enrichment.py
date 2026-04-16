from src.shared.dependencies import db
from src.shared.logger import logger

def _get_zone(hr: float, boundaries: list[float]) -> str:
    """
    boundaries should be a list of 4 floats: [z1_upper, z2_upper, z3_upper, z4_upper]
    Z1: < z1_upper
    Z2: >= z1_upper and < z2_upper
    Z3: >= z2_upper and < z3_upper
    Z4: >= z3_upper and < z4_upper
    Z5: >= z4_upper
    """
    if hr < boundaries[0]:
        return "Zone 1"
    elif hr < boundaries[1]:
        return "Zone 2"
    elif hr < boundaries[2]:
        return "Zone 3"
    elif hr < boundaries[3]:
        return "Zone 4"
    else:
        return "Zone 5"

async def enrich_with_physiology(user_id: str, parsed_data: dict, current_year: int = 2026) -> dict | None:
    if parsed_data.get("average_heartrate") is None:
        logger.info(f"Skipping physiological enrichment for user {user_id}: no average_heartrate data.")
        return None

    user_doc = await db.get("users", user_id)
    if not user_doc:
        logger.warning(f"Skipping physiological enrichment: user {user_id} not found in db.")
        return None
        
    biometrics = user_doc.get("biometrics", {})
    
    boundaries = []
    calc_method = ""
    
    if biometrics.get("threshold_hr"):
        calc_method = "LTHR"
        lthr = float(biometrics["threshold_hr"])
        boundaries = [0.85 * lthr, 0.90 * lthr, 0.95 * lthr, 1.00 * lthr]
        logger.info(f"Physiology logic tier 1: Using LTHR method for user {user_id} with LTHR {lthr}")
    elif biometrics.get("max_hr") and biometrics.get("resting_hr"):
        calc_method = "Karvonen"
        hrr = float(biometrics["max_hr"]) - float(biometrics["resting_hr"])
        rest = float(biometrics["resting_hr"])
        boundaries = [rest + 0.60 * hrr, rest + 0.70 * hrr, rest + 0.80 * hrr, rest + 0.90 * hrr]
        logger.info(f"Physiology logic tier 2: Using Karvonen method for user {user_id} with HRR {hrr}")
    else:
        calc_method = "Standard Max HR"
        if biometrics.get("max_hr"):
            max_hr = float(biometrics["max_hr"])
        else:
            birth_year = biometrics.get("birth_year", 1983)
            max_hr = 208.0 - 0.7 * (current_year - birth_year)
        boundaries = [0.68 * max_hr, 0.73 * max_hr, 0.80 * max_hr, 0.87 * max_hr]
        logger.info(f"Physiology logic tier 3: Using Standard Max HR method for user {user_id} with max HR {max_hr}")

    avg_hr = float(parsed_data["average_heartrate"])
    primary_zone = _get_zone(avg_hr, boundaries)
    
    splits = parsed_data.get("splits", [])
    valid_splits_count = 0
    total_weight = 0.0
    
    weights = {
        "Zone 1": 1.5,
        "Zone 2": 3.0,
        "Zone 3": 5.5,
        "Zone 4": 8.0,
        "Zone 5": 10.0
    }
    
    for split in splits:
        if split.get("average_heartrate") is not None:
            split_hr = float(split["average_heartrate"])
            split_zone = _get_zone(split_hr, boundaries)
            total_weight += weights[split_zone]
            valid_splits_count += 1
            
    if valid_splits_count > 0:
        intensity_score = round(total_weight / valid_splits_count, 1)
    else:
        # Fallback if no valid split HR data but overall HR exists
        intensity_score = round(weights[primary_zone], 1)
        logger.info(f"No valid split HR data for user {user_id}, falling back to primary zone intensity ({intensity_score})")
        
    logger.info(f"Physiology enrichment completed", extra={
        "user_id": user_id,
        "primary_zone": primary_zone,
        "intensity_score": intensity_score,
        "calculation_method": calc_method
    })
        
    return {
        "primary_zone": primary_zone,
        "intensity_score": intensity_score,
        "calculation_method": calc_method
    }
