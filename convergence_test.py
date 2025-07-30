import os

dir_run = "convergence_tests/coated_sphere_4-5_runs"

dirs = os.listdir(dir_run)
dirs.sort()
dirs = dirs[3:]
for dir in dirs:
    os.system(f"python3 my_program.py -r {dir_run}/{dir}")
