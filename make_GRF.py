# make porous gaussian random field particles according to M. Min et al 2007

import numpy as np
import matplotlib.pyplot as plt
import argparse
import time
import copy
import sys
import os

# this is a little scary but my particles are getting bigger
# this barely touches my 16 gb ram so it could be so so much bigger
sys.setrecursionlimit(100000)
por = 3
foldername = f"std_params_p{por}_por"
# make output folder
if os.path.isdir(foldername):
    nofolder = True
    counter = 1
    newfoldername = foldername + str(counter)

    while nofolder:
        try:
            os.mkdir(newfoldername)
            nofolder = False
        except FileExistsError:
            counter += 1
            newfoldername = foldername + str(counter)
else:
    newfoldername = foldername
    os.mkdir(newfoldername)

foldername = newfoldername

# parser = argparse.ArgumentParser()
# parser.add_argument("M", help="number of points", default=128, type=int, nargs="?")
# parser.add_argument("rho", help="size", default=100, type=float, nargs="?")
# args = parser.parse_args()

# ---------------------------------------------------------------------------------- #
# variables
# ---------------------------------------------------------------------------------- #
# np.random.seed(1)

# number of points
M = 128
# size of particles
rho = 300

mantle = True

# I dont want to pick a threshold above 0.5, also not with mantle. makes particles weirder
if mantle:
    mantle_threshold = 0.5
    # threshold value
    threshold = mantle_threshold * 1.1

else:
    threshold = 0.5

# porosity division (rho' = rho/por_div). The effect of this is very dependent om M of course.
# it does not scale linearly.
por_div = 62.5
# porosity threshold
por_threshold = 0.1
por_threshold = por / 10
# add porosity or not
porosity = True
rho2 = rho / por_div


save_particles = True
# size range for saving particles
part_low_lim = 1000
part_up_lim = 1500

with open(f"{newfoldername}/parameters.txt", "w") as f:
    f.write(f"M {M}\n")
    f.write(f"rho {rho}\n")
    f.write(f"threshold {threshold}\n")
    f.write(f"mantle_threshold {mantle_threshold}\n")
    f.write(f"por_div {por_div}\n")
    f.write(f"por_threshold {por_threshold}\n")
    f.write(f"save_lim {part_low_lim}-{part_up_lim}\n")


# ---------------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------------- #
def plot3d(arr, title=None, save=False):
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")

    # find the coordinates for plotting
    x, y, z = np.where(arr == 1)
    x2, y2, z2 = np.where(arr == 2)

    # https://discourse.matplotlib.org/t/collection-of-markers-with-size-set-in-data-units/21057/2
    # this has a good idea on how to make the plotting look nice i think. not implemented yet

    # Plot the points
    ax.scatter(x, y, z, color="orange", label="core", alpha=1)
    if x2.size > 0:
        ax.scatter(x2, y2, z2, alpha=0.5, color="blue", label="mantle")
        ax.legend()

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


def plot_slice(arr, title="slice"):

    # x, y = np.where(arr == 1)

    fig = plt.figure()

    # plt.scatter(x, y)
    plt.imshow(arr, cmap="hot", interpolation="none")
    # plt.xlim(plt.ylim())
    plt.title(title)
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
space[np.abs(GijkF) > threshold] = 1

# ---------------------------------------------------------------------------------- #
# add a mantle
# same idea as normal particle but theres another threshold such that the mantle
# is x% of the volume
# ---------------------------------------------------------------------------------- #

volume_particles = np.count_nonzero(space)
if mantle:
    space[(np.abs(GijkF) > mantle_threshold) & (np.abs(GijkF) < threshold)] = 2


# ---------------------------------------------------------------------------------- #
# add porosity
# NOTE whether the mantle is added before porosity or after determines if
# the mantle is porous
# ---------------------------------------------------------------------------------- #

no_poros = copy.copy(space)

if porosity:
    space[np.abs(GijkF2) > por_threshold] = 0

# plot_slice(space[int(M / 2)], title="with mantl and porosity")

print("done.")
print("number of dipoles:", np.count_nonzero(space))

por_diff = no_poros - space  # this should leave 1 values where there is stuff removed
print("dipoles removed with porosity:", np.count_nonzero(por_diff))
por_frac = np.count_nonzero(por_diff) / np.count_nonzero(no_poros)
print(f"porosity fraction:{por_frac:.3f}\n")
# plot3d(space)


# ---------------------------------------------------------------------------------- #
# extract the particles from here
# ---------------------------------------------------------------------------------- #


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
    destination_array[coordinate] = arr[coordinate]
    arr[coordinate] = 0

    # for each neighbour, call function and then add to particle and remove from original
    for neighbour in neighbours:
        if arr[neighbour] != 0:
            # if its inside the particle, go deeper.
            get_particle(neighbour, arr, particle_arr)


# we will do this for each particle so there will be a while loop involved.
particles_removed = False
space_copy = copy.copy(space)  # space_copy will be modified an slowly eaten
particles = []  # list to fill with particles arrays

# get a point inside a particle to start
x, y, z = np.where(space_copy != 0)
coordinate = (x[0], y[0], z[0])

while not particles_removed:

    # create new empty array to store particle in, and extract the particle
    particle_arr = np.zeros((M, M, M))
    get_particle(coordinate, space_copy, particle_arr)

    particles.append(particle_arr)

    # new particle. If theres nothing left, exit loop
    x, y, z = np.where(space_copy != 0)
    if x.size > 0:
        coordinate = (x[0], y[0], z[0])
    else:
        particles_removed = True

num_parts = len(particles)
print("number of particles extracted:", num_parts)

# ---------------------------------------------------------------------------------- #
# recombining the particles if they are not good
# ---------------------------------------------------------------------------------- #


def recombine_particle(particle):
    """takes a 'split' particle and recombines it by shifting the whole particle down
    and then moving the bottom half up to meet the top half.

    Args:
        particle (3d arr): array containing split particle

    Returns:
        3d arr: recombined particle
    """
    # plot the particle to see it
    # plot3d(particle, title="before shift")
    x, y, z = np.where(particle == 1)
    x2, y2, z2 = np.where(particle == 2)

    # shift necessary directions
    while 0 in x or 0 in x2:
        x -= 1
        x2 -= 1

    while 0 in y or 0 in y2:
        y -= 1
        y2 -= 1

    while 0 in z or 0 in z2:
        z -= 1
        z2 -= 1

    arr = np.zeros((M, M, M))
    arr[x, y, z] = 1
    arr[x2, y2, z2] = 2
    # plot3d(arr, title="fixed?")

    return arr


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
    file.write("# " + comments + "\n")
    if porosity:
        file.write(f"# porosity_frac = {por_frac:.3f}\n")
    else:
        file.write("# no porosity\n")
    if Ndom == 1:
        file.write(f"# Volume = {len(coordinates)}\n")
        file.write(f"Nmat={Ndom}\n")
        for coordinate in coordinates:
            x, y, z = coordinate
            file.write(f"{x} {y} {z} \n")
    else:
        file.write(f"# Volume1 = {len(coordinates[0])}\n")
        file.write(f"# Volume2 = {len(coordinates[1])}\n")

        # if Ndom is more than one, coordinates should be one dimension higher
        file.write(f"Nmat={Ndom}\n")
        for domain in range(Ndom):
            for coordinate in coordinates[domain]:
                x, y, z = coordinate
                file.write(f"{x} {y} {z}" + " " + str(domain + 1) + "\n")

    file.close()


# save particles one by one
# have a filter for particle size?
if mantle:
    Ndom = 2
else:
    Ndom = 1

i = 0
total_dipoles_particles = 0
particles_saved = 0
for particle in particles:

    total_dipoles_particles += np.count_nonzero(particle)

    # first check volume fraction before checking size
    # core_count = np.count_nonzero(particle == 1)
    # mantle_count = np.count_nonzero(particle == 2)
    # volume_fraction = mantle_count / core_count * 100
    # print(
    #     f"\nparticle {i}:\n \t core: {core_count}\n\t mantle: {mantle_count}\n volume fraction: {volume_fraction:.4f}"
    # )

    # these xyz are the total particle including mantle. this for checking size and split
    x, y, z = np.where(particle != 0)
    if part_low_lim < len(x) < part_up_lim:

        # first check volume fraction before checking size
        core_count = np.count_nonzero(particle == 1)
        mantle_count = np.count_nonzero(particle == 2)
        volume_fraction = mantle_count / (core_count + mantle_count)
        print(
            f"\nparticle {i}:\n \tdipoles: {(core_count + mantle_count)}\n \tmantle volume fraction: {volume_fraction:.4}"
        )

        # both 0 and max need to touch if the particle is split
        if (
            (0 in x and M - 1 in x)
            or (0 in y and M - 1 in y)
            or (0 in z and M - 1 in z)
        ):

            particle = recombine_particle(particle)
        # plot3d(particle)
        if save_particles:
            plot3d(particle, title="ACCEPTED", save=f"{newfoldername}/particle{i}")

        # save coordinates
        x, y, z = np.where(particle == 1)
        if mantle:
            x2, y2, z2 = np.where(particle == 2)
            core_coords = np.stack((x, y, z), axis=-1)
            mantle_coords = np.stack((x2, y2, z2), axis=-1)
            coordinates = [core_coords, mantle_coords]
        else:

            coordinates = zip(x, y, z)

        write_shape_file(f"{newfoldername}/GRFpart{i}", coordinates, Ndom)
        particles_saved += 1
    elif save_particles:
        pass
        # plot3d(particle, title="REJECTED", save=f"{newfoldername}/particle{i}")

    i += 1
if save_particles:
    # save the total cube plot
    plot3d(space, save=f"{newfoldername}/full")
    # plot3d(no_poros, save=f"{newfoldername}/no_poros")

print(f"\nsaving particles in {newfoldername}")
print("number of particles saved:", particles_saved)

# print(
#     f"dipole sanity check: \n    total from extracted particles={total_dipoles_particles}\n    total from espace={np.count_nonzero(space)} "
# )
