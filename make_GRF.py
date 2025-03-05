# make porous gaussian random field particles according to M. Min et al 2007

import numpy as np
import matplotlib.pyplot as plt
import argparse
import time
import copy
import sys
import os

# this is a little scary but my particles are getting bigger
sys.setrecursionlimit(3500)

foldername = "ahhhh"


# for testing
np.random.seed(10)

parser = argparse.ArgumentParser()
parser.add_argument("M", help="number of points", default=64, type=int, nargs="?")
parser.add_argument("rho", help="size", default=100, type=float, nargs="?")
args = parser.parse_args()

# ---------------------------------------------------------------------------------- #
# variables
# ---------------------------------------------------------------------------------- #
# np.random.seed(0)
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
rho2 = rho / por_div

save_particles = True
# size range for saving particles
part_low_lim = 1000
part_up_lim = 1500


# ---------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------- #
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
        plt.savefig(f"{save}.png")
        plt.close()
    else:
        plt.show()


def plot_slice(arr):

    x, y = np.where(arr == 1)

    fig = plt.figure()

    plt.scatter(x, y)
    plt.xlim(plt.ylim())
    plt.show()


def plot_heatmap(slice, maxm=100):
    plt.imshow(slice, cmap="hot", interpolation="nearest", vmin=0, vmax=maxm)
    plt.show()


# ---------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------- #

# construct 3D space with normal random points
print("constructing GRF...")
Rijk = np.random.normal(loc=0, scale=1, size=(M, M, M))
# porosity
Rijk2 = np.random.normal(loc=0, scale=1, size=(M, M, M))

# fourier transform to freq space
Rijk = np.fft.fftn(Rijk)
Rijk2 = np.fft.fftn(Rijk2)


# new method of distances array in a triple loop to try and match michiel
# (its not necessary to make these copies but it helps with my overview)
Gijk = copy.copy(Rijk)
Gijk2 = copy.copy(Rijk2)

for i in range(M):
    for j in range(M):
        for k in range(M):
            # scales x y and z to be between -1 and 1
            # theres a mistake in here wrt indexing but im too dumb to fix it rn (its in notebook)
            # (could just change the loop to be 1-M+1 and the -1's in the equation)
            x = 2.0 * i / M - 1.0
            y = 2.0 * j / M - 1.0
            z = 2.0 * k / M - 1.0
            Gijk[i, j, k] = Rijk[i, j, k] * np.exp(-(x**2 + y**2 + z**2) * rho)
            Gijk2[i, j, k] = Rijk2[i, j, k] * np.exp(-(x**2 + y**2 + z**2) * rho2)

# transform back into space space
GijkF = np.fft.ifftn(Gijk)
GijkF2 = np.fft.ifftn(Gijk2)

# normalise
GijkF = GijkF / np.max(GijkF)
GijkF2 = GijkF2 / np.max(GijkF2)

# all points where GijF is > 0.5 are inside the particle.
# so all points in space will be evaluated besed on the value from Gijkf
space = np.zeros((M, M, M))
space[GijkF > threshold] = 1

no_poros = copy.copy(space)

if porosity:
    space[GijkF2 > por_threshold] = 0

print("done.")
print("number of dipoles:", np.count_nonzero(space))

por_diff = no_poros - space  # this should leave 1 values where there is stuff removed
print("dipoles removed with porosity:", np.count_nonzero(por_diff))


plot3d(space)

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
# recursively. picture of cris' idea


# this method should work after dealing with porosity
def get_particle(coordinate, arr, destination_array):
    """given a starting coordinate, recursively check all the neighbouring spaces
    to get all the dipoles in a particle.
    Works for one particle,and has to start within a particle.

    arr and destination array need to have the same size and shape.

    Args:
        coordinate (tuple): x,y,z coordinate of starting point
        arr (3D array): space array containing all the particles
        destination_array (3D array): empty array of same size as arr to save particle in
    """
    # get the 26 neighbours. check if they are not outside of the array
    x, y, z = coordinate
    neighbours = []
    for xi in [-1, 0, 1]:
        for yi in [-1, 0, 1]:
            for zi in [-1, 0, 1]:
                if not (
                    xi == 0 and yi == 0 and zi == 0
                ):  # dont add current point (not a neighbour)

                    # if the index is too big, subtract M
                    newx = x + xi
                    newy = y + yi
                    newz = z + zi

                    if newx >= M:
                        newx -= M
                    if newy >= M:
                        newy -= M
                    if newz >= M:
                        newz -= M
                    # if index is too small, add M. This only happens if the particle wraps around multiple times
                    if newx < -M:
                        newx += M
                    if newy < -M:
                        newy += M
                    if newz < -M:
                        newz += M

                    neighbours.append((newx, newy, newz))

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
space_copy = copy.copy(space)  # space_copy will be modified an slowly eaten
particles = []  # list to fill with particles arrays

# get a point inside a particle to start
x, y, z = np.where(space_copy == 1)
coordinate = (x[0], y[0], z[0])

while not particles_removed:

    # create new empty array to store particle in, and extract the particle
    particle_arr = np.zeros((M, M, M))
    get_particle(coordinate, space_copy, particle_arr)

    particles.append(particle_arr)

    # new particle. If theres nothing left, exit loop
    x, y, z = np.where(space_copy == 1)
    if x.size > 0:
        coordinate = (x[0], y[0], z[0])
    else:
        particles_removed = True

num_parts = len(particles)
print("number of particles extracted:", num_parts)
# ---------------------------------------------------------------------------------- #
# saving the particles. I only want to save particles that are a certain size
# ---------------------------------------------------------------------------------- #


def write_shape_file(filename, coordinates, Ndom=1, comments="some comment"):
    # make a file for the particle with increasing particle number
    # idk why im doing this so complicatedly
    # nofile = True
    # counter = 0
    # newfilename = filename + str(counter)

    # while nofile:
    #     try:
    #         file = open(f"{newfilename}.geom", "x")
    #         nofile = False
    #     except FileExistsError:
    #         counter += 1
    #         newfilename = filename + str(counter)

    file = open(f"{filename}.geom", "x")

    # write the particle to file
    file.write(comments)
    if Ndom == 1:
        for coordinate in coordinates:
            x, y, z = coordinate
            file.write(f"{x} {y} {z} \n")
    else:
        # if Ndom is more than one, coordinates should be one dimension higher
        file.write(f"Nmat={Ndom}\n")
        for domain in range(Ndom):
            for coordinate in coordinates[domain]:
                file.write(coordinate + " " + str(domain + 1) + "\n")

    file.close()


# make a folder (very elaborate sorry)
if os.path.isdir(foldername):
    nofolder = True
    counter = 1
    newfoldername = foldername + str(counter)

    while nofolder:
        try:
            print(newfoldername)
            os.mkdir(newfoldername)
            nofolder = False
        except FileExistsError:
            counter += 1
            newfoldername = foldername + str(counter)
else:
    newfoldername = foldername
    os.mkdir(newfoldername)


# save particles one by one
# have a filter for particle size?
i = 0
total_dipoles_particles = 0
for particle in particles:
    if save_particles:
        plot3d(particle, save=f"{newfoldername}/particle{i}")

    total_dipoles_particles += np.count_nonzero(particle)

    x, y, z = np.where(particle == 1)
    coordinates = zip(x, y, z)
    write_shape_file(f"{newfoldername}/GRFpart{i}", coordinates)

    i += 1


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
