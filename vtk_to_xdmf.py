#!/usr/bin/env pvpython

# A tool to convert VTK timeseries into a single XDMF file
# with correct time from the individual VTK file headers.
#
# Ivan Markin, @unkaktus 2023

import vtk
from vtk.util.numpy_support import vtk_to_numpy
import glob
import os
import argparse
import shutil
import paraview.simple as pv

def mkdir_p(dir):
    try:
        os.makedirs(dir)
    except:
        pass

class VTK3D:
    def __init__(self, filename):
        self.load_file(filename)

    def set_data_from_header(self, header):
        if header.startswith("variable"):
            # variable ham, level 5, time  1.012500000e+01
            var_str, level_str, time_str = header.split(", ", 2)
            var_name = var_str.split(" ", 2)[1]
            self.var_name = var_name
            self.time = float(time_str.split(" ", 1)[1])
            self.extension = 'vti'
        if header.startswith("Apparent Horizon"):
            # Apparent Horizon 0, time=7982.500000
            self.time = float(header.split("time=", 1)[1])
            self.extension = 'vtu'
    def set_scalar_name(self, scalar_line):
        sp = scalar_line.split(' ')
        self.scalar_name = sp[1]

    def load_file(self, filename):
        with open(filename, 'rb') as file:
            file.readline() # skip first line
            header = file.readline().decode("utf-8").rstrip()
            self.set_data_from_header(header)
            scalars_found = False
            while True:
                line = file.readline().decode("utf-8")
                if line.startswith("SCALARS"):
                    scalars_found = True
                    break
            if not scalars_found:
                raise Exception("no SCALARS line found")
            self.set_scalar_name(line)

def vtk_to_single_pvd(filename, output_dir):
    name = os.path.splitext(os.path.basename(filename))[0]
    pvd_filename =  os.path.join(output_dir, f'{name}.pvd')
    reader = pv.OpenDataFile(filename)
    writer = pv.CreateWriter(pvd_filename, reader)
    writer.UpdatePipeline()

def write_timeseries_pvd(input_dir, output_filename):
    with open(output_filename, 'w') as f:
        f.write("""<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">
                <Collection>\n""")

        for filename in sorted(glob.glob(os.path.join(input_dir, '*.vtk'))):
            v = VTK3D(filename)
            name = os.path.splitext(os.path.basename(filename))[0]
            vt_filename = f'{name}/{name}_0.{v.extension}'
            f.write(f'            <DataSet timestep="{v.time}" file="{vt_filename}"/>\n')

        f.write("""</Collection>
            </VTKFile>
        """)

def convert_pvd_to_xdmf(filename, output_filename):
    reader = pv.OpenDataFile(filename)
    writer = pv.CreateWriter(output_filename, reader)
    writer.WriteAllTimeSteps = 1
    writer.UpdatePipeline()

def correct_variable_name(filename, scalar_name, var_name):
    with open(filename) as f:
        s = f.read()
    with open(filename, 'w') as f:
        s = s.replace(r'Name="'+scalar_name+'"', r'Name="'+var_name+'"')
        f.write(s)

def convert_vtk_to_xdmf(input_dir, output_dir, scratch_dir):
    filelist = sorted(glob.glob(os.path.join(input_dir, '*.vtk')))
    for filename in filelist:
        print(f'Converting {filename} to PVD')
        vtk_to_single_pvd(filename, scratch_dir)
    name = os.path.basename(input_dir)
    name = name.rstrip('_vtk')
    timeseries_filename = os.path.join(scratch_dir, f'{name}_timeseries.pvd')
    print(f"Creating timeseries: {timeseries_filename}")
    write_timeseries_pvd(input_dir, output_filename=timeseries_filename)

    output_filename = os.path.join(output_dir, f'{name}.xmf')
    print(f"Converting PVD timeseries to XDMF: {output_filename}")
    convert_pvd_to_xdmf(timeseries_filename, output_filename)
    print(f"Removing scratch directory: {scratch_dir}")
    shutil.rmtree(scratch_dir)
    print(f"Correcting the variable name in the XDMF file")
    first_vtk = VTK3D(filelist[0])
    if hasattr(first_vtk, 'var_name'):
        correct_variable_name(output_filename, first_vtk.scalar_name, first_vtk.var_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser('vtk_to_xdmf')
    parser.add_argument("--input-dir", type=str, help="Input directory", default=None)
    parser.add_argument("--output-dir", type=str, help="Output directory", default="")
    parser.add_argument("--scratch-dir", type=str, help="Scratch directory", default="scratch")
    args = parser.parse_args()

    mkdir_p(args.output_dir)
    mkdir_p(args.scratch_dir)

    convert_vtk_to_xdmf(args.input_dir.removesuffix('/'), args.output_dir, args.scratch_dir)
