# make porous gaussian random field particles according to M. Min et al 2007

import numpy as np
import matplotlib.pyplot as plt


def plot3d(arr):
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")

    ax.scatter(arr[:, 0], arr[:, 1], arr[:, 2])

    ax.set_xlabel("i")
    ax.set_ylabel("j")
    ax.set_zlabel("k")

    ax.set_aspect("equal")

    plt.show()


# number of points
M = 5
# size of particles
rho = 1

# construct random points
Rijk = np.random.rand(M, 3)
plot3d(Rijk)

# distances to the center
d = np.sqrt(
    (Rijk[:, 0] - M / 2) ** 2 + (Rijk[:, 1] - M / 2) ** 2 + (Rijk[:, 2] - M / 2) ** 2
)

# construct the field
Gijk = Rijk * np.exp(-rho * d[:, None] ** 2)
plot3d(Gijk)
# we need to take the 3d fourier transform
GijkF = np.fft.fftn(Gijk)
# normalise
GijkF = GijkF / GijkF.max()

# all points where GijF is > 0.5 are inside the particle. this Is unclear because the fourier transform does not return single values per point, but 3 coordinates (complex).
# I may not understand 3d fourier transforms
