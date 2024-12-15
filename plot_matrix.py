import matplotlib.pyplot as plt
import argparse
import numpy as np

# read in matrix file and plot elements of the matrix for a specific wavelength as a function of angle


def read_matrix(muellerfile, norm=True):
    """read in a mueller matrix file and output as array of matrices, for each angle. normalises to Hovenier normalisation.

    Args:
        muellerfile (file): file containing the mueler matrix
        norm (bool): normalise the matrix. defaults to True

    """
    # for adda:

    # read in file. 17 columns
    file = open(muellerfile, "r")
    columnnames = file.readline().split()
    # file always has 361 lines: a header and 360 angles
    # thetas = np.arange(181)
    thetas = np.arange(181)

    # saving the matrices in an array containing all the 4x4 matrices
    # sometimes it 180 and sometimes its 360
    # matrices = np.zeros((360, 4, 4))
    matrices = np.zeros((181, 4, 4))

    line = file.readline()

    while line:
        line_split = line.split()
        # this is the angle but it also works as an index
        i = int(float(line_split[0]))

        # remove the angle
        line_split.pop(0)
        # make numbers. this is not actually necessary
        elements = [float(el) for el in line_split]
        # reshape and save the matrix
        matrix = np.array(elements).reshape((4, 4))
        matrices[i] = matrix

        line = file.readline()

    file.close()

    # normalisation. assumes cross section and log file to be in the same folder
    if norm:
        # read in files
        path = muellerfile.split("/")
        crosssecpath = "/".join(path[:-1]) + "/CrossSec-Y"
        logpath = "/".join(path[:-1]) + "/log"

        # read cross section
        try:
            f = open(crosssecpath, "r")
        except FileNotFoundError:
            crosssecpath = "/".join(path[:-1]) + "/CrossSec"
            f = open(crosssecpath, "r")

        lines = f.readlines()
        Cexts = float(lines[0].split()[-1])
        Cabs = float(lines[2].split()[-1])
        Csca = Cexts - Cabs
        f.close()

        # read in lambda
        with open(logpath, "r") as f:
            for _ in range(3):
                line = f.readline()

            l = float(line.split()[-1])

        # calculate normalisation factor
        norm_fact = l**2 / (np.pi * Csca)
        print("norm factor:", norm_fact)

        # normalise matrix
        # matrices[:, 1:] = matrices[:, 1:] * norm_fact
        matrices = matrices * norm_fact

    return thetas, matrices


def read_matrix_optool(dustkapscatmatfile):
    # optool outputs everything on one file, so need to isolate the matrix first
    file = open(dustkapscatmatfile, "r")

    line = file.readline()

    # comments
    while line.startswith("#"):
        line = file.readline()

    # the way the file is written, there will be 3 white lines before the matrix
    white_counter = 0
    while white_counter < 3 and line:
        if line == "\n":
            white_counter += 1
        line = file.readline()

    # saving the matrices in an array containing all the 4x4 matrices
    if dustkapscatmatfile.endswith(".dat"):
        # optool only does 180 angles
        matrices = np.zeros((180, 4, 4))
        thetas = np.arange(0.5, 180, 1)
    else:
        thetas = np.arange(181)
        matrices = np.zeros((181, 4, 4))

    # ANGLE counter
    i = 0
    while line:

        matrix = np.zeros((4, 4))
        line_split = line.split()

        # fill in the six elements I have
        elements = [float(el) for el in line_split]
        matrix[0, 0] = elements[0]  # F11
        matrix[0, 1] = elements[1]  # F12
        matrix[1, 1] = elements[2]  # F22
        matrix[2, 2] = elements[3]  # F33
        matrix[2, 3] = elements[4]  # F34
        matrix[3, 3] = elements[5]  # F44

        # TODO fill in symmetry

        # save the same way
        matrices[i] = matrix

        i += 1
        line = file.readline()

    file.close()

    return thetas, matrices


# I need to write this matrix conversion shit. but idk how to do this well without restructuring my code a bunch.
# so this is just gonna be filled with some placeholder stuff
def convention_conversion(matrix, kappa_scat, mass, lam):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("muellerfile", help="mueller matrix file")
    parser.add_argument("element", help="element of the matrix to plot, like 12 or 33")
    args = parser.parse_args()

    # only works if the element argument is two numbers and no spaces
    element = [int(el) for el in list(args.element)]

    # optool file
    if args.muellerfile.endswith(".dat") or args.muellerfile.endswith(".inp"):
        thetas, matrices = read_matrix_optool(args.muellerfile)
    # adda file
    else:
        thetas, matrices = read_matrix(args.muellerfile)

    # array of chosen matrix elements
    element_arr = matrices[:, element[0] - 1, element[1] - 1]

    fig = plt.figure()
    plt.plot(thetas, element_arr)

    if args.muellerfile.endswith(".dat"):
        plt.title(f"optool mueller matrix element s{element[0]}{element[1]}")
    else:
        plt.title(f"adda mueller matrix element s{element[0]}{element[1]}")

    plt.xlabel("theta (degrees)")
    plt.ylabel(f"s{element[0]}{element[1]}")
    # plt.xlim(0, 180)
    plt.xlim(0, 180)
    plt.grid()
    plt.show()
    # plt.savefig(f"runs/GRF_test/plots_avg/mueller{args.element}GRFavg")
