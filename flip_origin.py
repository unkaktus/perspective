#!/usr/bin/env python3

# Flip the origin of the data for all the timesteps
# to allow interoperability with buggy XDMF readers.

# Ivan Markin, @unkaktus 2023

import argparse
import os
import xml.dom.minidom as md
import numpy as np

parser = argparse.ArgumentParser('extend_xdmf')
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
                    geometry = grid_node.getElementsByTagName("Geometry")[0]
                    origin_text = geometry.getElementsByTagName("DataItem")[0].childNodes[0]
                    origin = string_to_floatlist(origin_text.data)
                    print(f'{origin[::-1]}')
                    origin_text.data = floatlist_to_string(origin[::-1])
                    # print(origin_text.data)


modify_dom(root)
dom.writexml(open(args.o, "w"))
