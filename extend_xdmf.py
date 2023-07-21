#!/usr/bin/env python

# A tool to fix ParaView data cropping issue for 3D XDMF files
#
# It appends a magic negative timestep with maximal bounds
# to the specified XDMF file.
# The output XDMF file can be readily used in ParaView.
#
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
                    negativeGridNode =  grid_node.cloneNode(deep=True) # with all the fields
                    print(negativeGridNode)

                    attribute = negativeGridNode.getElementsByTagName("Attribute")[0]
                    print(attribute)
                    negativeGridNode.removeChild(attribute)

                    time = negativeGridNode.getElementsByTagName("Time")[0]
                    time.attributes["Value"] = "-1"

                    geometry = negativeGridNode.getElementsByTagName("Geometry")[0]
                    origin_text = geometry.getElementsByTagName("DataItem")[0].childNodes[0]

                    origin = string_to_floatlist(origin_text.data)
                    min_origin = np.min(origin)
                    origin_text.data = floatlist_to_string(np.full_like(origin, fill_value=min_origin))
                    print(origin_text.data)

                    topology = negativeGridNode.getElementsByTagName("Topology")[0]
                    topology_dimensions = topology.attributes["Dimensions"]
                    dims = string_to_intlist(topology_dimensions.value)
                    print(dims)
                    dim_max = np.max(dims)
                    topology_dimensions.value = floatlist_to_string(np.full_like(dims, fill_value=dim_max))
                    print(topology_dimensions.value)

                    newline = dom.createTextNode('\n')
                    collection_node.insertBefore(newline, grid_node)
                    collection_node.insertBefore(negativeGridNode, newline)

                    return
modify_dom(root)
dom.writexml(open(args.o, "w"))
