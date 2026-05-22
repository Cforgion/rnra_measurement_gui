# core/uncertainty.py

import math

def compute_uncertainty_budget(
    calibration_result=None,
    sigmoid_info=None,
):
    """
    Construit un budget d'incertitude global à partir des résultats
    déjà présents dans app_state.

    Parameters
    ----------
    calibration_result : dict ou None
        self.app_state["calibration_results"]
        -> { "a", "b", "R2", "channels", "energies", "rel_rms_pct" }
        ou dictionnaire multi-groupes avec "rel_rms_pct"

    sigmoid_info : dict ou None
        self.app_state["uncertainty_budget"]["sigmoid_fit"]
        -> { "value_pct", "source", "comment" }

    Returns
    -------
    dict
        {
            "rows": [
                {
                    "source": str,
                    "value": float,
                    "std_unc": float,
                    "sensitivity": float,
                    "contribution": float,
                }, ...
            ],
            "combined_uncertainty": float
        }
    """

    rows = []

    # ---------- 1) Étalonnage global ----------
    if calibration_result is not None and isinstance(calibration_result, dict):

        # Cas A : ancien format simple
        if "rel_rms_pct" in calibration_result:
            rel_rms_pct = calibration_result.get("rel_rms_pct", None)
            if rel_rms_pct is not None:
                u_rel = float(rel_rms_pct) / 100.0
                rows.append({
                    "source": "Étalonnage global (RMS relative)",
                    "value": rel_rms_pct,
                    "std_unc": u_rel,
                    "sensitivity": 1.0,
                    "contribution": abs(u_rel),
                })

        # Cas B : format multi-groupes
        else:
            calib_values = []

            for group_name, group_data in calibration_result.items():
                if not isinstance(group_data, dict):
                    continue

                rel_rms_pct = group_data.get("rel_rms_pct", None)
                if rel_rms_pct is None:
                    continue

                try:
                    rel_rms_pct = float(rel_rms_pct)
                except (TypeError, ValueError):
                    continue

                u_rel = rel_rms_pct / 100.0
                calib_values.append(u_rel)

                rows.append({
                    "source": f"Étalonnage groupe {group_name}",
                    "value": rel_rms_pct,
                    "std_unc": u_rel,
                    "sensitivity": 1.0,
                    "contribution": abs(u_rel),
                })

            if calib_values:
                mean_u = sum(calib_values) / len(calib_values)
                rows.append({
                    "source": "Étalonnage moyen (tous groupes)",
                    "value": 100.0 * mean_u,
                    "std_unc": mean_u,
                    "sensitivity": 1.0,
                    "contribution": abs(mean_u),
                })

    # ---------- 2) Fit sigmoïde ----------
    if sigmoid_info is not None:
        value_pct = sigmoid_info.get("value_pct", None)
        if value_pct is not None:
            u_rel = float(value_pct) / 100.0
            rows.append({
                "source": f"Fit sigmoïde ({sigmoid_info.get('source', '')})",
                "value": value_pct,
                "std_unc": u_rel,
                "sensitivity": 1.0,
                "contribution": abs(u_rel),
            })

    # ---------- 3) Incertitude combinée en quadrature ----------
    uc = math.sqrt(sum(r["contribution"] ** 2 for r in rows)) if rows else 0.0

    return {
        "rows": rows,
        "combined_uncertainty": uc,
    }