#!/usr/bin/env python3

# Rename the variable in an XDMF file,
# assuming that it is the only variable there.

# Ivan Markin, @unkaktus 2023

import argparse
import os
import xml.dom.minidom as md
import numpy as np

parser = argparse.ArgumentParser('extend_xdmf')
parser.add_argument("-i", type=str, help="Input filename")
parser.add_argument("-o", type=str, help="Output filename")
parser.add_argument("-varname", type=str, help="New variable name to set")


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
                    attribute = grid_node.getElementsByTagName("Attribute")[0]
                    varname_text = attribute.attributes["Name"]
                    varname_text.value = args.varname


modify_dom(root)
dom.writexml(open(args.o, "w"))
