import pandas as pd
import glob
import os

# Path to the data folder
folder_path = r"C:\Users\Admin\OneDrive\Desktop\AsistenciaAsambleaLegislativa2022-2026\data"

# Get all .xlsx files
xlsx_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
xlsx_files.sort()

dfs = []

for file in xlsx_files:
    try:
        # Always skip the junk first row in every file
        df = pd.read_excel(file, skiprows=1)

        # Drop last 2 rows
        df = df.iloc[:-2]

        # Remove first column
        df = df.drop(df.columns[0], axis=1)
        
        # Add filename for tracking
        df["source_file"] = os.path.basename(file)

        dfs.append(df)

    except Exception as e:
        print(f"Error reading {file}: {e}")

# Combine DataFrames
if dfs:
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Keep only columns 0 to 30 (0–30 = 31 columns)
    combined_df = combined_df.iloc[:, :31]  
    
    # Save to Excel
    output_path = os.path.join(folder_path, "combined_asistencia.xlsx")
    combined_df.to_excel(output_path, index=False)
    print(f"✅ Combined {len(dfs)} files with {combined_df.shape[0]} rows")

else:
    print("⚠ No Excel files found in the folder.")
    # Keep only columns 0 to 30 (0–30 = 31 columns)
    #combined_df = combined_df.iloc[:, :31]  
    #print(f"✅ Loaded {len(dfs)} files with {combined_df.shape[0]} rows")


