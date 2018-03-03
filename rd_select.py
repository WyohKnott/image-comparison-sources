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
import errno
import subprocess
import sys
import glob
import shlex
import string
import json
from multiprocessing import Pool
from shutil import copy

# Paths to various programs and config files used by the tests #
# Conversion
convert = "ffmpeg"

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


def create_dir(path):
    if not os.path.exists(os.path.dirname(path)):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise


def path_for_file_in_tmp(path):
    return tmpdir + str(os.getpid()) + os.path.basename(path)


def convert_img(inn, out):
    cmd = "%s -y -i %s -pix_fmt yuv420p %s" % (convert, inn, out)
    run_silent(cmd)


def find_by_size(size, path):
    result = []
    files = [
        f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
    ]
    for f in files:
        if os.path.getsize(os.path.join(path, f)) == size:
            result.append(
                [os.path.join(f),
                 os.path.getsize(os.path.join(path, f))])
    if not result:
        print("Nothing of size %d was found" % size)
    return result


def find_closest_size(size, path):
    file_sizes = []
    result = []
    files = [
        f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))
    ]
    for f in files:
        file_sizes.append(os.path.getsize(os.path.join(path, f)))
    result = find_by_size(min(file_sizes, key=lambda x: abs(x - size)), path)
    if not result:
        print("Nothing of size close to %d was found" % size)
    return result[0][0]


def process_image(args):
    [format, format_recipe, subset_name, origpng] = args

    try:
        start = float(format_recipe['quality_start'])
        end = float(format_recipe['quality_end'])
        step = float(format_recipe['quality_step'])
    except ValueError:
        print('There was an error parsing the format recipe')
        return

    if (not format_recipe['encode_extension']
            or not format_recipe['decode_extension']
            or not format_recipe['encode_cmd']
            or not format_recipe['lossless_cmd']
            or not format_recipe['decode_cmd']):
        print('There was an error parsing the format recipe')
        return

    path = format.upper() + "_out/" + subset_name + "/" + os.path.splitext(
        os.path.basename(origpng))[0] + "/"
    target_path = "comparisonfiles/" + subset_name + "/"
    orig_target_path = target_path + "Original/"
    create_dir(orig_target_path)

    # Copy original
    copy(origpng, orig_target_path)

    # Lossless
    if not os.path.isdir(path):
        print(
            "Compressed image files not found in {}. You must run rd_collect first.".
            format(path))
        return

    lossless_target = [
        f for f in os.listdir(path)
        if f.startswith(
            os.path.splitext(os.path.basename(origpng))[0] + "-lossless")
    ]
    if not lossless_target[0]:
        print(
            "Compressed image files not found in {}. You must run rd_collect first.".
            format(path))
        return
    lossless_target = os.path.join(path, lossless_target[0])

    # BPG @ crf24
    ref_file = "BPG_out" + '/' + subset_name + "/" + os.path.splitext(
        os.path.basename(origpng))[0] + "/" + os.path.splitext(
            os.path.basename(origpng))[0] + "-q24.bpg"
    if not os.path.isfile(ref_file):
        print(
            "BPG reference file {} was not found. You must run rd_collect with BPG first.".
            format(ref_file))
        return

    large_size = os.path.getsize(ref_file)
    medium_size = large_size * 0.60
    small_size = medium_size * 0.60
    tiny_size = small_size * 0.60

    large_target = os.path.join(path, find_closest_size(large_size, path))
    medium_target = os.path.join(path, find_closest_size(medium_size, path))
    small_target = os.path.join(path, find_closest_size(small_size, path))
    tiny_target = os.path.join(path, find_closest_size(tiny_size, path))

    if not os.path.isfile(lossless_target) or not os.path.isfile(
            large_target) or not os.path.isfile(
                medium_target) or not os.path.isfile(
                    small_target) or not os.path.isfile(tiny_target):
        print(
            "Compressed image files not found in {}. You must run rd_collect first.".
            format(path))
        return

    lossless_target_path = os.path.join(
        target_path, "lossless/",
        format.upper() + "/",
        os.path.splitext(os.path.basename(lossless_target))[0].rsplit('-lossless',
                                                                      1)[0] +
        os.path.splitext(os.path.basename(lossless_target))[1])

    create_dir(lossless_target_path)
    copy(lossless_target, lossless_target_path)
    large_target_path = os.path.join(
        target_path, "large/",
        format.upper() + "/",
        os.path.splitext(os.path.basename(large_target))[0].rsplit(
            '-q', 1)[0] + os.path.splitext(os.path.basename(large_target))[1])
    create_dir(large_target_path)
    copy(large_target, large_target_path)
    medium_target_path = os.path.join(
        target_path, "medium/",
        format.upper() + "/",
        os.path.splitext(os.path.basename(medium_target))[0].rsplit(
            '-q', 1)[0] + os.path.splitext(os.path.basename(medium_target))[1])
    create_dir(medium_target_path)
    copy(medium_target, medium_target_path)
    small_target_path = os.path.join(
        target_path, "small/",
        format.upper() + "/",
        os.path.splitext(os.path.basename(small_target))[0].rsplit(
            '-q', 1)[0] + os.path.splitext(os.path.basename(small_target))[1])
    create_dir(small_target_path)
    copy(small_target, small_target_path)
    tiny_target_path = os.path.join(
        target_path, "tiny/",
        format.upper() + "/",
        os.path.splitext(os.path.basename(tiny_target))[0].rsplit(
            '-q', 1)[0] + os.path.splitext(os.path.basename(tiny_target))[1])
    create_dir(tiny_target_path)
    copy(tiny_target, tiny_target_path)

    files_list = [
        lossless_target_path, large_target_path, medium_target_path,
        small_target_path, tiny_target_path
    ]

    if format_recipe['export_to_png']:
        for target in files_list:
            target_dec = path_for_file_in_tmp(target)
            target_dec += "." + format_recipe['decode_extension']
            cmd = string.Template(format_recipe['decode_cmd']).substitute(
                locals())
            run_silent(cmd)
            convert_img(target_dec, os.path.splitext(target)[0] + ".png")
            try:
                os.remove(target_dec)
            except FileNotFoundError:
                pass


def main(argv):
    if sys.version_info[0] < 3 and sys.version_info[1] < 5:
        raise Exception("Python 3.5 or a more recent version is required.")

    data = {}
    try:
        with open('recipes.json') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        print("Could not find recipes.json")
        return

    supported_formats = list(data['recipes'].keys())

    if len(argv) != 4:
        print("rd_select.py: Select images among the ones generated by rd_collect.py at fifth quality levels (lossless, large, medium, small and tiny)")
        print("Arg 1: format to test {}".format(supported_formats))
        print("Arg 2: name of the subset to test (e.g. 'subset1')")
        print("Arg 3: path to subset to test (e.g. 'subset1')")
        return

    format = argv[1]
    subset_name = argv[2]
    if format not in supported_formats:
        print("Image format not supported!")
        return

    Pool().map(process_image, [(format, data['recipes'][format], subset_name,
                                origpng)
                               for origpng in glob.glob(os.path.normpath(argv[3]) + "/*.png")])


if __name__ == "__main__":
    main(sys.argv)
