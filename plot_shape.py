import matplotlib.pyplot as plt
import argparse
import numpy as np


def plot_shape(shapefile, mode="full"):

    # its probably easiest to do this with numpy reshape type shit
    file = open(shapefile, "r")
    line = file.readline()
    # comments
    while line.startswith("#"):
        line = file.readline()

    # check if number of materials is specified
    if line.startswith("Nmat"):
        Nmat = int(line[-2])
        line = file.readline()
    else:
        Nmat = 1

    x_list = [[] for _ in range(Nmat)]
    y_list = [[] for _ in range(Nmat)]
    z_list = [[] for _ in range(Nmat)]

    while line:
        domain = 1
        if Nmat != 1:
            x, y, z, domain = line.split()
        else:
            x, y, z = line.split()
        # for indexing
        domain = int(domain) - 1
        x_list[domain].append(int(x))
        y_list[domain].append(int(y))
        z_list[domain].append(int(z))

        line = file.readline()

    file.close()

    # try to plot this thing
    if mode == "full":

        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")
        for domain in range(Nmat):
            ax.scatter(x_list[domain], y_list[domain], z_list[domain], alpha=0.7, s=10)

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")

        ax.set_aspect("equal")

        plt.show()
    else:
        len_x = max(sum(x_list, []))
        len_y = max(sum(y_list, []))
        len_z = max(sum(z_list, []))

        particle = np.zeros((len_x + 1, len_y + 1, len_z + 1))
        for domain in range(Nmat):
            particle[x_list[domain], y_list[domain], z_list[domain]] = domain + 1

        # x, y = np.where(arr == 1)
        # I would like to make this smaller, as small as possible. so remove empty slices
        # x direction:
        i = 0
        while not np.any(particle[i]):
            i += 1
        print("first x:", i)

        # y direction:
        j = 0
        while not np.any(particle[:, j, :]):
            j += 1
        print("first y:", j)

        # z direction:
        k = 0
        while not np.any(particle[:, :, k]):
            k += 1
        print("first y:", k)

        particle_stripped = particle[i:, j:, k:]

        for i in range(len_x):

            plt.imshow(particle_stripped[i], cmap="hot", interpolation="none")
            # print(particle_stripped[i])
            plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("shapefile", help="shapefile to plot")
    parser.add_argument(
        "-m", "--mode", help="single slice or full particle", default="full"
    )
    args = parser.parse_args()
    if "slice" in args.mode:
        plot_shape(args.shapefile, mode="single")
    else:
        plot_shape(args.shapefile)
