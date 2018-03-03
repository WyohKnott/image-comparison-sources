#!/usr/bin/python3
# Copyright 2017-2018 Wyoh Knott
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#     software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import os
import sys
import glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Cairo')
import matplotlib.pyplot as plt


def generate_plots(path, requested_formats):
    data = {}
    subset_name = os.path.basename(path)

    for format in requested_formats:
        file = path + "/" + subset_name + "." + format + ".lossy.out"
        data[format] = pd.read_csv(file, sep=":")

    plt.rcParams['svg.fonttype'] = 'svgfont'

    # Y-SSIM
    fig = plt.figure()
    plt.figure(figsize=(25, 15))
    plt.title(
        "Quality according to Y-SSIM in function of number of bits per pixel")
    plt.suptitle(subset_name)
    plt.xlabel("Bits per pixels")
    plt.ylabel("dB (Y-SSIM)")
    plt.xscale("log")
    plt.xlim([0.1, 2])
    plt.ylim([10, 20])
    plt.minorticks_on()
    plt.grid(b=True, which='both', color='0.65', linestyle='--')
    for format in data:
        plt.plot(
            data[format]["avg_bpp"],
            data[format]["wavg_y_ssim_score"],
            label=format)
    plt.legend()
    plt.savefig(path + "/" + subset_name + ".y-ssim.(" +
                ','.join(requested_formats) + ").svg")
    plt.close(fig)

    # RGB-SSIM
    fig = plt.figure()
    plt.figure(figsize=(25, 15))
    plt.title(
        "Quality according to RGB-SSIM in function of number of bits per pixel"
    )
    plt.suptitle(subset_name)
    plt.xlabel("Bits per pixels")
    plt.ylabel("dB (RGB-SSIM)")
    plt.xscale("log")
    plt.xlim([0.1, 2])
    plt.ylim([10, 20])
    plt.minorticks_on()
    plt.grid(b=True, which='both', color='0.65', linestyle='--')
    for format in data:
        plt.plot(
            data[format]["avg_bpp"],
            data[format]["wavg_rgb_ssim_score"],
            label=format)
    plt.legend()
    plt.savefig(path + "/" + subset_name + ".rgb-ssim.(" +
                ','.join(requested_formats) + ").svg")
    plt.close(fig)

    # MS-SSIM
    fig = plt.figure()
    plt.figure(figsize=(25, 15))
    plt.title(
        "Quality according to MS-SSIM in function of number of bits per pixel")
    plt.suptitle(subset_name)
    plt.xlabel("Bits per pixels")
    plt.ylabel("dB (MS-SSIM)")
    plt.xscale("log")
    plt.xlim([0.1, 2])
    plt.ylim([15, 35])
    plt.minorticks_on()
    plt.grid(b=True, which='both', color='0.65', linestyle='--')
    for format in data:
        plt.plot(
            data[format]["avg_bpp"],
            data[format]["wavg_msssim_score"],
            label=format)
    plt.legend()
    plt.savefig(path + "/" + subset_name + ".ms-ssim.(" +
                ','.join(requested_formats) + ").svg")
    plt.close(fig)

    fig = plt.figure()
    plt.figure(figsize=(25, 15))
    plt.title(
        "Quality according to PSNR-HVS-M in function of number of bits per pixel"
    )
    plt.suptitle(subset_name)
    plt.xlabel("Bits per pixels")
    plt.ylabel("dB (PSNR-HVS-M)")
    plt.xscale("log")
    plt.xlim([0.1, 2])
    plt.ylim([25, 50])
    plt.minorticks_on()
    plt.grid(b=True, which='both', color='0.65', linestyle='--')
    for format in data:
        plt.plot(
            data[format]["avg_bpp"],
            data[format]["wavg_psnrhvsm_score"],
            label=format)
    plt.legend()
    plt.savefig(path + "/" + subset_name + ".psnr-hvs-m.(" +
                ','.join(requested_formats) + ").svg")
    plt.close(fig)

    fig = plt.figure()
    plt.figure(figsize=(25, 15))
    plt.title(
        "Quality according to VMAF in function of number of bits per pixel")
    plt.suptitle(subset_name)
    plt.xlabel("Bits per pixels")
    plt.ylabel("Score (VMAF)")
    plt.xscale("log")
    plt.xlim([0.1, 2])
    plt.ylim([75, 100])
    plt.minorticks_on()
    plt.grid(b=True, which='both', color='0.65', linestyle='--')
    for format in data:
        plt.plot(
            data[format]["avg_bpp"],
            data[format]["wavg_vmaf_score"],
            label=format)
    plt.legend()
    plt.savefig("test.svg")
    plt.savefig(path + "/" + subset_name + ".vmaf.(" +
                ','.join(requested_formats) + ").svg")
    plt.close(fig)

    fig = plt.figure()
    plt.figure(figsize=(25, 15))
    plt.title("Encoding time in function of average bpp")
    plt.suptitle(subset_name)
    plt.xlabel("Bits per pixel")
    plt.ylabel("Time (s)")
    plt.xscale("log")
    plt.xlim([0.1, 2])
    plt.ylim([0, 25])
    plt.minorticks_on()
    plt.grid(b=True, which='both', color='0.65', linestyle='--')
    for format in data:
        plt.plot(
            data[format]["avg_bpp"],
            data[format]["wavg_encode_time"],
            label=format)
    plt.legend()
    plt.savefig("test.svg")
    plt.savefig(path + "/" + subset_name + ".encoding_time.(" +
                ','.join(requested_formats) + ").svg")
    plt.close(fig)
    
    plt.close("all")


def main(argv):
    if sys.version_info[0] < 3 and sys.version_info[1] < 5:
        raise Exception("Python 3.5 or a more recent version is required.")

    if len(argv) < 2 or len(argv) > 3:
        print(
            "Arg 1: Path to a subset with results generated by rd_average.py")
        print("       For ex: rd_average.py \"results/subset1\"")
        print("Arg 2: Comma-separated list of format to plot.")
        print(
            "       For ex: rd_average.py \"results/subset1\" \"bpg,mozjpeg,flif,vp9\""
        )

    results_folder = os.path.normpath(argv[1])

    if (not os.path.isdir(results_folder)
            or not glob.glob(results_folder + "/*.lossy.out")):
        print(
            "Could not find all results file. Please make sure the path provided is correct."
        )
        return

    available_formats = []
    for f in glob.glob(results_folder + "/*.lossy.out"):
        available_formats.append(os.path.basename(f).split(".")[1])

    try:
        requested_formats = [format.strip() for format in argv[2].split(",")]
    except IndexError:
        requested_formats = available_formats

    for format in requested_formats:
        if format not in available_formats:
            print("The format {} is not in the list of available formats {}".
                  format(format, available_formats))
            return

    generate_plots(results_folder, requested_formats)


if __name__ == "__main__":
    main(sys.argv)
