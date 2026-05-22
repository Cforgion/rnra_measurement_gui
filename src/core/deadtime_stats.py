import re
import math
import pandas as pd


def infer_day_from_basename(basename):
    basename = str(basename)
    m = re.match(r"(\d{6})", basename)
    return m.group(1) if m else basename


def compute_deadtime_stats_by_day(files_data, adc_name="ADC0"):
    adc_name = str(adc_name)

    possible_keys = [
        f"deadtime_{adc_name}",                 # ex: deadtime_ADC0
        f"deadtime{adc_name}",                  # ex: deadtimeADC0
        f"deadtime_ADCDATA{adc_name[-1]}",      # ex: deadtime_ADCDATA0
        f"deadtimeADCDATA{adc_name[-1]}",       # ex: deadtimeADCDATA0
    ]

    rows = []

    for fd in files_data:
        if not isinstance(fd, dict):
            continue

        found_key = None
        for key in possible_keys:
            if key in fd:
                found_key = key
                break

        if found_key is None:
            continue

        try:
            deadtime = float(fd[found_key])
        except (TypeError, ValueError):
            continue

        day = infer_day_from_basename(fd.get("fichier_base", ""))
        rows.append({
            "jour": day,
            "adc": adc_name,
            "deadtime": deadtime,
        })

    if not rows:
        return pd.DataFrame(
            columns=["jour", "adc", "deadtime_mean", "deadtime_std", "n_files"]
        )

    df = pd.DataFrame(rows)

    return (
        df.groupby(["jour", "adc"])["deadtime"]
          .agg(deadtime_mean="mean", deadtime_std="std", n_files="size")
          .reset_index()
          .sort_values("jour")
    )