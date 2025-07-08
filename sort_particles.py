"""read in particles that have been deemed acceptable and sort them on porosity value
and mantle volume  percentage"""

import os

# output directories
output_dir = "GRF_particles"

# input files
particles_dir = ""
particle_files = os.listdir(particles_dir)

for particle_file in particle_files:
    rf = open(particles_dir + "/" + particle_file)
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

    rf.close()

    mantle_frac = mantle_volume / (mantle_volume + core_volume)

    # sort it into a folder, two parameters
    # porfrac in ranges of .1
    # mantlefrac in ranges of .1
    if mantle_frac:
        pass
