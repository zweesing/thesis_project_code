import os
import numpy as np




# read in file from optool for refractive indices
rfile = open("pyr-mg70-Dorschner1995.lnk", "r")

dum = rfile.readline()
header = ''

while dum.strip()[0]=='#':
    header = header + dum
    dum = rfile.readline()

# number of lambdas and rho
while len(dum.strip())<1: dum = rfile.readline() # skip any empty lines
nlam = int(dum.split()[0])
rho = float(dum.split()[1])

lamarr=np.zeros(nlam); narr=np.zeros(nlam); karr=np.zeros(nlam)

# Read the refractive indices
dum = rfile.readline()
while len(dum.strip())<1: dum = rfile.readline() # skip any empty lines
for ilam in range(nlam):
    dum           = dum.split()
    lamarr[ilam]     = float(dum[0]) # micron
    narr[ilam]    = float(dum[1])  
    karr[ilam]    = float(dum[2])

    dum = rfile.readline()

rfile.close()
# ----------------------------------------------------------------- #
# ----------------------------------------------------------------- #

# what we want
crosssec = np.zeros(100)

# a as defined by optool
a = 1 #micron

for i, lam in enumerate(lamarr):
    if lam < 1: # these take forever
        pass
    else:
    

        n = narr[i]
        k = karr[i]

        # hardcoded single folder
        os.system(f'cd adda_runs && adda -eq_rad {a} -lambda {lam} -m {n} {k}')
        