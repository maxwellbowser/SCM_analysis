# Single Cell Mechanics Analysis (WIP)
 <a href = " https://www.python.org/downloads/release/python-3110/ " ><img alt="Python 3.11" src="https://img.shields.io/badge/version-Python 3.11-forestgreen.svg"></a> 
 <a href = "https://github.com/maxwellbowser/SCM_analysis/blob/main/LICENSE" > <img alt="MIT License" src="https://img.shields.io/badge/license-MIT-blue"></a>  <a href="https://github.com/psf/black"> <img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

## Summary:
Software for analyzing .DAT files from Single Cell Mechanics (SCM)

I'm creating this repository as a User Guide for future people in the Gregorio Lab, or for anyone who is doing SCM and may find this useful.

## Setup Specifications
* Aurora ASI600A (Software version)
* Linux KDE Shell, Ubuntu Kernel

## User Guide
There are 2 scripts in this repo, an automated version of the SCM analysis, and a more manual version.

## Manual Version:
In the manual version, you select all of the force recording files done for a single cell (should be .dat files), then are shown the force traces one by one. 

When the first file is opened, you are shown the cell dimensions (Figure 1), provided you write them in the Aurora Setup notes tab as:  
**Comment: Mouse C843 Cell 1**  
**Width 0.0316**  
**Thick 0.0158**

The above numbers don't need to match, only the layout of the text, where it **begins with "Comment:" and "Width" & "Thick" following it.**

<div align = "center">
<img src="README_files/image.png" alt="pop up window showing cell thickness and width" width="200"/>
</div>

*Figure 1: Example of cell size pop up.*


After hitting "OK" on this pop up, you will see the first force trace (Figure 2).

![force trace of cell, starting with a step function](README_files/image-2.png)  
*Figure 2: Trace of filtered cell force.*

To calculate the difference between 2 areas, **you simply click and drag on the graph to select one area, then the next**. These points in these two areas are then averaged and displayed in the bottom panel (Figure 3)!


![selecting area on force trace](<README_files/SM_GIF better.gif>)  
*Figure 3: Gif of selecting cell force trace.*


**You can then write/copy down the force difference onto the provided Excel sheet**. The "72" shown in this example is simply the name of the file. So, for example, if your files are named "pCa point 6.75.dat", the text would read "pCa point 6.75 Difference: 5.000µN"


To continue onto the next selected file, you close the window, at which point the next file is opened (Figure 4).

![SCM analysis cycling to next file](<README_files/SC_Gif CLosing.gif>)  
*Figure 4: Gif of closing cell force trace, to cycle to next file.*  

After doing all files, the program closes and opens a folder containing CSVs of the filtered forces.

## Automated Version:

The automated version of this analysis is **much** faster, however it only will work correctly if the files are correctly formatted. This is why I reccomend doing the by-hand analysis first, to have something to compare to.

The automated version does the same basic calculation as the manual one. The order of operations for each file is:
1. **Averages the first 200 ms**   

2. **Waits 40 ms**
3. **Averages the next 5 ms** 
4. **Calculates the difference between them**

This difference is saved, along with the cell widths.

**IMPORTANT:** Rather than selecting all of the raw files, you select one folder containing all of the cell recordings.

Our file naming convention is that the file names contain the % of activating solution in the mixture, with 100% and 0% being named differently, as "Passive" or "Active".

From this, the pCa chart in the Excel file has all of the % mixtures possible, and the free Ca++ associated (calculated using [this calculator](https://somapp.ucdmc.ucdavis.edu/pharmacology/bers/maxchelator/CaMgATPEGTA-TS.htm) hosted by UCDavis). 
## Insert already calculated values & Table

#### Folders should be formatted as:
```bash
|-- Folder_to_Select
    |-- Cell 1
    |   |-- Passive.dat
    |   |-- 80.dat
    |   |-- ...
    |   |-- Active.dat
    |
    |-- Cell 2
    |   |-- Passive.dat
    |   |-- 80.dat
    |   |-- ...
    |   |-- Active.dat
    |
    |-- Cell 3
    |   |-- Passive.dat
    |   |-- 80.dat
    |   |-- ...
    |   |-- Active.dat  
    |
    |-- ...
    |-- Cell n
    |   |-- Passive.dat
    |   |-- 80.dat
    |   |-- ...
    |   |-- Active.dat

```

After selecting and running, the output file contains 2 sheets. The first sheet (Figure 5) has columns for the Cell #, the % of activating solution (derived from the file name), and the forces. 

<div>
<img src="README_files/image-3.png"> 
</div>

*Figure 5: Automated SCM analysis output Sheet 1, calculated forces and Ca++ concentration.* 

The second sheet (Figure 6) has the cell dimensions, provided that they are entered according the Aurora Setup Notes convention mentioned in [Manual Version](#manual-version).

<div>
<img src="README_files/image-4.png"> 
</div>



*Figure 6: Automated SCM analysis output Sheet 2, cell dimensions.*

