import math
import numpy as np
import pandas as pd
 
 
input_csv = "fitts_law_experiment_data.csv"
df = pd.read_csv(input_csv)
print(f"Loaded data with {len(df)} rows from '{input_csv}'")
 
 
#Infer screen center from target positions
center_x = df["circle_center_x"].median()
center_y = df["circle_center_y"].median()
print(f"Inferred screen center: ({center_x:.1f}, {center_y:.1f})")
 
#Diameter (W) in pixels
df["diameter"] = 2 * df["circle_radius"]  
 
# Distance from inferred center to target center (intended distance)
dx = df["circle_center_x"] - center_x
dy = df["circle_center_y"] - center_y
df["intended_distance"] = np.sqrt(dx**2 + dy**2)
 
# Movement time in milliseconds
df["MT_ms"] = df["time_taken"] * 1000.0
 
 
df["error_flag"] = np.where(
    (df["errors"] != 0) | (df["success"] == False),
    1,
    0
)
 
#Direction derived from x-position (left/right relative to center)
df["direction_derived"] = np.where(
    df["circle_center_x"] < center_x,
    "left",
    "right"
)
 
print("\nBinning distances into 4 groups...")
 
df["distance_bin"] = pd.qcut(
    df["intended_distance"],
    4,
    labels=["D1_near", "D2_mid", "D3_far", "D4_farthest"]
)
 
bin_means = df.groupby("distance_bin")["intended_distance"].mean().to_dict()
df["D_bin_value"] = df["distance_bin"].map(bin_means).astype(float)
 
 
print("Distance bin means (pixels):")
for k, v in bin_means.items():
    print(f"  {k}: {v:.2f}")
 
 
#ID = log2(D / W + 1)
 
valid = df["diameter"] > 0
df.loc[valid, "ID_raw"] = np.log2(df.loc[valid, "D_bin_value"] / df.loc[valid, "diameter"] + 1)
 
#Round ID to 2 decimals so trials in same (distance_bin, diameter) share the same ID
df["ID"] = df["ID_raw"].round(2)
 
unique_ids = sorted(df["ID"].dropna().unique())
print(f"\nNumber of unique binned IDs: {len(unique_ids)}")
print("Sample of IDs:", unique_ids[:10])
 
 
clean_trials_path = "fitts_clean_trials.csv"
df.to_csv(clean_trials_path, index=False)
print(f"\nSaved cleaned trial-level data to '{clean_trials_path}'")
 
 
#Linear regression: MT_ms ~ ID (using binned ID)
print("\nRunning linear regression: MT_ms ~ ID ...")
 
reg_data = df[["ID", "MT_ms"]].dropna()
X = reg_data["ID"].values
Y = reg_data["MT_ms"].values
 
if len(reg_data) > 1:
    # Simple linear regression using numpy
    # MT = a * ID + b
    a, b = np.polyfit(X, Y, 1)
 
    # R^2
    Y_pred = a * X + b
    SS_res = np.sum((Y - Y_pred) ** 2)
    SS_tot = np.sum((Y - Y.mean()) ** 2)
    R2 = 1 - SS_res / SS_tot if SS_tot != 0 else np.nan
 
    # Index of Performance from slope (in bits/s)
    # a is ms/bit → convert to sec/bit
    a_sec_per_bit = a / 1000.0
    IP_global = 1.0 / a_sec_per_bit if a_sec_per_bit != 0 else np.nan
 
    print("\n--- Linear Regression Results (MT_ms ~ ID) ---")
    print(f"Slope (ms/bit): {a:.3f}")
    print(f"Intercept (ms): {b:.3f}")
    print(f"R^2: {R2:.3f}")
    print(f"Global IP (bits/s) from slope: {IP_global:.3f}")
else:
    print("Not enough data for regression.")
 
 
 
 
#Participant-level summary
participant_summary = (
    df.groupby("participant")
    .agg(
        MT_ms_mean=("MT_ms", "mean"),
        error_rate=("error_flag", "mean"),
        distance_mean=("intended_distance", "mean"),
        trials=("MT_ms", "count"),
    )
    .reset_index()
)
 
participant_summary_path = "fitts_participant_summary.csv"
participant_summary.to_csv(participant_summary_path, index=False)
print(f"\nSaved participant summary to '{participant_summary_path}'")
print(participant_summary)
 
#final table: ID, MT, Error, IP
 
print("\nGenerating assignment-style Fitts' Law results table...")
 
results = (
    df.groupby("ID")
    .agg(
        MT_ms_mean=("MT_ms", "mean"),
        error_rate=("error_flag", "mean"),
        trials=("MT_ms", "count"),
    )
    .reset_index()
)
 
#MT in milliseconds
results["MT"] = results["MT_ms_mean"]
 
#IP = ID / MT_seconds (bits/s)
results["IP"] = results["ID"] / (results["MT"] / 1000.0)
 
#Format nicely
results_formatted = pd.DataFrame({
    "ID": results["ID"],
    "MT": results["MT"].round(3),
    "Error": results["error_rate"].round(3),
    "IP": results["IP"].round(3),
})
 
excel_output = "Fitts_Law_results_binned.xlsx"
results_formatted.to_excel(excel_output, index=False)
print(f"Saved final binned Fitts' Law table to '{excel_output}'")
 
print("\nDone.")
