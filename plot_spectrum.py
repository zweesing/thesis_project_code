"""plot the opacities in my own results.dat file"""

import matplotlib.pyplot as plt
import numpy as np
import argparse


def read_in_file(file):
    """read in the opacities from results.dat and return the wavelength array, kext and kabs

    Args:
        file (_type_): _description_

    Returns:
        _type_: _description_
    """
    file = open(file, "r")
    line = file.readline()
    # header
    while line.startswith("#"):
        line = file.readline()
    nlam = int(float(line))
    line = file.readline()

    # prepare arrays
    lam_arr = np.zeros(nlam)
    kext_arr = np.zeros(nlam)
    kabs_arr = np.zeros(nlam)

    for i in range(nlam):
        lam_arr[i] = float(line.split()[0])
        kext_arr[i] = float(line.split()[5])
        kabs_arr[i] = float(line.split()[6])

        line = file.readline()

    file.close()

    return lam_arr, kext_arr, kabs_arr


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="plot the spectrum from a results.dat file."
    )
    parser.add_argument("file", type=str, help="path to results.dat")

    args = parser.parse_args()
    file = args.file

    lam, kext, kabs = read_in_file(file)

    plt.figure(figsize=(8, 6))

    plt.title("spectrum")
    plt.ylabel("kabs, kext, ksca")
    plt.xlabel(r"lambda [$\mu$m]")

    plt.plot(lam, kext, label="kext")
    plt.plot(lam, kabs, label="kabs")
    plt.plot(lam, kext - kabs, label="ksca")

    ymin, ymax = plt.ylim()
    # plt.vlines(18,ymin,ymax,color='red' )

    plt.xscale("log")
    plt.xlim(lam[0], lam[-1])
    plt.yscale("log")

    plt.legend()
    plt.show()
