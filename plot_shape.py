import matplotlib.pyplot as plt
import argparse


def plot_shape(shapefile):

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
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    for domain in range(Nmat):
        ax.scatter(x_list[domain], y_list[domain], z_list[domain], alpha=0.7, s=10)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    ax.set_aspect("equal")

    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("shapefile", help="shapefile to plot")
    args = parser.parse_args()
    plot_shape(args.shapefile)
