#!/usr/bin/python3
# Copyright 2013, Mozilla Corporation
# Copyright 2017, Wyoh Knott
# Loosely based on a script written by Josh Aas
# https://github.com/bdaehlie/web_image_formats
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
import errno
import subprocess
import sys
import glob
import re
import shlex
import string
import json
from multiprocessing import Pool
from timeit import Timer
import numpy as np

# Paths to various programs and config files used by the tests #
# Conversion
convert = "ffmpeg"

# Tests
rgbssim = "dump_ssim"
yssim = "dump_ssim -y"
psnrhvsm = "dump_psnrhvs -y"
msssim = "dump_msssim -y"
vmaf = "vmafossexec yuv420p"

# Path to tmp dir to be used by the tests
tmpdir = "/tmp/"

#############################################################################


def split(cmd):
    lex = shlex.shlex(cmd)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ''
    return list(lex)


def run_silent(cmd):
    FNULL = open(os.devnull, 'w')
    rv = subprocess.call(split(cmd), stdout=FNULL, stderr=FNULL)
    if rv != 0:
        sys.stderr.write("Failure from subprocess:\n")
        sys.stderr.write("\t" + cmd + "\n")
        sys.stderr.write("Aborting!\n")
        sys.exit(rv)
    return rv


def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)

    return wrapped


def create_dir(path):
    if not os.path.exists(os.path.dirname(path)):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise


def path_for_file_in_tmp(path):
    return tmpdir + str(os.getpid()) + os.path.basename(path)


def get_img_width(path):
    cmd = "identify -format %%w %s" % (path)
    proc = subprocess.Popen(
        split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8")
    out, err = proc.communicate()
    if proc.returncode != 0:
        sys.stderr.write("Failed process: identify\n")
        sys.exit(proc.returncode)
    lines = out.split(os.linesep)
    return int(lines[0].strip())


def get_img_height(path):
    cmd = "identify -format %%h %s" % (path)
    proc = subprocess.Popen(
        split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8")
    out, err = proc.communicate()
    if proc.returncode != 0:
        sys.stderr.write("Failed process: identify\n")
        sys.exit(proc.returncode)
    lines = out.split(os.linesep)
    return int(lines[0].strip())


def convert_img(inn, out):
    cmd = "%s -y -i %s -pix_fmt yuv420p %s" % (convert, inn, out)
    run_silent(cmd)


def score_y_ssim(y4m1, y4m2):
    cmd = "%s %s %s" % (yssim, y4m1, y4m2)
    proc = subprocess.Popen(
        split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8")
    out, err = proc.communicate()
    if proc.returncode != 0:
        sys.stderr.write("Failed process: %s\n" % (yssim))
        sys.exit(proc.returncode)
    lines = out.split(os.linesep)
    qscore = float(re.search('(?<=Total: )\d+\.?\d*', lines[-2]).group(0))
    return qscore


def score_psnrhvsm(y4m1, y4m2):
    cmd = "%s %s %s" % (psnrhvsm, y4m1, y4m2)
    proc = subprocess.Popen(
        split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8")
    out, err = proc.communicate()
    if proc.returncode != 0:
        sys.stderr.write("Failed process: %s\n" % (psnrhvsm))
        sys.exit(proc.returncode)
    lines = out.split(os.linesep)
    qscore = float(re.search('(?<=Total: )\d+\.?\d*', lines[-2]).group(0))
    return qscore


def score_rgb_ssim(y4m1, y4m2):
    cmd = "%s %s %s" % (rgbssim, y4m1, y4m2)
    proc = subprocess.Popen(
        split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8")
    out, err = proc.communicate()
    if proc.returncode != 0:
        sys.stderr.write("Failed process: %s\n" % (rgbssim))
        sys.exit(proc.returncode)
    lines = out.split(os.linesep)
    qscore = float(re.search('(?<=Total: )\d+\.?\d*', lines[-2]).group(0))
    return qscore


def score_msssim(y4m1, y4m2):
    cmd = "%s %s %s" % (msssim, y4m1, y4m2)
    proc = subprocess.Popen(
        split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8")
    out, err = proc.communicate()
    if proc.returncode != 0:
        sys.stderr.write("Failed process: %s\n" % (msssim))
        sys.exit(proc.returncode)
    lines = out.split(os.linesep)
    qscore = float(re.search('(?<=Total: )\d+\.?\d*', lines[-2]).group(0))
    return qscore


def score_vmaf(width, height, yuv1, yuv2):
    cmd = "%s %s %s %s %s %s" % (vmaf, width, height, yuv1, yuv2,
                                 "vmaf_v0.6.1.pkl")
    proc = subprocess.Popen(
        split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8")
    out, err = proc.communicate()
    if proc.returncode != 0:
        sys.stderr.write("Failed process: %s\n" % (vmaf))
        sys.exit(proc.returncode)
    lines = out.split(os.linesep)
    qscore = float(
        re.search('(?<=VMAF score = )\d+\.?\d*', lines[-2]).group(0))
    return qscore


# Returns tuple containing:
#   (target_file_size, encode_time, decode_time)
def get_lossless_results(subset_name, origpng, format, format_recipe):

    origpng_y4m = path_for_file_in_tmp(origpng) + ".y4m"
    convert_img(origpng, origpng_y4m)
    origpng_ppm = path_for_file_in_tmp(origpng) + ".ppm"
    convert_img(origpng, origpng_ppm)

    target = format.upper() + "_out/" + subset_name + "/" + os.path.splitext(
        os.path.basename(origpng))[0] + "/" + os.path.splitext(
            os.path.basename(origpng))[0] + "-lossless"
    create_dir(target)
    target_dec = path_for_file_in_tmp(target)

    target += "." + format_recipe['encode_extension']
    cmd = string.Template(format_recipe['lossless_cmd']).substitute(locals())
    wrapped = wrapper(run_silent, cmd)
    encode_time = Timer(wrapped).timeit(5)

    target_dec += "." + format_recipe['decode_extension']
    cmd = string.Template(format_recipe['decode_cmd']).substitute(locals())
    wrapped = wrapper(run_silent, cmd)
    decode_time = Timer(wrapped).timeit(5)

    target_file_size = os.path.getsize(target)

    try:
        os.remove(origpng_y4m)
        os.remove(origpng_ppm)
        os.remove(target_dec)
    except FileNotFoundError:
        pass

    return (target_file_size, encode_time, decode_time)


# Returns tuple containing:
#   (target_file_size, encode_time, decode_time, yssim_score, rgbssim_score,
#   psnrhvsm_score, msssim_score)
def get_lossy_results(subset_name, origpng, width, height, format,
                      format_recipe, quality):
    origpng_y4m = path_for_file_in_tmp(origpng) + ".y4m"
    convert_img(origpng, origpng_y4m)
    origpng_yuv = path_for_file_in_tmp(origpng) + ".yuv"
    convert_img(origpng, origpng_yuv)
    origpng_ppm = path_for_file_in_tmp(origpng) + ".ppm"
    convert_img(origpng, origpng_ppm)

    target = format.upper() + "_out/" + subset_name + "/" + os.path.splitext(
        os.path.basename(origpng))[0] + "/" + os.path.splitext(
            os.path.basename(origpng))[0] + "-q" + str(quality)
    create_dir(target)
    target_dec = path_for_file_in_tmp(target)

    target += "." + format_recipe['encode_extension']
    cmd = string.Template(format_recipe['encode_cmd']).substitute(locals())
    wrapped = wrapper(run_silent, cmd)
    encode_time = Timer(wrapped).timeit(1)

    target_dec += "." + format_recipe['decode_extension']
    cmd = string.Template(format_recipe['decode_cmd']).substitute(locals())
    wrapped = wrapper(run_silent, cmd)
    decode_time = Timer(wrapped).timeit(1)

    if format_recipe['decode_extension'] == 'y4m':
        target_y4m = target_dec
    else:
        target_y4m = path_for_file_in_tmp(target_dec) + ".y4m"
        convert_img(target_dec, target_y4m)

    if format_recipe['decode_extension'] == 'yuv':
        target_yuv = target_dec
    else:
        target_yuv = path_for_file_in_tmp(target_dec) + ".yuv"
        convert_img(target_dec, target_yuv)

    yssim_score = score_y_ssim(origpng_y4m, target_y4m)
    rgb_ssim_score = score_rgb_ssim(origpng_y4m, target_y4m)
    psnrhvsm_score = score_psnrhvsm(origpng_y4m, target_y4m)
    msssim_score = score_msssim(origpng_y4m, target_y4m)
    vmaf_score = score_vmaf(width, height, origpng_yuv, target_yuv)

    target_file_size = os.path.getsize(target)

    try:
        os.remove(origpng_yuv)
        os.remove(origpng_y4m)
        os.remove(origpng_ppm)
        os.remove(target_dec)
        os.remove(target_yuv)
        os.remove(target_y4m)
    except FileNotFoundError:
        pass

    return (target_file_size, encode_time, decode_time, yssim_score,
            rgb_ssim_score, msssim_score, psnrhvsm_score, vmaf_score)


def process_image(args):
    [format, format_recipe, subset_name, origpng] = args

    result_file = "results/" + subset_name + "/" + format + "/lossy/" + \
        os.path.splitext(os.path.basename(origpng))[0] + "." + format + ".out"
    if os.path.isfile(result_file) and not os.stat(result_file).st_size == 0:
        return


    try:
        isfloat = isinstance(format_recipe['quality_start'], float) or isinstance(format_recipe['quality_end'], float) or isinstance(format_recipe['quality_step'], float)
        
        if isfloat:
            start = float(format_recipe['quality_start'])
            end = float(format_recipe['quality_end'])
            step = float(format_recipe['quality_step'])
        else:
            start = int(format_recipe['quality_start'])
            end = int(format_recipe['quality_end'])
            step = int(format_recipe['quality_step'])
    except ValueError:
        print('There was an error parsing the format recipe.')
        return

    if (not format_recipe['encode_extension']
            or not format_recipe['decode_extension']
            or not format_recipe['encode_cmd']
            or not format_recipe['lossless_cmd']
            or not format_recipe['decode_cmd']):
        print('There was an error parsing the format recipe.')
        return

    orig_file_size = os.path.getsize(origpng)
    width = get_img_width(origpng)
    height = get_img_height(origpng)
    pixels = width * height

    # Lossless
    print("Processing image {}, quality lossless".format(
        os.path.basename(origpng)))

    path = "results/" + subset_name + "/" + format + "/lossless/" + os.path.splitext(
        os.path.basename(origpng))[0] + "." + format + ".out"
    create_dir(path)
    file = open(path, "w")

    file.write(
        "file_name:orig_file_size:compressed_file_size:pixels:bpp:compression_ratio:encode_time:decode_time\n"
    )

    results = get_lossless_results(subset_name, origpng, format, format_recipe)
    bpp = results[0] * 8 / pixels
    compression_ratio = orig_file_size / results[0]
    file.write("%s:%d:%d:%d:%f:%f:%f:%f\n" %
               (os.path.splitext(os.path.basename(origpng))[0], orig_file_size,
                results[0], pixels, bpp, compression_ratio, results[1],
                results[2]))

    file.close()

    # Lossy
    path = "results/" + subset_name + "/" + format + "/lossy/" + os.path.splitext(
        os.path.basename(origpng))[0] + "." + format + ".out"
    create_dir(path)
    file = open(path, "w")

    file.write(
        "file_name:quality:orig_file_size:compressed_file_size:pixels:bpp:compression_ratio:encode_time:decode_time:y_ssim_score:rgb_ssim_score:msssim_score:psnrhvsm_score:vmaf_score\n"
    )
    if isfloat:
        quality_list = list(np.arange(start, end, step))
    else:
        quality_list = list(range(start, end, step))

    i = 0
    while i < len(quality_list):
        quality = quality_list[i]
        print("Processing image {}, quality {}".format(
            os.path.basename(origpng), quality))
        results = get_lossy_results(subset_name, origpng, width, height,
                                    format, format_recipe, quality)
        bpp = results[0] * 8 / pixels
        compression_ratio = orig_file_size / results[0]
        file.write("%s:%f:%d:%d:%d:%f:%f:%f:%f:%f:%f:%f:%f:%f\n" %
                   (os.path.splitext(os.path.basename(origpng))[0], quality,
                    orig_file_size, results[0], pixels, bpp, compression_ratio,
                    results[1], results[2], results[3], results[4], results[5],
                    results[6], results[7]))
        i += 1

    file.close()


def main(argv):
    if sys.version_info[0] < 3 and sys.version_info[1] < 5:
        raise Exception("Python 3.5 or a more recent version is required.")

    data = {}
    try:
        with open('recipes.json') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        raise Exception("Could not find recipes.json")

    supported_formats = list(data['recipes'].keys())

    if len(argv) != 4:
        print(
            "rd_collect.py: Generate compressed images from PNGs and calculate quality and speed metrics for a given format"
        )
        print("Arg 1: format to test {}".format(supported_formats))
        print("Arg 2: name of the subset to test (e.g. 'subset1')")
        print("Arg 3: path to the subset to test (e.g. 'subset1/')")
        return

    format = argv[1]
    subset_name = argv[2]
    if format not in supported_formats:
        print("Image format not supported. Supported formats are: {}.".format(
            supported_formats))
        return

    Pool().map(process_image, [(format, data['recipes'][format], subset_name,
                                origpng)
                               for origpng in glob.glob(argv[3] + "/*.png")])


if __name__ == "__main__":
    main(sys.argv)
