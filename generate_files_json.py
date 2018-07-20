#!/usr/bin/python3

import os
import json
import glob

data = {}
data['comparisonfiles'] = {}

for subset in next(os.walk("comparisonfiles/"))[1]:
    data['comparisonfiles'][subset] = {}
    data['comparisonfiles'][subset]["format"] = []
    format_list = [
        format
        for format in next(os.walk("comparisonfiles/" + subset + "/large"))[1]
    ]
    for format in format_list:
        extension = [
            os.path.splitext(os.path.basename(fn))[1][1:]
            for fn in glob.glob(
                "comparisonfiles/" + subset + "/large/" + format + "/*")
            if os.path.splitext(os.path.basename(fn))[1] != ".png"
        ][0]
        data['comparisonfiles'][subset]["format"].append({
            "extension": extension,
            "name": format
        })

    data['comparisonfiles'][subset]["format"].append({
        "extension": "png",
        "name": "Original"
    })

    filenames_list = [
        os.path.splitext(os.path.basename(files))[0]
        for files in next(
            os.walk("comparisonfiles/" + subset + "/Original/"))[2]
    ]
    data['comparisonfiles'][subset]["files"] = []
    for filename in filenames_list:
        data['comparisonfiles'][subset]["files"].append({
            "title": "",
            "filename": filename
        })

with open('comparisonfiles.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)
