"""read in particles recursively from input_dir and sort them on porosity
and mantle volume percentage in subdirectories in output_dir"""

import os
from pathlib import Path
from numpy import floor
import sys

# output directories
output_dir = "GRF_particles"

# input files
input_dir = "generating_particles"
particle_files = os.listdir(input_dir)

i = 1
mantle_frac_list = []
por_frac_list = []
for particle_file in Path("generating_particles").rglob("*.geom"):

    rf = open(particle_file)
    # read in relevant header data
    mantle_volume = 0  # in case theres no mantle
    line = rf.readline()
    while line.startswith("#"):
        if line.startswith("# porosity_frac"):
            porosity_frac = float(line.split()[-1])
        elif line.startswith("# Volume1"):
            core_volume = float(line.split()[-1])
        elif line.startswith("# Volume2"):
            mantle_volume = float(line.split()[-1])
        line = rf.readline()

    rf.close()

    mantle_frac = mantle_volume / (mantle_volume + core_volume)
    mantle_frac_list.append(mantle_frac)
    por_frac_list.append(porosity_frac)
    # sort it into a folder, two parameters
    # porfrac in ranges of .1
    # mantlefrac in ranges of .1
    id = f"{i:04d}"
    mantle_bin = int(floor(mantle_frac * 10 + 0.5) * 10)
    porosity_bin = int(floor(porosity_frac * 10 + 0.5) * 10)

    output_subdir = "mantle_" + str(mantle_bin) + "por_" + str(porosity_bin)
    if not os.path.isdir(output_dir + "/" + output_subdir):
        os.mkdir(output_dir + "/" + output_subdir)

    os.system(f"cp {particle_file} {output_dir}/{output_subdir}/particle{id}.geom")

    i += 1
