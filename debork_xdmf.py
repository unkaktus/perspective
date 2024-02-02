#!/usr/bin/env python3

# Debork the XDMF files produced by BAM.
# Ivan Markin, @unkaktus 2023,2024

import argparse
import os
import xml.dom.minidom as md
import numpy as np

parser = argparse.ArgumentParser('debork_xdmf.py')
parser.add_argument("-i", type=str, help="Input filename")
parser.add_argument("-o", type=str, help="Output filename")

def string_to_floatlist(s):
    return [float(x) for x in s.split(' ')]

def string_to_intlist(s):
    return [int(x) for x in s.split(' ')]

def floatlist_to_string(fl):
    return ' '.join([str(f) for f in fl])

args = parser.parse_args()

dom = md.parse(args.i)
root = dom.documentElement


def modify_dom(root):
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

                    # Flip origin
                    geometry = grid_node.getElementsByTagName("Geometry")[0]
                    origin_text = geometry.getElementsByTagName("DataItem")[0].childNodes[0]
                    origin = string_to_floatlist(origin_text.data)
                    origin_text.data = floatlist_to_string(origin[::-1])
                    print(f'origin: {origin_text.data}')

                    # Flip spacings
                    dx_text = geometry.getElementsByTagName("DataItem")[1].childNodes[0]
                    dx = string_to_floatlist(dx_text.data)
                    dx_text.data = floatlist_to_string(dx[::-1])
                    print(f'dx: {dx_text.data}')

                    # topology = grid_node.getElementsByTagName("Topology")[0]
                    # dimensions_text = topology.attributes["Dimensions"]
                    # dimensions = string_to_intlist(dimensions_text.value)
                    # dimensions_text.value = floatlist_to_string(dimensions[::-1])
                    # print(f'dimensions: {dimensions_text.value}')


modify_dom(root)
dom.writexml(open(args.o, "w"))
