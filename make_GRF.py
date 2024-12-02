# make porous gaussian random field particles according to M. Min et al 2007

import numpy as np
import matplotlib.pyplot as plt
import argparse
import time
from copy import deepcopy


def plot3d(arr):
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")

    # find the coordinates for plotting
    x, y, z = np.where(arr == 1)

    # https://discourse.matplotlib.org/t/collection-of-markers-with-size-set-in-data-units/21057/2
    # this has a good idea on how to make the plotting look nice i think. not implemented yet

    # Plot the points
    ax.scatter(x, y, z, marker="s")

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_aspect("equal")
    ax.set_title(f"M={M}, rho={rho}")

    plt.show()


# for testing
# np.random.seed(10)

parser = argparse.ArgumentParser()
parser.add_argument("M", help="number of points", default=40, type=int, nargs="?")
parser.add_argument("rho", help="size", default=1, type=int, nargs="?")
args = parser.parse_args()

# ---------------------------------------------------------------------------------- #
# variables
# ---------------------------------------------------------------------------------- #

# number of points
M = args.M
# size of particles
rho = args.rho
# threshold value
threshold = 0.5
# porosity division (rho' = rho/por_div). The effect of this is very dependent om M of course.
# it does not scale linearly.
por_div = 50
# porosity threshold
por_threshold = 0.2
# add porosity or not
porosity = False
# ---------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------- #

# construct random points
print("constructing GRF...")
start_time = time.time()

Rijk = np.random.rand(M, M, M)

# distances to the center 3d array. this is actually half a point off center? but it maches the algorithm.
i_arr = np.arange(M) + 1
j_arr = np.arange(M) + 1
k_arr = np.arange(M) + 1

print("making distances array...")
d = np.sqrt(
    (i_arr[:, np.newaxis, np.newaxis] - M / 2) ** 2
    + (j_arr[:, np.newaxis] - M / 2) ** 2
    + (k_arr - M / 2) ** 2
)

# construct the field
Gijk = Rijk * np.exp(-rho * d**2)

# we need to take the 3d fourier transform. ( not sure how this function wants the input to look like and what axes to specify) (axes=[0,1] or [1,0] does not change anything)
GijkF = np.fft.fftn(Gijk)

print("first fourier...")

# normalise
GijkF = GijkF / np.max(GijkF)

# all points where GijF is > 0.5 are inside the particle.
# so all points in space will be evaluated besed on the value from Gijkf
space = np.zeros((M, M, M))
space[GijkF > threshold] = 1

no_poros = deepcopy(space)
print("done.")
print(np.count_nonzero(space))
# ---------------------------------------------------------------------------------- #
# we can add porosity
# ---------------------------------------------------------------------------------- #
print("adding porosity...")
if porosity:
    # second GRF with smaller effective size
    rho2 = rho / por_div

    # construct the field
    Gijk2 = Rijk * np.exp(-rho2 * d**2)
    print("second fourier...")
    GijkF2 = np.fft.fftn(Gijk2)
    print("done with second fourier.")
    GijkF2 = GijkF2 / np.max(GijkF2)

    # we add vacuum back where gijkf2 is above the porosity threshold
    space[GijkF2 > por_threshold] = 0
print(np.count_nonzero(space))

# see where the porosity got added.
por_diff = no_poros - space  # this should leave 1 values where there is stuff removed

print(np.count_nonzero(por_diff))
plot3d(space)
