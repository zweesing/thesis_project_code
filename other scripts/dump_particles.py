"""dump all geom particles into a singel directory"""

import os
from pathlib import Path


# output directories
output_dir = "GRF_particles_all"

# input files
input_dir = "generating_particles"
particle_files = os.listdir(input_dir)

i = 1
for particle_file in Path("generating_particles").rglob("*.geom"):

    id = f"{i:04d}"
    os.system(f"cp {particle_file} {output_dir}/particle{id}.geom")

    i += 1
