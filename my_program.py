#!/usr/bin/python3
"""

inputs:

    lambda or lambda range

    size of particle

    volume fraction porosity

    mantle and core materials and mass fraction -> gives mantle volume fraction

    n realisations (foraveraging)



    optional (TODO?):
        normalisation for the matrix

outputs:
    all scattering quantities and scattering matrix in one file (results.dat)
    DuCKLinG input q curve (ducky.dat)



TODO functionality to add:
    spherical particles for testing

    write descriptions for arguments

    input lnk files instead of arguments (list of nk instead of optool)

    make it a commandline tool with a setup.py etc

    proper errors and exceptions

    delete optool files when I'm done, or have an option to keep them


TODO fixes still needed:

    think there should be more particles in that high mantle fraction range maybe.

    0 mantle particles must not get mantle particles

    test missing adda output (maybe important for multicore). what happens then? it should skip that datapoint

    if multicore fucks up, create near error message and exit (or let that one be skipped)





"""

import argparse
import numpy as np
import os
import sys
import time
import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import shutil

# if a value in in something other than CGS, multiply it by the conversion
micron = 1e-4
particle_folder = "GRF_particles_all"


def make_output_dir(output_dir):
    """Create an output directory. use a numbered suffix if requested name is already in use.

    Args:
        output_dir (str): name of output directory

    Returns:
        str: name of output directory
    """

    # check if name already in use. Generate a new unique name
    if os.path.isdir(output_dir):
        nodir = True
        counter = 1
        new_dir = output_dir + f"{counter:03d}"

        while nodir:
            try:
                os.mkdir(new_dir)
                nodir = False
                return new_dir

            except FileExistsError:
                counter += 1
                new_dir = output_dir + f"{counter:03d}"
    else:
        os.mkdir(output_dir)
        return output_dir


def get_nk(wavelength, material, output_dir, suffix=""):
    """Get refractive index for specified material(s) from optool. Material can be
    the entire string including the mass fractions, in which case optool will mix them.
    Renames the optool_mix.lnk file and returns the full path to it.

    Args:
        wavelength (float or str): wavelength in micron. Can be a single value or a lmin lmax and number of points
        material (str): material name(s) or shorthand and mass fractions if multiple.
        suffix (str): suffix for renaming optool output file. Defaults to an empty string.

    Returns:
        path to lnk file
    """
    # optool -err frag outputs an exit code. linux returns a 16-bit number that does:
    # "a 16-bit number, whose low byte is the signal number that killed the process,
    # and whose high byte is the exit status (if the signal number is zero)"
    # so I get the exit code of optool back with os.WEXITSTATUS
    result = os.system(
        f"optool -c {material} -l {wavelength} -a 0.1 -w -q -o {output_dir} -err > {output_dir}/optool_out.log 2>&1"
    )
    if os.WEXITSTATUS(result) != 0:
        # reproduce the error without the backtrace
        with open(f"{output_dir}/optool_out.log", "r") as f:
            sys.stderr.write(f.readlines()[-1])

        # probably better to raise my own error here. Optool error or adda error for example
        sys.exit(1)

    # rename file to differentiate core and mantle
    new_name = f"{output_dir}/optool_mix_{suffix}.lnk"
    shutil.move(f"{output_dir}/optool_mix.lnk", new_name)

    # remove other optool files
    os.remove(f"{output_dir}/optool_lam.dat")
    os.remove(f"{output_dir}/optool_sd.dat")

    return new_name


def read_nk(path):
    """Read in an optool generated lnk file.

    Args:
        path (str): path to lnk file

    Returns:
        2xN arr of nk values, 1xN arr of wavelength grid, density of (mixed) material(s)
    """
    # read in data
    rfile = open(path)

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


def select_particles(
    central_point, output_dir, closest_num, particles_dir=particle_folder, plot=False
):
    mantle_frac_list = []
    por_frac_list = []
    name_list = []
    # extract all information from all particles
    for particle_file in Path(particles_dir).rglob("*.geom"):

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
        name_list.append(str(particle_file).split("/")[-1])

    # calculate distance
    mantle_fracs = np.array(mantle_frac_list)
    por_fracs = np.array(por_frac_list)
    coordinates = np.stack((mantle_fracs, por_fracs), axis=-1)
    distances_vec = coordinates - central_point
    distances = np.linalg.norm(distances_vec, axis=1)

    # create (distance, name) tuples for sorting.
    dist_name_tups = []
    for i in range(len(distances)):
        # also add coordinates for plotting (can be removed if i want)
        dist_name_tups.append((distances[i], name_list[i], coordinates[i]))

    # select closes num
    selection = sorted(dist_name_tups)[:closest_num]

    # make directory for putting these aprticles in
    os.mkdir(f"{output_dir}/particles")

    # move the desired particles into the temporary directory
    for particle in selection:
        # this works on multiple operating systems, I hope
        shutil.copy(
            f"{particles_dir}/{particle[1]}", f"{output_dir}/particles/{particle[1]}"
        )

    # optionally i can plot this so the user can see the spread. or save that plot in
    # the selection directory
    if plot:
        x = [x[2][0] for x in selection]
        y = [x[2][1] for x in selection]

        plt.figure(figsize=(6, 6))

        plt.scatter(mantle_fracs, por_fracs, s=7, alpha=0.3)
        plt.scatter(x, y, s=7)
        plt.scatter(central_point[0], central_point[1], color="black", s=8)
        plt.xlabel("%mantle ")
        plt.ylabel("%porosity")
        plt.ylim(-0.05, 1)
        plt.xlim(-0.05, 1)
        plt.xticks(np.arange(0, 1.05, 0.1), range(0, 101, 10))
        plt.yticks(np.arange(0, 1.05, 0.1), range(0, 101, 10))
        plt.title(
            f"closest {closest_num} particles of mantle={central_point[0]:.3f} por={central_point[1]:.3f}"
        )
        plt.grid()
        plt.savefig(f"{output_dir}/particles/plot")


def get_material_mix(output_dir, core, mantle):
    """get the full material mix with mass fractions from optool. Also get the total particle density (excluding porosity).

    Args:
        output_dir (str): _description_
        core (str): core material string as input by user
        mantle (str): mantle material string as input by user

    Returns:
        str, str, float: corrected and normalised core and mantle strings, particle density
    """
    # run optool with one wavelength and one size to extract the full mix
    if mantle:
        os.system(f"cd {output_dir} && optool -c {core} -m {mantle} -l 1 -a 1 -mie -q")
    else:
        os.system(f"cd {output_dir} && optool -c {core} -l 1 -a 1 -mie -q")

    with open(output_dir + "/dustkappa.dat", "r") as rf:
        l = rf.readline()
        while not l.startswith("#  -----"):
            l = rf.readline()

        # next lines until - - - are composition
        core_str = ""
        mantle_str = ""
        while not l.startswith("#--"):
            l = rf.readline()
            splitline = l.split()

            if "core" in splitline:
                core_str += f"{splitline[-1]} {splitline[2].rstrip('0')} "
            if "mantle" in splitline:
                mantle_str += f"{splitline[-1]} {splitline[2].rstrip('0')} "
            if "grain" in splitline:
                rho_particle = float(splitline[3])
    os.remove(output_dir + "/dustkappa.dat")
    return core_str, mantle_str, rho_particle


if __name__ == "__main__":

    # TODO add description and such
    parser = argparse.ArgumentParser(
        description="Calculate optical properties of dust particles using the DDA method on GRF particles."
    )
    rw_group = parser.add_mutually_exclusive_group()
    rw_group.add_argument(
        "-r",
        "--read",
        help="load a directory prepared with -w instead of specifying parameters.",
    )
    rw_group.add_argument(
        "-w",
        "--write",
        action="store_true",
        help="generate nk files and select particles but exit before doing any calculations. Use -r [DIR] to perform the calculations later.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Include the distribution of the particles on a porosity vfrac/mantle vfrac plot. Plot will be saved in [DIR]/particles/.",
    )
    parser.add_argument(
        "-l",
        "--wavelength",
        default="1",
        nargs="*",
        help="wavelength in micron. Can be a single value [WAVELENGTH], [START STOP NLAM] to indicate a range with NLAM logarithmically spaced values, or a ",
    )
    parser.add_argument(
        "-c",
        "--core",
        help="material(s) and mass fractions of the core. Core and mantle mass fractions are renormalised together.",
        nargs="*",
        default="pyr-mg70 0.87 c 0.13",
    )
    parser.add_argument(
        "-m",
        "--mantle",
        help="material(s) and mass fractions of the mantle.",
        nargs="*",
        default=None,
    )
    parser.add_argument(
        "-p",
        "--porosity",
        default=0.2,
        type=float,
        nargs="?",
        help="porosity volume fraction of the particle.",
    )
    parser.add_argument(
        "-a",
        "--size",
        help="size of the particle in micron.",
        default=0.1,
        type=float,
        nargs="?",
    )
    parser.add_argument("-o", "--output", help="output folder", default="output")
    parser.add_argument(
        "-n", "--number", help="number of GRF particles to use", default=3
    )
    parser.add_argument("-mc", "--multicore", type=int, nargs="?", default=0)
    parser.add_argument(
        "-d",
        "--duckling",
        action="store_true",
        help="Produce the duckling input file with Q curves",
    )

    args = parser.parse_args()

    write_bool = args.write
    read_bool = bool(args.read)

    if read_bool:
        # read in parameters
        output_dir = args.read.strip("/")
        # we do no mantle until proven otherwise
        mantle_bool = False
        mantle_mat = ""

        try:
            rf = open(output_dir + "/parameters.txt", "r")
        except FileNotFoundError:

            sys.stderr.write("ERROR: directory does not contain parameters.txt\n")
            sys.exit()

        line = rf.readline()
        while line:
            if line.startswith("size"):
                size_micron = float(line.split()[-1])
            elif line.startswith("core:"):
                core_mat = " ".join(line.split()[1:])
            elif line.startswith("mantle:"):
                mantle_mat = " ".join(line.split()[1:])
                mantle_bool = True
            elif line.startswith("multicore"):
                multicore = int(line.split()[-1])
            line = rf.readline()

        rf.close()

    else:
        # materials
        # only 1 material provided and no mass fraction does not give list
        if type(args.core) == list:
            core_mat = " ".join(args.core)
        else:
            core_mat = args.core

        mantle_bool = bool(args.mantle)
        if mantle_bool:
            if type(args.mantle) == list:
                mantle_mat = " ".join(args.mantle)
            else:
                mantle_mat = args.mantle
        else:
            mantle_mat = ""

        # other parameters
        lam_range_micron = " ".join(args.wavelength)  # str for optool input
        v_frac_porosity_arg = args.porosity
        size_micron = args.size
        output_dir = args.output.strip("/")
        n_part = int(args.number)
        plot_distr_bool = args.plot
        multicore = args.multicore

    size = size_micron * micron

    # ------------------------------------------------------------------------------------- #
    # make output folder
    # ------------------------------------------------------------------------------------- #
    if not read_bool:
        output_dir = make_output_dir(output_dir)

    # ------------------------------------------------------------------------------------- #
    # get n,k from optool
    # ------------------------------------------------------------------------------------- #

    # optool calculates n and k seperately for my mantle and core
    if read_bool:
        nk_file = f"{output_dir}/optool_mix_core.lnk"
    else:
        nk_file = get_nk(lam_range_micron, core_mat, output_dir, "core")
    core_nk, lam_arr, rho_core = read_nk(nk_file)

    if mantle_bool:
        if read_bool:
            nk_file = f"{output_dir}/optool_mix_mantle.lnk"
        else:
            nk_file = get_nk(lam_range_micron, mantle_mat, output_dir, "mantle")
        mantle_nk, _, rho_mantle = read_nk(nk_file)

    lam_arr_micron = lam_arr / micron

    # To get a proper string with mass fractions for the output file I let optool do one
    # simple calculation.
    core_mat, mantle_mat, rho_particle_arg = get_material_mix(
        output_dir, core_mat, mantle_mat
    )

    # ------------------------------------------------------------------------------------- #
    # find matching GRF particles
    # ------------------------------------------------------------------------------------- #
    # calculate mantle volume fraction from densities
    if not read_bool:
        if mantle_bool:
            try:
                # this works, except when the densities of the mantle and the core are the same.
                v_frac_mantle_arg = (rho_particle_arg - rho_core) / (
                    rho_mantle - rho_core
                )
            except ZeroDivisionError:
                # if densities are the same, mass fraction = volume fraction
                # we take this from the mantle_mat string that has alternating mass frac
                v_frac_mantle_arg = sum(
                    [
                        float(mantle_mat.split()[x])
                        for x in range(1, len(mantle_mat.split()), 2)
                    ]
                )
        else:
            v_frac_mantle_arg = 0
        sys.stdout.write(f"\nmantle volume fraction: {v_frac_mantle_arg:.3f}\n")

        select_particles(
            (v_frac_mantle_arg, v_frac_porosity_arg),
            output_dir,
            closest_num=n_part,
            plot=plot_distr_bool,
        )

    # ------------------------------------------------------------------------------------- #
    # exit if --write
    if write_bool:
        with open(f"{output_dir}/parameters.txt", "w") as wf:
            wf.write(f"size(um): {size_micron}\n")
            wf.write(f"core: {core_mat}\n")
            if multicore:
                wf.write(f"multicore: {multicore}\n")
            if mantle_bool:
                wf.write(f"mantle: {mantle_mat}\n")
                wf.write(f"mantle volume fraction: {v_frac_mantle_arg}\n")
        sys.stdout.write(
            f"written nk and particle files to ./{output_dir}/. Perform calculations with '-r {output_dir}'\n"
        )
        sys.exit()
    # ------------------------------------------------------------------------------------- #

    # list of relative path strings
    # filter out any images or notes
    particles = Path(f"{output_dir}/particles/").rglob("*.geom")
    particles = [str(x) for x in particles]  # these need to be strings

    # actual average porosity
    porosity_fracs = []

    # in [core, mantle] format. in #dipoles units
    # if no mantle, just a list of core volumes
    particle_volumes_dip = []
    # get the volumes
    for particle in particles:
        file = open(particle, "r")
        line = file.readline()
        # comments
        volumes_dipoles = []

        while line.startswith("#"):
            if line.startswith("# Volume"):
                dipoles = int(line.split()[-1])
                volumes_dipoles.append(dipoles)
            if line.startswith("# porosity_frac"):
                por = float(line.split()[-1])
                porosity_fracs.append(por)
            line = file.readline()
        file.close()

        particle_volumes_dip.append(volumes_dipoles)

    # calculate porosity
    if (
        not porosity_fracs
    ):  # the spheres test cases do not contain a porosity info line so this would remain empty
        porosity = 0
        porosity_avg = 0
    elif len(porosity_fracs) != len(particles):
        sys.stdout.write(
            "WARNING: you may be mixing spherical test particles and GRF! check the particles directory"
        )
    else:
        # TODO this is not weighted average. not super important
        # print(f"por fracs:{porosity_fracs}")
        porosity_avg = sum(porosity_fracs) / len(porosity_fracs)

    # ------------------------------------------------------------------------------------- #
    # call adda
    # ------------------------------------------------------------------------------------- #

    n_part = len(particles)
    nlam = len(lam_arr)

    start_time = time.time()

    # run per wavelength for whole particle. if multiple realisations, run for those
    # we also need the volumes
    # for all realisations
    for ig, geom_file in enumerate(particles):

        current_folder = output_dir + f"/adda_runs_particle{ig}"
        os.mkdir(current_folder)
        # adda needs this file for orientational averaging
        # this might not work on windows?
        # os.system(f"cp avg_params.dat {current_folder}/avg_params.dat")
        # for wavelength grid, needs to run multiple times
        for i, lam in enumerate(lam_arr):
            # status update?
            sys.stdout.write(f"\rparticle {ig+1:>3}/{n_part}  lambda {i+1:>3}/{nlam}")
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
            if multicore:
                # can change to "mpiexec -n {multicore} adda_mpi ..." if i want to sepcify the amount
                # it defaults to all of them i think, however '6' does not work (and I have 8)
                os.system(
                    f"mpiexec -n {multicore} adda_mpi -shape read {geom_file} -eq_rad {a_micron} -lambda {lam_micron} -m {nc} {kc} {nm} {km} -orient avg -dir {run_folder} > dump/adda_term_output{ig}_{i}.txt"
                )
            else:
                os.system(
                    f"adda -shape read {geom_file} -eq_rad {a_micron} -lambda {lam_micron} -m {nc} {kc} {nm} {km} -orient avg -dir {run_folder} > dump/adda_term_output{ig}_{i}.txt"
                )

            time_passed = time.time() - start_time

    sys.stdout.write(f"\nADDA took {datetime.timedelta(seconds =time_passed )}\n\n")

    # ------------------------------------------------------------------------------------- #
    # read in dipole size to calculate mass
    # read in adda C and Q outputs into 3d array for each particle, each wavelength, 4 results
    # read in matrices + apply RADMC convention immediately
    # ------------------------------------------------------------------------------------- #

    # do this for each realisation and average

    particle_masses = np.zeros(n_part)
    particle_rhos = np.zeros(n_part)
    # we have a 4x4 matrix, for each wavelength, for each particle
    matrices_RADMC_arr = np.zeros((n_part, nlam, 181, 4, 4))
    # matrices_unnorm_arr = np.zeros((n_part, nlam, 181, 4, 4))  # just for testing

    # for each lambda [Cext Qext Cabs Qabs], for each particle
    # so the order is arr[particle, lambda, C/Q]
    C_and_Q_arr = np.zeros((n_part, nlam, 4))

    # these are saved for the output writing
    volumes_core_mantle = np.zeros((n_part, 2))
    for ig in range(n_part):

        adda_folders = os.listdir(f"{output_dir}/adda_runs_particle{ig}")
        adda_folders.sort()

        # calculate particle mass to convert to opacity
        # all dipoles are the same size (for one particle) so we only need to read it once
        f = open(f"{output_dir}/adda_runs_particle{ig}/{adda_folders[0]}/log")
        line = f.readline()
        while not line.startswith("Dipole size"):
            line = f.readline()
        f.close()

        dipole_size_micron = float(line.split()[-2])  # micron
        dipole_size = dipole_size_micron * micron

        # dipoles are cuboids so the mass is amount of dipoles x dipole size^3 x rho
        if mantle_bool:
            volume_core_dip, volume_mantle_dip = particle_volumes_dip[ig]

            core_volume = volume_core_dip * dipole_size**3
            mantle_volume = volume_mantle_dip * dipole_size**3

            core_mass = core_volume * rho_core
            mantle_mass = mantle_volume * rho_mantle

        else:
            volume_core_dip = particle_volumes_dip[ig][0]

            core_volume = volume_core_dip * dipole_size**3

            core_mass = core_volume * rho_core
            mantle_mass = mantle_volume = 0

        particle_mass = core_mass + mantle_mass

        particle_masses[ig] = particle_mass
        # TODO this needs to be a weighted average
        particle_rhos[ig] = particle_mass / (core_volume + mantle_volume)

        volumes_core_mantle[ig] = np.array([core_volume, mantle_volume])

        for il, a_folder in enumerate(adda_folders):
            try:
                f = open(
                    f"{output_dir}/adda_runs_particle{ig}/{a_folder}/CrossSec", "r"
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
            f = open(f"{output_dir}/adda_runs_particle{ig}/{a_folder}/mueller", "r")
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
            matrices_RADMC_arr[ig, il] = (
                matrices * lam_arr[il] ** 2 / (4 * np.pi**2 * particle_mass)
            )

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

        results_arr[i] = np.array([Cext, Qext, Cabs, Qabs, kext, kabs])

    # matrix. gonna do this the slow way
    # first weigh by particle mass
    for ip in range(n_part):
        matrices_RADMC_arr[ip] = matrices_RADMC_arr[ip] * particle_masses[ip]
    # sum for averaging and divide my total mass
    matrices_RADMC_averaged = np.sum(matrices_RADMC_arr, axis=0) / particle_masses.sum()

    # volumes
    volume_fracs = volumes_core_mantle[:, 1] / (
        volumes_core_mantle[:, 0] + volumes_core_mantle[:, 1]
    )
    for ip in range(n_part):
        volume_fracs[ip] = volume_fracs[ip] * particle_masses[ip]
        particle_rhos[ip] = particle_rhos[ip] * particle_masses[ip]
    volume_frac = volume_fracs.sum() / particle_masses.sum()
    particle_rho = particle_rhos.sum() / particle_masses.sum()

    # mass
    if mantle_bool:
        mass_frac = (
            rho_core
            * (1 - volume_frac)
            / (rho_core * (1 - volume_frac) + rho_mantle * (volume_frac))
        )
    else:
        mass_frac = 1
    # density

    # ------------------------------------------------------------------------------------- #
    # write output files
    # ------------------------------------------------------------------------------------- #
    output_filename = output_dir + "/results.dat"
    wfile = open(output_filename, "w")
    # header
    wfile.write(
        "#===================================================================================\n"
    )
    # credits
    wfile.write("# computed by me yay\n")

    wfile.write("# Parameters:\n")
    wfile.write(
        f"#   lmin [um]= {lam_arr_micron[0]:10.3f} lmax [um]= {lam_arr_micron[-1]:10.3f}  nlam = {nlam:4.3g}     nang=   181\n"
    )
    wfile.write(
        f"#   porosity =      {porosity_avg:5.3f}    a [um]= {size_micron:10.3f}  npart= {n_part:4.3g}\n"
    )

    # composition

    wfile.write("# Composition:\n")
    wfile.write(
        "# Note: values in vfrac & mfrac columns are averages of particles used. Values in materials column are user input.\n"
    )

    wfile.write("#  Where   vfrac  mfrac  rho   Material\n")
    wfile.write(
        "#  -----   -----  -----  ----  -----------------------------------------------------\n"
    )

    wfile.write(
        f"#  core    {1-volume_frac:5.3f}  {mass_frac:5.3f}  {rho_core:3.2f}  {core_mat}\n"
    )
    if mantle_bool:
        wfile.write(
            f"#  mantle  {volume_frac:5.3f}  {1-mass_frac:5.3f}  {rho_mantle:3.2f}  {mantle_mat}\n"
        )

    wfile.write(
        "#  -----   -----  -----  ----  -----------------------------------------------------\n"
    )
    wfile.write(
        "#===================================================================================\n"
    )
    # description of the data section. TODO needs to also include the matrices expl.
    wfile.write("# format of output file\n")
    # lam(1)    kabs(1)    ksca(1)    g(1)        ! um, cm^2/g, cm^2/g, none
    #    ...
    #    lam(nlam) kabs(nlam) ksca(nlam) g(nlam)
    wfile.write("#    nlambda\n")
    wfile.write(
        "#    lambda(1)    Cext(1)    Qext(1)    Cabs(1)    Qabs(1)    kext(1)    kabs(1)\n"
    )
    wfile.write("#    ...\n")
    wfile.write(
        "#    lambda(nlam) Cext(nlam) Qext(nlam) Cabs(nlam) Qabs(nlam) kext(nlam) kabs(nlam)\n#\n"
    )

    wfile.write("#    lambda(1)\n")
    wfile.write(
        "#    ang(1)   s11 s12 s13 s14 s21 s22 s23 s24 s31 s32 s33 s34 s41 s42 s43 s44\n#    ...\n"
    )
    wfile.write(
        "#    ang(181) s11 s12 s13 s14 s21 s22 s23 s24 s31 s32 s33 s34 s41 s42 s43 s44"
    )
    wfile.write("\n#\n#    ...\n#\n")
    wfile.write("#    lambda(nlam)\n")
    wfile.write(
        "#    ang(1)   s11 s12 s13 s14 s21 s22 s23 s24 s31 s32 s33 s34 s41 s42 s43 s44\n#    ...\n"
    )
    wfile.write(
        "#    ang(181) s11 s12 s13 s14 s21 s22 s23 s24 s31 s32 s33 s34 s41 s42 s43 s44\n"
    )
    wfile.write(
        "#===================================================================================\n"
    )
    # opacites etc
    # there is some information that is needed here. optool does format number
    # and number of lambdas
    # [Cext Qext Cabs Qabs kext kabs]
    wfile.write(f"{nlam}\n")
    for i in range(nlam):

        # write the lambda grid and the opacities
        # this means 15 wide with 5 decimals after the dot. should line up with header.

        wfile.write(
            f"{lam_arr_micron[i]:15.5e} {results_arr[i][0]:15.5e} {results_arr[i][1]:15.5e} {results_arr[i][2]:15.5e} {results_arr[i][3]:15.5e} {results_arr[i][4]:15.5e} {results_arr[i][5]:15.5e}\n"
        )

    # matrix

    for il, matrices in enumerate(matrices_RADMC_averaged):
        wfile.write("\n")
        wfile.write(f"{lam_arr_micron[il]}\n")
        for ia, matrix in enumerate(matrices):
            wfile.write(
                f"{ia} {matrix[0,0]} {matrix[0,1]} {matrix[0,2]} {matrix[0,3]} {matrix[1,0]} {matrix[1,1]} {matrix[1,2]} {matrix[1,3]} {matrix[2,0]} {matrix[2,1]} {matrix[2,2]} {matrix[2,3]} {matrix[3,0]} {matrix[3,1]} {matrix[3,2]} {matrix[3,3]}\n"
            )

    wfile.close()
    sys.stdout.write(f"written output file to {output_filename}\n")

    # write Q file for duckling
    outputduck_filename = output_dir + "/ducky.dat"

    wfile = open(outputduck_filename, "w")
    # column names
    # TODO put average rho in there
    wfile.write(f"{nlam} {size_micron} {particle_rho}\n")
    for i in range(nlam):
        # am now writing Qext
        wfile.write(f"{lam_arr_micron[i]:.15e} {results_arr[i][3]:.15e}\n")

    wfile.close()
