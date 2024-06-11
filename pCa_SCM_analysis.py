"""Written using Python 3.11"""

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd

import sys
import os, subprocess
from pathlib import Path

import pandas as pd
import random
import string
import numpy as np
import time

from scipy.ndimage import gaussian_filter
import warnings


def main():
    """
    This automates the filtering of single cell mechanics files

    """
    # For higher resolution screens (just personal thing)
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)

    def select_files(event=None):
        global root_folder

        root_folder = fd.askdirectory(
            title="Open files", initialdir=r"C:\Users\Desktop"
        )

        root.destroy()

    filtering_amount = 10

    # Placing these here to make them easy to change if desired...

    # This is how many data points (i.e. ms if sampling rate = 1kHz) to average for the baseline
    FIRST_AVG = 200
    # This is how long the motor arm takes to move, which is lengthened as filtering # increases
    PAUSE = 40
    # This is how many data points to average for the change in force, a small number seems to work better for high Ca points
    SECOND_AVG = 5

    # Gui Creation:

    # Create the main window
    root = tk.Tk()
    root.title("Sine Strands v0.1.0")

    # Create and configure the frame
    frame = ttk.Frame(root, padding=10)
    frame.grid(column=0, row=0)

    # Making variables
    filtering_var = tk.BooleanVar()
    folder_name = tk.StringVar()
    filtering_strength = tk.IntVar(value=filtering_amount)

    # Create and place the label for folder name
    folder_name_label = ttk.Label(frame, text="Folder Name:")
    folder_name_label.grid(column=0, row=0, sticky="w", padx=10, pady=10)

    # Create and place the entry field for folder name
    folder_name_entry = tk.Entry(frame, textvariable=folder_name)
    folder_name_entry.grid(column=1, row=0, padx=10, pady=10)

    # Create and place the label and entry for filter strength
    filter_strength_label = ttk.Label(frame, text="Filter Strength:")
    filter_strength_label.grid(column=0, row=1, sticky="w", padx=10, pady=10)

    filter_strength_entry = tk.Entry(frame, textvariable=filtering_strength)
    filter_strength_entry.grid(column=1, row=1, padx=10, pady=10)

    # Create and place the button to open the files
    create_button = ttk.Button(frame, text="Open Files", command=select_files)
    create_button.grid(column=0, row=2, columnspan=2, padx=10, pady=10)
    root.bind("<Return>", select_files)

    # Run the tkinter main loop
    root.mainloop()

    # Folder Creation
    current_dir = Path(os.getcwd())
    output_dir = current_dir / folder_name.get()

    try:
        os.mkdir(output_dir)
    except FileExistsError:
        # If it already exists, adds 5 random digits to the end
        output_dir = current_dir / (
            folder_name.get()
            + "-"
            + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        )
        os.mkdir(output_dir)
        print("Folder name already existed, made copy instead. Everybody gets one.")

    os.chdir(output_dir)

    # Making Collated Difference excel
    difference_dict = {"Cell #": [], "Force Diff": [], "% Activating": []}

    # Making Thickness Excel sheet
    thickness_dict = {"Cell #": [], "Width": [], "Thick": []}

    # subdirs has the full filepath
    # dirs just has the name of the folders in the selected folder
    first = True
    for subdir, dirs, files in os.walk(root_folder):

        # For the first iteration, make n num of folders, to hold the filtered CSVs and traces
        if first:
            for dir in dirs:
                os.mkdir(dir)
            first = False

        for file in files:
            # Changing from "60.dat" to C:/Users/panch/Desktop/Important/Gregorio Lab/Single Cell Mechanics/2024-04-05 Test/Cell 1/60.dat
            working_filepath = os.path.join(subdir, file)
            working_filepath = Path(working_filepath)
            cell_num = int(working_filepath.parent.name[-1])

            # On mac, there is a hidden metadata file named ".DS_Store"
            # if found, skip that file
            if file[0] == ".":
                continue

            # Making a basename, for human reading
            elif ".dat" in file or ".txt" in file:
                filename = file[:-4]

            else:
                filename = file

            # TBH I got this from stackoverflow for reading DAT files
            try:
                DAT_df = pd.DataFrame(
                    [i.strip().split() for i in open(working_filepath).readlines()]
                )

            except UnicodeDecodeError:
                print(f"Uh Oh, Corrupted File! Please check: {file}")
                time.sleep(2)
                continue

            # We only want to do this for the first file of "Cell n"
            # If there is already a value for the cell, do nothing
            try:
                thickness_dict["Cell #"][cell_num - 1]  # - 1 because index starts at 0

            # Else, find and save values to thickness_dict
            except IndexError:
                # Finding Thickness, which is right after the first use of "Comment:"f
                comments = DAT_df.loc[DAT_df[0] == "Comment:"].index.to_list()

                thickness = (
                    DAT_df.iloc[comments[0] + 1 : comments[0] + 3, [0, 1]]
                    .reset_index(drop=True)
                    .transpose()
                )

                # Making the words "Width" & "Thick" into columns, then removing the columns from the data
                thickness.columns = thickness.iloc[0]
                thickness = thickness[1:]

                thickness_dict["Cell #"].append(
                    cell_num
                )  # Finding parent "Cell n", appending "n"
                thickness_dict["Width"].append(thickness.loc[1, "Width"])
                thickness_dict["Thick"].append(thickness.loc[1, "Thick"])

            # This is finding the parameters' start & end
            # Looks for "time", where the second and third instance are the boundries for the timing
            try:
                parameter_locs = DAT_df.loc[DAT_df[0] == "Time"].index.tolist()
            except KeyError:
                print(
                    f"File '{filename}' in Folder {working_filepath.parent.name} does not comply with convention and was therefore skipped! Please check {filename} to ensure this was correct..."
                )
                continue
            parameter_locs[2] -= 2

            # Preparing the data to be analyzed
            column_names = [
                "Time",
                "Lin",
                "Fin",
                "SL",
            ]

            # We only want Time (0), Lin (1), Fin (3), and SL (7)
            fiber_data = pd.DataFrame(
                DAT_df.iloc[(parameter_locs[2] + 3) :, [0, 1, 3, 7]]
            )
            fiber_data.reset_index(drop=True, inplace=True)

            fiber_data.columns = column_names

            full_data_df = fiber_data.copy()
            full_data_df.reset_index(drop=True, inplace=True)
            full_data_df = full_data_df.astype(
                {
                    "Time": "float",
                    "Lin": "float",
                    "Fin": "float",
                    "SL": "float",
                }
            )

            # Filter Force
            full_data_df["Fin"] = gaussian_filter(
                full_data_df["Fin"], filtering_strength.get()
            )

            data = full_data_df["Fin"].values

            base_force = np.mean(
                data[:FIRST_AVG]
            )  # Average the first 200ms for a baselined (set by first average #)
            step_force = np.mean(
                data[(FIRST_AVG + PAUSE) : (FIRST_AVG + PAUSE + SECOND_AVG)]
            )  # Give 40ms for the motor to move, then average the next 5ms for the changed force (smaller thing seems to be better)

            force_diff = abs(base_force - step_force) * 1000  # From mN to uN

            # Getting an int number from filename & converting strings "active"/"passive" to 100/0
            try:
                conc_activating = int(filename.strip())

            except ValueError:
                if "active" in filename.strip().lower():
                    conc_activating = 100

                elif "passive" in filename.strip().lower():
                    conc_activating = 0

                else:
                    warnings.warn(
                        f"Non-conforming filename... please enter correct % activating for {filename}"
                    )
                    correct_activ = input(">>").strip()
                    conc_activating = int(correct_activ)

            # Appending cell data
            difference_dict["Cell #"].append(cell_num)
            difference_dict["Force Diff"].append(force_diff)
            difference_dict["% Activating"].append(conc_activating)

            # Change dir to the file's parent folder
            os.chdir(
                os.path.join(output_dir, working_filepath.parent.name)
            )  # working_filepath.parent.name = "Cell n"

            # Saving filtered data
            full_data_df.to_csv(f"{filename}-filter.csv")
            # plt.plot()

            # Then exit parent dir, go back to root folder
            os.chdir("../")

    # Convert dicts to dfs
    force_df = pd.DataFrame.from_dict(difference_dict)
    thickness_df = pd.DataFrame.from_dict(thickness_dict)

    # Save dfs as excel file
    with pd.ExcelWriter(f"{folder_name.get()}-Results.xlsx") as writer:
        # use to_excel function and specify the sheet_name and index
        # to store the dataframe in specified sheet
        force_df.to_excel(writer, sheet_name="Force Differences", index=False)
        thickness_df.to_excel(writer, sheet_name="Cell Measurements", index=False)

    print("All Done!")
    folder = os.getcwd()

    # Mac/Linux/Windows compatability to open the output folder
    if sys.platform == "win32":
        os.startfile(folder)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, folder])
    sys.exit()


if __name__ == "__main__":
    main()
