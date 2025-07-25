# import sys
import os

# 0.1 should be the max, 1.02 is the lowest I think
man = 0
# por from 0.8 to 3
por = 0
# os.system(f"python3 make_GRF.py -p {por} -m {man}")
for _ in range(6):
    for por in [0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 0]:
        # for man in [1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09, 1.1, 0]:
        os.system(f"python3 make_GRF.py -p {por} -m {man}")


# for man in np.arange(1.02, 1.101, 0.01):
#     os.system(f"python3 make_GRF.py -p {por} -m {man}")
