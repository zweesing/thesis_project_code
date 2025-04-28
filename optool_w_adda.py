"""One big mofo to combine everything I have so far

inputs:

    lambda or lambda range

    size of particles (or range)

    volume fraction porosity

    mantle and core materials mass fraction -> gives mantle volume fraction

    n realisations (foraveraging)
    n rotations (for averaging)



    optional:
        normalisation for the matrix

outputs:
    kappa_scat and kappa_abs
    scattering matrix

    would be nice if this looks like the optool output


program needs to do:
if GRF:
    generate GRF for specified resolution needed (depending on wavelength)
    turn GRF file into adda geometry file

make optool write the files for n and k. (needs the material for this and the wavelength(grid))
for both the mantle and the core (mix per domain if multiple materials)

rho for the material will be in these files. Calculate which particles are needed by getting a dipole ratio
to match with the porosity fraction to select particle(s)

read in n and k for the wavelength grid

run adda with the shapefile(s).

this gives a matrix and a crosssection (and a log file). want to convert crosssection into kappa.
Want to rewrite this into optool style output, so for all lambdas one file.



"""

import argparse
import numpy as np
import os

# if a value in in something other than CGS, multiply it by the conversion
micron = 1e-4


def get_nk(wavelength, materials):
    """get refractive index for specified material(s) from optool. Material can be
    the entire string including the mass fractions.

    Args:
        wavelength (arr or float): wavelength in micron.can be a single wavelength or a range
        material (str): material name(s) or shorthand and mass fractions if multiple.
    """
    # TODO
    # possibly specify a single size so optool doesnt calculate a range (optimisation)
    os.system(f"optool -c {material} -l {wavelength} -mie -w")

    # read in data
    # TODO i dont need all this information so this can be shorter I think
    rfile = open("optool_mix.lnk", "r")

    dum = rfile.readline()
    header = ""

    while dum.strip()[0] == "#":
        header = header + dum
        dum = rfile.readline()

    # number of lambdas and rho
    while len(dum.strip()) < 1:
        dum = rfile.readline()  # skip any empty lines
    nlam = int(dum.split()[0])
    rho = float(dum.split()[1])

    lamarr = np.zeros(nlam)
    narr = np.zeros(nlam)
    karr = np.zeros(nlam)

    # Read the refractive indices
    dum = rfile.readline()
    while len(dum.strip()) < 1:
        dum = rfile.readline()  # skip any empty lines
    for ilam in range(nlam):
        dum = dum.split()
        lamarr[ilam] = float(dum[0]) * micron
        narr[ilam] = float(dum[1])  # refractive indices
        karr[ilam] = float(dum[2])

        dum = rfile.readline()

    rfile.close()

    nk_arr = np.column_stack((narr, karr))
    # TODO I also probably want to save the rho's for converting between volume and mass
    return nk_arr


def run_adda(size, wavelength, n, k, geom):
    # TODO
    # run adda for one wavelength
    a_micron = size * micron
    lam_micron = wavelength * micron
    os.system(
        f"adda -shape read {geom} -eq_rad {a_micron} -lambda {lam_micron} -m {n} {k}"
    )

    # this writes out into a folder called run001 etc


if __name__ == "__main__":

    # leaving the arguments for now

    # TODO add description and such
    parser = argparse.ArgumentParser()
    # TODO this needs to be able to take a range. and the types need to make sense?
    parser.add_argument("-l", "--lambda")
    # mass fraction is required here for separating mantle and core.
    parser.add_argument(
        "-c", "--core", help="material(s) and mass fractions of the core.", nargs="*"
    )
    parser.add_argument(
        "-m", "--mantle", help="material(s) and mass fractions of the core.", nargs="*"
    )
    parser.add_argument("-p", "--porosity", help="porosity volume fraction")
    # TODO size range as in optool
    parser.add_argument(
        "-a", "--size", help="size of the particle", default=1, type=float, nargs="?"
    )

    # do I need this?
    # parser.add_argument(
    #     "-dpl",
    #     "--dpl",
    #     help="dipoles per lambda, resolution parameter",
    #     default=16,
    #     type=int,
    #     nargs="?",
    # )
    args = parser.parse_args()

    # ------------------------------------------------------------------------------------- #
    # ------------------------------------------------------------------------------------- #

    # generate GRF's
    # --> needs size and lambda for minimum dpl (not tested)
    # --> gives geom file

    # ------------------------------------------------------------------------------------- #

    # get n,k from optool
    # --> needs material and lambda
    # --> gives arrays of n,k
    # can run multiple times for the different materials
    nkarrs = []

    for material in materials:
        nk_arr = get_nk(wavelength, material)
        nkarrs.append(nk_arr)

    # ------------------------------------------------------------------------------------- #

    # call adda
    # --> needs size (equivalent radius), wavelength, nk, geom file
    # --> gives matrix and crosssections
    # for wavelength grid, needs to run multiple times

    # ------------------------------------------------------------------------------------- #

    # convert and write output.
    # potentially plot
