"""Written using Python 3.12"""

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox

import sys
import os
from pathlib import Path

import pandas as pd
import random
import string
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector


from scipy.ndimage import gaussian_filter
import ctypes


def main():
    """
    This automates the filtering of single cell mechanics files

    """
    # For higher resolution screens (just personal thing)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

    def select_files(event=None):
        filetypes = (("All Files", "*.*"),)

        global filepath

        filepath = fd.askopenfilenames(
            title="Open files", initialdir=r"C:\Users\Desktop", filetypes=filetypes
        )

        root.destroy()

    def onselect(xmin, xmax):
        global counter

        imin, imax = int(xmin + 0.5), int(xmax + 0.5)
        if imax < imin:
            imin, imax = imax, imin
        if imax - imin > 0:
            selected_data = data[imin:imax]
            average = selected_data.mean()
            averages.append(average)

            if counter == 1:
                ax1.cla()
                ax1.plot(data, "-")
                ax1.set_title(f"Calculate Difference of Averages")
                plt.draw()
                counter = 0

            # After two selections, calculate the difference and update the display
            if len(averages) >= 2:
                diff = abs(averages[0] - averages[1])
                diff = diff * 1000
                ax2.cla()  # Clear the ax2 for text display
                ax2.text(
                    0.5,
                    0.5,
                    f"{filename} Difference: {diff:.3f}µN",
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=15,
                    transform=ax2.transAxes,
                )
                ax2.set_xticks([])
                ax2.set_yticks([])
                plt.draw()  # Redraw to update the display
                averages.clear()  # Reset for next selections
                counter = 1 - counter

    # Modify the SpanSelector to color the selections
    def onselect_red_blue(xmin, xmax):
        # Call the original onselect function to handle logic
        onselect(xmin, xmax)
        # Color the regions: Red for the first, Blue for the second
        color = "red" if len(averages) == 1 else "blue"
        ax1.axvspan(xmin, xmax, color=color, alpha=0.5)

    filtering_amount = 10

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
    new_dir = current_dir / folder_name.get()

    try:
        os.mkdir(new_dir)
    except FileExistsError:
        # If it already exists, adds 5 random digits to the end
        new_dir = current_dir / (
            folder_name.get()
            + "-"
            + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        )
        os.mkdir(new_dir)
        print("Folder name already existed, made copy instead. Everybody gets one.")

    os.chdir(new_dir)
    first = True

    for file in filepath:
        filename = os.path.basename(file)
        if ".dat" in filename:
            filename = filename[:-4]

        # TBH I got this from stackoverflow
        DAT_df = pd.DataFrame([i.strip().split() for i in open(file).readlines()])

        # Finding Thickness
        comments = DAT_df.loc[DAT_df[0] == "Comment:"].index.to_list()

        thickness = (
            DAT_df.iloc[comments[0] + 1 : comments[0] + 3, [0, 1]]
            .reset_index(drop=True)
            .transpose()
        )
        thickness.columns = thickness.iloc[0]
        thickness = thickness[1:]
        # This is finding where the parameters start and end
        # Looks for "time", where the second and third instance are the boundries for the timings
        parameter_locs = DAT_df.loc[DAT_df[0] == "Time"].index.tolist()
        parameter_locs[2] -= 2

        # Preparing the data to be analyzed
        column_names = [
            "Time",
            "Lin",
            "Fin",
            "SL",
        ]

        # We only want time (0), Lin (1), Fin (3), and SL (7)
        fiber_data = pd.DataFrame(DAT_df.iloc[(parameter_locs[2] + 3) :, [0, 1, 3, 7]])
        fiber_data.reset_index(drop=True, inplace=True)
        # fiber_data.drop(fiber_data.columns[9:], axis=1, inplace=True)
        fiber_data.columns = column_names

        # At this point in the script, the data is separated, indexes are reset,
        # the column names have been changed, and we are ready to do some math (yaaaayyy)
        # print(fiber_data)
        # print(combined_timing_df)
        # print(fiber_data.tail())

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

        full_data_df["Fin"] = gaussian_filter(
            full_data_df["Fin"], filtering_strength.get()
        )

        # Calculate baseline and subtract
        # base = peakutils.baseline(full_data_df["Fin"], 2)
        # full_data_df["Fin"] = full_data_df["Fin"] - base

        # plt.plot(fiber_data.Time, fiber_data.Fin)
        # plt.plot(full_data_df.Time, full_data_df.Fin)
        # plt.show()

        # Show the string representation in a messagebox.
        # You might want to limit the size of the DataFrame to avoid creating an oversized messagebox.
        if first:
            thickness_string = thickness.to_markdown(
                index=False,
                tablefmt="pipe",
                colalign=["center"] * len(thickness.columns),
            )
            thickness_string = thickness_string.split("\n")
            thickness_string.pop(1)
            thickness_string = "\n".join(thickness_string)
            messagebox.showinfo("Cell Dimensions", thickness_string)

            first = False

        data = full_data_df["Fin"].values

        fig, (ax1, ax2) = plt.subplots(2, figsize=(13, 7))
        (line,) = ax1.plot(data, "-")

        # Making the window appear in the same spot everytime
        window_position = [10, 10]
        manager = plt.get_current_fig_manager()
        manager.window.wm_geometry(f"+{window_position[0]}+{window_position[1]}")

        # Set up the SpanSelector with the new callback
        span = SpanSelector(
            ax1,
            onselect_red_blue,
            "horizontal",
            useblit=True,
            props=dict(alpha=0.5, facecolor="tab:blue"),
        )

        ax1.set_title(f"Calculate Difference of Averages {filename}")
        plt.show()

        full_data_df.to_csv(f"{filename}-filter_baseline.csv")
        plt.close()

        # For comparison between filtered and unfiltered
        # I considered making a folder for these, but I think it would just be a waste
        # fiber_data.to_csv(f"{filename[:-4]}-unfiltered.csv")

    print("All Done!")
    folder = os.getcwd()
    os.startfile(folder)
    sys.exit()


if __name__ == "__main__":
    averages = []
    counter = 0
    main()
