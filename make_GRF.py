# make porous gaussian random field particles according to M. Min et al 2007

import numpy as np
import matplotlib.pyplot as plt
import argparse
import time
import copy
import sys

# this is a little scary but my particles are getting bigger
sys.setrecursionlimit(3500)

test_folder = "test_images/"


def plot3d(arr, title=None, save=False):
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")

    # find the coordinates for plotting
    x, y, z = np.where(arr == 1)

    # https://discourse.matplotlib.org/t/collection-of-markers-with-size-set-in-data-units/21057/2
    # this has a good idea on how to make the plotting look nice i think. not implemented yet

    # Plot the points
    ax.scatter(x, y, z)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    ax.set_xlim(0, arr.shape[0])
    ax.set_ylim(0, arr.shape[1])
    ax.set_zlim(0, arr.shape[2])

    ax.set_aspect("equal")
    ax.set_title(f"M={M}, rho={rho}")
    if title:
        ax.set_title(title)

    if save:
        plt.savefig(f"{test_folder}{save}.png")
    else:
        plt.show()


def plot_slice(arr):

    x, y = np.where(arr == 1)

    fig = plt.figure()

    plt.scatter(x, y)
    plt.xlim(plt.ylim())
    plt.show()


# for testing
# np.random.seed(10)

parser = argparse.ArgumentParser()
parser.add_argument("M", help="number of points", default=40, type=int, nargs="?")
parser.add_argument("rho", help="size", default=1, type=float, nargs="?")
args = parser.parse_args()

# ---------------------------------------------------------------------------------- #
# variables
# ---------------------------------------------------------------------------------- #
np.random.seed(0)
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
porosity = True
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

no_poros = copy.copy(space)
print("done.")
print("number of dipoles:", np.count_nonzero(space))

plot3d(space, save="no_poros")
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

    # see where the porosity got added.
    por_diff = (
        no_poros - space
    )  # this should leave 1 values where there is stuff removed
    print("dipoles removed with porosity:", np.count_nonzero(por_diff))

    plot3d(space, save="poros_added")
# ---------------------------------------------------------------------------------- #
# extract the particles from here
# ---------------------------------------------------------------------------------- #
# plot_slice(space[0])

# pick a point. any point that is inside a particle.
# check all eight neighbours. if any are outside the particle, add point to some list
#  go to new point that is one of those neighbours and repeat

# what does this give us? in the end, a0n entire outside boundary of the particle (potato peel)
# this means we have the 6 bounds to extract it.

# check the ouside of the extraction box for particle bits (ones) (jonas' idea).
# if there is a point in here that is NOT in my potato peel, it is a slice of a different particle
# we could then do another search to find the boundary of that particle to remove it? no idk
# cris has an idea to do recursive boxes that get smaller and smaller until i only have the particle

# could also just try neighbour searching for the entire thing.
# recursively. picture of cris' pseudocode


# this method should work after dealing with porosity
def get_particle(coordinate, arr, destination_array):
    """given a coordinate, check if the coordinate is inside a particle in the 3d array.
    then recursively check all the neighbouring spaces to get all the dipoles of a particle.
    works for one particle,and has to start within a particle.

    Args:
        coordinate (tuple): x,y,z coordinate of starting point
        arr (3D array): space array containing all the particles
        destination_array
    """
    # get the 26 neighbours. check if they are not outside of the array
    x, y, z = coordinate
    neighbours = []
    for xi in [-1, 0, 1]:
        for yi in [-1, 0, 1]:
            for zi in [-1, 0, 1]:
                if (
                    not (xi == 0 and yi == 0 and zi == 0)
                    and (0 <= x + xi < M)
                    and (0 <= y + yi < M)
                    and (0 <= z + zi < M)
                ):  # don't add the current coordinate, and dont add anything outside of the array
                    neighbours.append((x + xi, y + yi, z + zi))

    # save point and remove from original
    destination_array[coordinate] = 1
    arr[coordinate] = 0

    # for each neighbour, call function and then add to particle and remove from original
    for neighbour in neighbours:
        if arr[neighbour] == 1:
            # if its inside the particle, go deeper.
            get_particle(neighbour, arr, particle_arr)


# we will do this for each particle so there will be a while loop involved.
particles_removed = False
space_copy = copy.copy(space)  # space_copy will be modified an dslowly eaten
particles = []  # list to fill with particles arrays

# get a point inside a particle. this can be done a lot easier possibly but this works
x, y, z = np.where(space_copy == 1)
coordinate = (x[0], y[0], z[0])

while not particles_removed:

    x, y, z = np.where(space_copy == 1)
    coordinate = (x[0], y[0], z[0])

    particle_arr = np.zeros((M, M, M))
    get_particle(coordinate, space_copy, particle_arr)

    particles.append(particle_arr)

    # new particle
    x, y, z = np.where(space_copy == 1)
    if x.size > 0:
        coordinate = (x[0], y[0], z[0])
    else:
        particles_removed = True

num_parts = len(particles)
print("number of particles extracted:", num_parts)
# plot3d(space_copy, title="(hopefully) empty space")
# plot3d(space, title=f"space with hopefully {num_parts} particles")
i = 1
total_dipoles_particles = 0
for particle in particles:
    plot3d(particle, save=f"particle{i}")
    i += 1
    total_dipoles_particles += np.count_nonzero(particle)


print(
    f"dipole sanity check: \n    total from extracted particles={total_dipoles_particles}\n    total from espace={np.count_nonzero(space)} "
)
# ---------------------------------------------------------------------------------- #
# we can add a mantle
# same idea as normal particle but theres another threshold such that the mantle
# is 30% of the volume (at least thats how they do it)
# ---------------------------------------------------------------------------------- #
volume_particles = np.count_nonzero(space)
# not sure how to do this, you'd have to run it to see how much the threshold should be maybe
# unless i can find a way to understand what volume my parameters will produce. It would be too
# time consuming to do it twice.
