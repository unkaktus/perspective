#!/usr/bin/env python3

# A tool to reflect data in XDMF files along z-direction
# (Supports only HDF5 for now)
#
# Ivan Markin, @unkaktus 2023

import numpy as np
import h5py

import argparse
import os

parser = argparse.ArgumentParser('reflect_bitant')
parser.add_argument("-i", type=str, help="Input filename")
parser.add_argument("-o", type=str, help="Output filename")
parser.add_argument("--ghost-points")
args = parser.parse_args()


ghost_points = 6


input_file = h5py.File(args.i, 'r+')

output_file = h5py.File(args.o, 'w')

for key_n, key in enumerate(input_file.keys()):
    print(f"Handling key {key_n}/{len(input_file.keys())}")
    data = np.array(input_file[key])

    data = data[ghost_points:,:,:]
    data_reflected = np.flip(data, axis=0)
    data = np.concatenate((data_reflected, data), axis=0)

    output_file[key] = data
    print(f'Output shape: {data.shape}')

input_file.close()
output_file.close()