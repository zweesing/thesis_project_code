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
    parser.add_argument("-l", "--wavelength", help="wavelength in micron")
    # mass fraction is required here for separating mantle and core.
    # TODO needs default
    parser.add_argument(
        "-c",
        "--core",
        help="material(s) and mass fractions of the core.",
        nargs="?",
        default="pyr-mg70 0.87 c 0.13",
    )
    # TODO needs default
    parser.add_argument(
        "-m",
        "--mantle",
        help="material(s) and mass fractions of the core.",
        nargs="?",
        default=None,
    )
    # TODO needs default
    parser.add_argument("-p", "--porosity", help="porosity volume fraction")
    # TODO size range as in optool
    parser.add_argument(
        "-a", "--size", help="size of the particle", default=1, type=float, nargs="?"
    )
    parser.add_argument("-o", "--output", help="output folder", default="output")

    args = parser.parse_args()

    # unpack
    lam_micron = args.wavelength
    # materials and mass fractions should be able to be parsed into optool for mixing as is
    core_mat = args.core
    mantle_bool = bool(args.mantle)
    if mantle_bool:
        mantle_mat = args.mantle
    porosity = args.porosity
    size = args.size
    output_folder = "./" + args.output

    # for testing
    lam_micron = "1"
    # mantle_mat = "h2o-w"
    mantle_mat = "pyr-mg70 0.87 c 0.13"
    mantle_bool = True
    porosity = 0
    size_micron = 0.1
    size = size_micron * micron

    # do I need this?
    # parser.add_argument(
    #     "-dpl",
    #     "--dpl",
    #     help="dipoles per lambda, resolution parameter",
    #     default=16,
    #     type=int,
    #     nargs="?",
    # )
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

        particle_volumes_dip.append(volumes_dipoles)
    # ------------------------------------------------------------------------------------- #
    # get n,k from optool
    # ------------------------------------------------------------------------------------- #

    # --> needs material and lambda
    # --> gives arrays of n,k
    # needs to run for both core and mantle
    core_nk, lam_arr, rho_core = get_nk(lam_micron, core_mat)
    if mantle_bool:
        mantle_nk, _, rho_mantle = get_nk(lam_micron, mantle_mat)
    # ------------------------------------------------------------------------------------- #

    # call adda
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
            print(run_folder)
            os.system(
                f"adda -shape read {geom_file} -eq_rad {a_micron} -lambda {lam_micron} -m {nc} {kc} {nm} {km} -orient avg -dir {run_folder}"
            )

    # ------------------------------------------------------------------------------------- #
    # convert and calculate output for each realisation
    # ------------------------------------------------------------------------------------- #

    # first trying for one realisation
    ig = 0
    adda_folders = os.listdir(f"{output_folder}/adda_runs_particle{ig}")
    adda_folders.sort()
    nlam = len(adda_folders)

    # prepare arrays
    Cexts = np.zeros(nlam)
    Qext = np.zeros(nlam)
    Cabs = np.zeros(nlam)
    Qabs = np.zeros(nlam)

    for i, a_folder in enumerate(adda_folders):
        try:
            f = open(f"{output_folder}/adda_runs_particle{ig}/{a_folder}/CrossSec", "r")

            lines = f.readlines()
            Cexts[i] = float(lines[0].split()[-1]) * micron**2
            Qext[i] = float(lines[1].split()[-1]) * micron**2
            Cabs[i] = float(lines[2].split()[-1]) * micron**2
            Qabs[i] = float(lines[3].split()[-1]) * micron**2

            f.close()
        except FileNotFoundError:
            Cexts[i] = Qext[i] = Cabs[i] = Qabs[i] = np.nan

    # convert to kappas. we need dipole size from the log files
    # all dipoles are the same size (for one particle) so we only need to read it once
    f = open(f"{output_folder}/adda_runs_particle{ig}/{adda_folders[0]}/log")
    line = f.readline()
    while not line.startswith("Dipole size"):
        line = f.readline()

    dipole_size_micron = float(line.split()[-2])  # micron
    dipole_size = dipole_size_micron * micron

    # dipoles are cuboids so the mass is amount of dipoles x dipole size^3 x rho
    volume_core_dip, volume_mantle_dip = particle_volumes_dip[ig]

    core_volume = volume_core_dip * dipole_size**3
    mantle_volume = volume_mantle_dip * dipole_size**3

    core_mass = core_volume * rho_core
    mantle_mass = mantle_volume * rho_mantle
    particle_mass = core_mass + mantle_mass

    print(
        f"\nvolume core: {core_volume} cm3\nvolume mantle: {mantle_volume} cm3\nvolume total: {core_volume+mantle_volume} cm3"
    )
    print(f"densities: {rho_core, rho_mantle}")
    print("\nmass: ", particle_mass, " gram")

    k_ext = Cexts[ig] / particle_mass
    k_abs = Cabs[ig] / particle_mass
    print("kappa abs=", k_abs, " cm2/g\nkappa sca=", k_ext - k_abs, " cm2/g")
    # ------------------------------------------------------------------------------------- #
    # plot for now?
    # ------------------------------------------------------------------------------------- #
