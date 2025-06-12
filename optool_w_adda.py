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
import sys

# if a value in in something other than CGS, multiply it by the conversion
micron = 1e-4


def get_nk(wavelength, material):
    """get refractive index for specified material(s) from optool. Material can be
    the entire string including the mass fractions, in which case optool will mix them.

    Args:
        wavelength (float or str): wavelength in micron. Can be a single value or a lmin lmax and number of points
        material (str): material name(s) or shorthand and mass fractions if multiple.

    Returns:
        2xN arr of n,k values, 1xN arr of wavelength grid, density of materials
    """
    # TODO output folder needs to be a temp
    # possibly specify a single size so optool doesnt calculate a range (optimisation)
    # optool bug, does not write to correct folder
    os.system(f"cd {output_folder} && optool -c {material} -l {wavelength} -mie -w ")

    # read in data
    # TODO i dont need all this information so this can be shorter I think
    rfile = open(f"{output_folder}/optool_mix.lnk", "r")

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
    return nk_arr, lamarr, rho


if __name__ == "__main__":

    # TODO add description and such
    parser = argparse.ArgumentParser()
    # TODO this needs to be able to take a range, same as optool
    # possibly easiest to do with interpreting the input as a string?
    parser.add_argument(
        "-l", "--wavelength", default="1", nargs="*", help="wavelength in micron"
    )
    # mass fraction is required here for separating mantle and core.
    parser.add_argument(
        "-c",
        "--core",
        help="material(s) and mass fractions of the core.",
        nargs="?",
        default="pyr-mg70 0.87 c 0.13",
    )
    parser.add_argument(
        "-m",
        "--mantle",
        help="material(s) and mass fractions of the mantle.",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "-p",
        "--porosity",
        default=0,
        type=float,
        nargs="?",
        help="porosity volume fraction",
    )
    # TODO size range as in optool
    parser.add_argument(
        "-a",
        "--size",
        help="size of the particle in micron",
        default=0.1,
        type=float,
        nargs="?",
    )
    parser.add_argument("-o", "--output", help="output folder", default="output")

    args = parser.parse_args()

    # unpack
    lam_range_micron = " ".join(
        args.wavelength
    )  # this needs to be a string with 1 or 3 arguments

    # materials and mass fractions should be able to be parsed into optool for mixing as is
    core_mat = args.core

    mantle_bool = bool(args.mantle)

    if mantle_bool:
        mantle_mat = args.mantle
    # for testing, keeping this in. the argument works but this is better for now
    mantle_mat = "h2o-w"
    mantle_bool = True

    porosity = args.porosity
    size_micron = args.size
    output_folder = "./" + args.output

    size = size_micron * micron

    # ------------------------------------------------------------------------------------- #
    # make output folder (idk if i want this or if i want it to save to the folder regardless of if its empty)
    # ------------------------------------------------------------------------------------- #
    if os.path.isdir(output_folder):
        nofolder = True
        counter = 1
        newfoldername = output_folder + str(counter)

        while nofolder:
            try:
                os.mkdir(newfoldername)
                nofolder = False
                output_folder = newfoldername

            except FileExistsError:
                counter += 1
                newfoldername = output_folder + str(counter)
    else:
        os.mkdir(output_folder)

    # ------------------------------------------------------------------------------------- #
    # find matching GRF particles TODO
    # ------------------------------------------------------------------------------------- #
    particles = os.listdir("GRF_particles")
    particles = ["GRF_particles/" + x for x in particles]
    # in [core, mantle] format. in #dipoles units
    particle_volumes_dip = []
    # get the volumes. first line is general description and
    # second (and third) line are volumes?
    for particle in particles:
        file = open(particle, "r")
        line = file.readline()
        # comments
        volumes_dipoles = []
        line = file.readline()
        while line.startswith("# Volume"):

            dipoles = int(line.split()[-1])
            volumes_dipoles.append(dipoles)
            line = file.readline()
        file.close()

        particle_volumes_dip.append(volumes_dipoles)
    # ------------------------------------------------------------------------------------- #
    # get n,k from optool
    # ------------------------------------------------------------------------------------- #

    # --> needs material and lambda
    # --> gives arrays of n,k
    # needs to run for both core and mantle
    core_nk, lam_arr, rho_core = get_nk(lam_range_micron, core_mat)
    if mantle_bool:
        mantle_nk, _, rho_mantle = get_nk(lam_range_micron, mantle_mat)
    # ------------------------------------------------------------------------------------- #
    # call adda
    # ------------------------------------------------------------------------------------- #

    # --> needs size (equivalent radius), wavelength, nk, geom file
    # --> gives matrix and crosssection

    # run per wavelength for whole particle. if multiple realisations, run for those
    # we also need the volumes
    # for all realisations
    for ig, geom_file in enumerate(particles):
        current_folder = output_folder + f"/adda_runs_particle{ig}"
        os.mkdir(current_folder)
        # adda needs this file for orientational averaging
        # this might not work on windows?
        # os.system(f"cp avg_params.dat {current_folder}/avg_params.dat")
        # for wavelength grid, needs to run multiple times
        for i, lam in enumerate(lam_arr):

            nc, kc = core_nk[i]
            if mantle_bool:
                nm, km = mantle_nk[i]
            else:
                nm = km = ""

            # convert back to micron
            a_micron = size / micron
            lam_micron = lam / micron
            run_folder = (
                current_folder + "/run" + str(i).zfill(4) + "lam" + str(lam_micron)
            )
            os.system(
                f"adda -shape read {geom_file} -eq_rad {a_micron} -lambda {lam_micron} -m {nc} {kc} {nm} {km} -orient avg -dir {run_folder}"
            )

    # ------------------------------------------------------------------------------------- #
    # read in dipole size to calculate mass
    # read in adda C and Q outputs into 3d array for each particle, each wavelength, 4 results
    # read in matrices + apply RADMC convention immediately
    # ------------------------------------------------------------------------------------- #

    # do this for each realisation and average
    npart = len(particles)
    nlam = len(lam_arr)
    particle_masses = np.zeros(npart)
    # we have a 4x4 matrix, for each wavelength, for each particle
    matrices_RADMC_arr = np.zeros((npart, nlam, 181, 4, 4))
    matrices_unnorm_arr = np.zeros((npart, nlam, 181, 4, 4))  # just for testing

    # for each lambda [Cext Qext Cabs Qabs], for each particle
    # so the order is arr[particle, lambda, C/Q]
    C_and_Q_arr = np.zeros((npart, nlam, 4))

    for ig in range(npart):

        adda_folders = os.listdir(f"{output_folder}/adda_runs_particle{ig}")
        adda_folders.sort()

        # calculate particle mass to convert to opacity
        # all dipoles are the same size (for one particle) so we only need to read it once
        f = open(f"{output_folder}/adda_runs_particle{ig}/{adda_folders[0]}/log")
        line = f.readline()
        while not line.startswith("Dipole size"):
            line = f.readline()
        f.close()

        dipole_size_micron = float(line.split()[-2])  # micron
        dipole_size = dipole_size_micron * micron

        # dipoles are cuboids so the mass is amount of dipoles x dipole size^3 x rho
        volume_core_dip, volume_mantle_dip = particle_volumes_dip[ig]

        core_volume = volume_core_dip * dipole_size**3
        mantle_volume = volume_mantle_dip * dipole_size**3

        core_mass = core_volume * rho_core
        mantle_mass = mantle_volume * rho_mantle
        particle_mass = core_mass + mantle_mass
        particle_masses[ig] = particle_mass

        for il, a_folder in enumerate(adda_folders):
            try:
                f = open(
                    f"{output_folder}/adda_runs_particle{ig}/{a_folder}/CrossSec", "r"
                )

                lines = f.readlines()

                C_and_Q_arr[ig, il, 0] = float(lines[0].split()[-1]) * micron**2
                C_and_Q_arr[ig, il, 1] = float(lines[1].split()[-1]) * micron**2
                C_and_Q_arr[ig, il, 2] = float(lines[2].split()[-1]) * micron**2
                C_and_Q_arr[ig, il, 3] = float(lines[3].split()[-1]) * micron**2

                f.close()
            except FileNotFoundError:
                C_and_Q_arr[ig, il, :] = np.array([np.nan, np.nan, np.nan, np.nan])

            # matrix
            f = open(f"{output_folder}/adda_runs_particle{ig}/{a_folder}/mueller", "r")
            f.readline()  # columnnames
            matrices = np.zeros((181, 4, 4))
            line = f.readline()

            while line:
                line_split = line.split()
                # this is the angle but it also works as an index
                ia = int(float(line_split[0]))

                # remove the angle
                line_split.pop(0)

                # make numbers.
                elements = [float(el) for el in line_split]
                # reshape and save the matrix
                matrix = np.array(elements).reshape((4, 4))

                matrices[ia] = matrix

                line = f.readline()

            f.close()
            # apply RADMC convention and save
            # first, apply RADMC convention, which is lamda^2 /(4 pi^2 m)
            # matrices_RADMC_arr[ig, il] = (
            #     matrices * lam_arr[il] ** 2 / (4 * np.pi**2 * particle_mass)
            # )
            matrices_unnorm_arr[ig, il] = matrices
            # sanity check. 1,1-element of all angles should add up to kappa_sca/(4pi)
            # print(
            #     "1,1-element sum (for all 360 angles?), /4pi:",
            #     (
            #         matrices_RADMC_arr[ig, il, :, 0, 0].sum()
            #         # + matrices_RADMC_arr[ig, il, :, 0, 0][1:-1].sum()
            #     ),
            # )

    # ------------------------------------------------------------------------------------- #
    # average results, weighted by mass
    # ------------------------------------------------------------------------------------- #

    # for each wavelength, six values [Cext Qext Cabs Qabs kext kabs]
    results_arr = np.zeros((nlam, 6))
    for i in range(nlam):
        Cext_arr = C_and_Q_arr[:, i, 0]  # array for all particles
        Cabs_arr = C_and_Q_arr[:, i, 2]

        Cext = (Cext_arr * particle_masses).sum() / particle_masses.sum()
        # Qext becasue of orientational averaging,this is just C / 'spherical cross section'
        Qext = Cext / (np.pi * size**2)

        Cabs = (Cabs_arr * particle_masses).sum() / particle_masses.sum()
        Qabs = Cabs / (np.pi * size**2)

        # the particle weight of the weighted average cancels the weight of the kappa conversion
        kext = Cext_arr.sum() / particle_masses.sum()
        kabs = Cabs_arr.sum() / particle_masses.sum()
        print("ksca/4pi:", (kext - kabs) / (4 * np.pi))

        results_arr[i] = np.array([Cext, Qext, Cabs, Qabs, kext, kabs])

    # matrix
    # try to get hovenier and test it
    matrices_unnorm_arr[0, 0, :, :, :] = matrices_unnorm_arr[0, 0, :, :, :] * (
        lam_arr[0] ** 2 / (np.pi * (Cext - Cabs))
    )
    print("sum of 1,1 elements", matrices_unnorm_arr[0, 0, :, 0, 0].sum())
    print(matrices_unnorm_arr)
    print("\n masses:")

    for p in particle_masses:

        print(p)
    # ------------------------------------------------------------------------------------- #
    # write output files
    # ------------------------------------------------------------------------------------- #
    output_filename = output_folder + "results.dat"
    wfile = open(output_filename, "w")
    # header
    wfile.write(
        "#============================================================================"
    )
    # credits
    wfile.write("# computed by me yay")

    # parameters. make nice with spacing
    wfile.write("# Parameters:")
    # lambda
    wfile.write(
        f"#   lmin [um]= {lam_arr[0]:10.3f} lmax [um]= {lam_arr[-1]:10.3f}  nlam= {nlam:4.3g}     nang=   181"
    )
    # other stuff idk yet
    wfile.write(
        f"#   porosity =      {args.porosity:5.3f}    a [um]= {size_micron:10.3f}"
    )

    # composition
    wfile.write("# Composition:")
    #  Where   mfrac  rho   Material
    #  -----   -----  ----  -----------------------------------------------------
    #  core    1.000  0.92  h2o-w
    #  - - -   - - -  -  -  - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #  grain   1.000  0.92  mixture of  1 materials
    # ----------------------------------------------------------------------------
    wfile.write("#  Where   mfrac  rho   Material")
    wfile.write(
        "#  -----   -----  ----  -----------------------------------------------------"
    )
    # TODO figure these out. one line for each core material and a mixture result for
    # core and mantle
    cmatstring = ""
    wfile.write(f"#  core    {0:5.3f}  {0:3.2f}  {cmatstring}")
    wfile.write(
        "#  -----   -----  ----  -----------------------------------------------------"
    )
    mmatstring = ""
    wfile.write(f"#  mantle  {0:5.3f}  {0:3.2f}  {mmatstring}")

    wfile.write(
        "#  -----   -----  ----  -----------------------------------------------------"
    )
    wfile.write(
        "#============================================================================"
    )
    # description of the data section
    wfile.write(
        "#============================================================================"
    )
    # opacites etc
    # there is some information that is needed here. optool does format number
    # and number of lambdas
    wfile.write()
    for i in range(nlam):
        pass
        # write the lambda grid and the opacities
        # this means 15 wide with 5 decimals after the dot
        # wfile.write(' %15.5e %15.5e %15.5e %15.5e\n' % (s.lam[i],s.kabs[0,i],s.ksca[0,i],s.gsca[0,i]))
    wfile.close()
