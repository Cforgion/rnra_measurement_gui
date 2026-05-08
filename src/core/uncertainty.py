# core/uncertainty.py

import math


def compute_uncertainty_budget(
    calibration_result=None,
    excitation_info=None,
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
    excitation_info : dict ou None
        self.app_state["uncertainty_budget"]["excitation_curve"]
        -> { "value_pct", "source", "comment" }
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
    if calibration_result is not None:
        # Erreur RMS relative globale de l'étalonnage en %
        rel_rms_pct = calibration_result.get("rel_rms_pct", None)
        if rel_rms_pct is not None:
            # On l'interprète ici comme incertitude type relative (approche simple)
            u_rel = float(rel_rms_pct) / 100.0
            rows.append({
                "source": "Étalonnage global (RMS relative)",
                "value": rel_rms_pct,
                "std_unc": u_rel,
                "sensitivity": 1.0,
                "contribution": abs(u_rel),
            })

    # ---------- 2) Courbes d'excitation ----------
    if excitation_info is not None:
        value_pct = excitation_info.get("value_pct", None)
        if value_pct is not None:
            u_rel = float(value_pct) / 100.0
            rows.append({
                "source": f"Courbes d'excitation ({excitation_info.get('source', '')})",
                "value": value_pct,
                "std_unc": u_rel,
                "sensitivity": 1.0,
                "contribution": abs(u_rel),
            })

    # ---------- 3) Fit sigmoïde ----------
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

    # ---------- 4) Incertitude combinée en quadrature ----------
    uc = math.sqrt(sum(r["contribution"] ** 2 for r in rows)) if rows else 0.0

    return {
        "rows": rows,
        "combined_uncertainty": uc,
    }