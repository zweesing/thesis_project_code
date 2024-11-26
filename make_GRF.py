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
M = 4
# size of particles
rho = 1

# construct random points
Rijk = np.random.rand(M, 3)


# distances to the center
d = np.sqrt(
    (Rijk[:, 0] - M / 2) ** 2 + (Rijk[:, 1] - M / 2) ** 2 + (Rijk[:, 2] - M / 2) ** 2
)

# construct the field
Gijk = Rijk * np.exp(-rho * d[:, None] ** 2)

# we need to take the 3d fourier transform. ( not sure how this function wants the input to look like and what axes to specify) (axes=[0,1] or [1,0] does not change anything)
GijkF = np.fft.fftn(Gijk, axes=[0, 1])
print(GijkF)
print(" ")
print(np.fft.fftn(Gijk))
# normalise
GijkF = GijkF / np.max(GijkF, 1)[:, None]

# all points where GijF is > 0.5 are inside the particle. this Is unclear because the fourier transform does not return single value per point, but the transformed coordinates (complex).
# do I take the length of the fourier transformed vector?
