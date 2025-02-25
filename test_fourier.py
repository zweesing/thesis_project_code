import numpy as np
import matplotlib.pyplot as plt

M = 40


def plot_heatmap(slice):
    plt.imshow(
        slice,
        cmap="hot",
        interpolation="nearest",
    )
    plt.show()


# make array to transform
Rijk = np.random.normal(loc=0, scale=1, size=(M, M, M))


Rijk = np.ones((M, M))
Rijk[10:-10, 10:-10] = 0
plot_heatmap(Rijk)
Rijk = np.fft.fftn(Rijk)
Rijk = np.fft.fftshift(Rijk)

plot_heatmap(np.abs(Rijk))

# uni = np.ones(M)
# plt.scatter(range(M), uni)
# plt.show()

# uni_tranformed = np.fft.fftn(uni)
# plt.scatter(range(M), uni_tranformed)
# plt.show()

# uni_tranformed = np.fft.fftshift(uni_tranformed)
# plt.scatter(range(M), uni_tranformed)
# plt.show()

from scipy.stats import norm

# M = 50

# x = np.arange(-M / 2, M / 2)
# # mean and var
# arr = norm.pdf(x, 0, 1)

# # print(arr)
# plt.plot(x, arr)
# plt.show()

# transformed = np.fft.fftn(arr)
# what = np.fft.fftshift(transformed)
# plt.plot(x, transformed)
# plt.plot(x, what, label="shift")
# plt.legend()
# plt.show()


# distances to the center 3d array. this is actually half a point off center? but it maches the algorithm.
# i_arr = np.arange(M) + 1
# j_arr = np.arange(M) + 1
# k_arr = np.arange(M) + 1

# print("making distances array...")
# d = np.sqrt(
#     (i_arr[:, np.newaxis, np.newaxis] - M / 2) ** 2
#     + (j_arr[np.newaxis, :, np.newaxis] - M / 2) ** 2
#     + (k_arr[np.newaxis, np.newaxis, :] - M / 2) ** 2
# )

# for i in range(M):
# print(np.abs(Rijk[i]))
# plot_heatmap(np.abs(Rijk[i]))
