"""One big mofo to combine everything I have so far

probably best to have some class object? I don't need to keep the objects, can write them to a file
inputs:

    lambda or lambda range

    material

    for the GRF
        rho 
        rho_porous
        resolution/dpl

        this together gives M 
    
    if not using GRF, it needs a shape or a shapefile?

    number of realisations (how many GRF particles do we want, and then average over these)

    optional:
        normalisation for the matrix?
    
outputs:
    kappa_scat and kappa_abs
    scattering matrix

    would be nice if this looks like the optool output


program needs to do:
if GRF:
    calculate the M needed for the rho and resolution.
    make the GRF particle WITHOUT porosity. get the bounds for extracting.
    make porous and extract particles
    turn GRF file into adda geometry file

then, make optool write the files for n and k. (needs the material for this and the wavelength(grid))
read in n and k for the wavelength grid. also rho for the material will be in here.

run adda with the shapefile.
this gives a matrix and a crosssection (and a log file). want to convert crosssection into kappa. 
Might want to rewrite this into optool style output, so for all lambdas one file.



"""

import argparse
import numpy as np


def make_GRF(rho, porosity=True, rho_por_frac=50, threshold=0.5, threshold_por=0.2):
    pass


if __name__ == "__main__":
    # TODO add description and such
    parser = argparse.ArgumentParser()
    # TODO this needs to be able to take a range. and the types need to make sense?
    parser.add_argument("-l", "--lambda")
    # TODO this must state the order of materials well (or we do separate option for core and mantle like optool)
    parser.add_argument(
        "-m", "--material", help="material(s) of the particle.", nargs="*"
    )
    parser.add_argument(
        "-r", "--rho", help="size of the particle", default=1, type=float, nargs="?"
    )

    parser.add_argument(
        "-dpl",
        "--dpl",
        help="dipoles per lambda, resolution parameter",
        default=16,
        type=int,
        nargs="?",
    )
    args = parser.parse_args()
