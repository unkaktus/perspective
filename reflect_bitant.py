#!/usr/bin/env python3

# A tool to reflect data in XDMF files along z-direction
#
# Ivan Markin, @unkaktus 2023

import argparse
import os

import numpy as np
import h5py
import xml.dom.minidom as md

def string_to_floatlist(s):
    return [float(x) for x in s.split(' ')]

def string_to_intlist(s):
    return [int(x) for x in s.split(' ')]

def floatlist_to_string(fl):
    return ' '.join([str(f) for f in fl])

parser = argparse.ArgumentParser('reflect_bitant')
parser.add_argument("-i", type=str, help="Input filename without extension")
parser.add_argument("--ghost-points", type=int, default=6, help="Number of ghost points")
parser.add_argument("--no-compression", type=bool, default=False, help="Disable compression")
args = parser.parse_args()


if __name__ == "__main__":
    outfilename = args.i+'.reflected'
    ghost_points = args.ghost_points

    dom = md.parse(args.i+'.xmf')
    root = dom.documentElement

    ### Reflect XMF file
    print('[i] Reflecting XMF file')
    times = {}

    if root.childNodes:
        for domain_node in root.childNodes:
            if domain_node.nodeType != domain_node.ELEMENT_NODE:
                continue
            for collection_node in domain_node.childNodes:
                if collection_node.nodeType != collection_node.ELEMENT_NODE:
                    continue
                for grid_node in collection_node.childNodes:
                    if grid_node.nodeType != grid_node.ELEMENT_NODE:
                        continue
                    # Filter out duplicate times
                    time = grid_node.getElementsByTagName("Time")[0].attributes["Value"].value
                    if time in times:
                        collection_node.removeChild(grid_node)
                    else:
                        times[time] = True

                    topology = grid_node.getElementsByTagName("Topology")[0]
                    dimensions_text = topology.attributes["Dimensions"]
                    dimensions = string_to_intlist(dimensions_text.value)
                    dimensions[0] = (dimensions[0]-ghost_points)*2
                    dimensions_text.value = floatlist_to_string(dimensions)

                    attribute_node = grid_node.getElementsByTagName("Attribute")[0]
                    data_item = attribute_node.getElementsByTagName("DataItem")[0]
                    dimensions_text = data_item.attributes["Dimensions"]
                    dimensions = string_to_intlist(dimensions_text.value)
                    dimensions[0] = (dimensions[0]-ghost_points)*2
                    dimensions_text.value = floatlist_to_string(dimensions)

                    data_pointer = data_item.childNodes[0]
                    data_item_text = data_pointer.data
                    data_id = data_item_text.split(":")[1]
                    data_pointer.data = f'{outfilename}.h5:{data_id}'


                    geometry = grid_node.getElementsByTagName("Geometry")[0]

                    # Spacings
                    dx_text = geometry.getElementsByTagName("DataItem")[1].childNodes[0]
                    dx = string_to_floatlist(dx_text.data)
                    dz = dx[0]

                    # Origin
                    origin_text = geometry.getElementsByTagName("DataItem")[0].childNodes[0]
                    origin = string_to_floatlist(origin_text.data)
                    origin[0] = -dz*(dimensions[0]//2-0.5)
                    origin_text.data = floatlist_to_string(origin)

    dom.writexml(open(outfilename+'.xmf', "w"))

    ### Reflect HDF5 file
    print('[i] Reflecting HDF5 file')
    input_file = h5py.File(args.i+'.h5', 'r+')
    output_file = h5py.File(outfilename+'.h5', 'w')

    for key_n, key in enumerate(input_file.keys()):
        print(f"Reflecting timestep {key_n}/{len(input_file.keys())}")
        data = np.array(input_file[key])

        data = data[ghost_points:,:,:]
        data_reflected = np.flip(data, axis=0)
        data = np.concatenate((data_reflected, data), axis=0)

        if not args.no_compression:
            dset = output_file.create_dataset(key, data.shape, compression="gzip", compression_opts=1)
        else:
            dset = output_file.create_dataset(key, data.shape)
        dset[::] = data

    input_file.close()
    output_file.close()

    print('[+] Done.')