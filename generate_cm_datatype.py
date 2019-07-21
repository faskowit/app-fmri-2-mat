#!/usr/bin/env python

import json
import os
import shutil

with open('config.json') as config_file:
    config = json.load(config_file)

input_csv = "output_makemat/out_parc_correlation_connMatdf.csv"

#parse key file
catalog = dict()
with open(config["key"]) as key_file:
    key_lines = key_file.readlines();
    for line in key_lines:
        tokens = line.split("\t")
        label = tokens[0]
        parcellation = tokens[2]
        name_comp = tokens[3].split(" ") #== rh.R_V4t_ROI.label \n
        name = name_comp[1]
        catalog[parcellation] = {"name": name, "label": label, "parcellation": int(parcellation)}

labels = [ {"name": None, "desc": "index-0 is the diagonal"} ]

#parse the csv
with open(input_csv) as cm_csv:
    cm_lines = cm_csv.readlines()
    cols = cm_lines[0].split(",")
    for col in cols[1:]:
        try:
            rec = catalog[col.strip()]
            labels.append(rec)
        except:
            print("no %s in key.txt" % col)
        #print(rec)

    #for line in cm_lines[1:]:
    #    None
    #    #print(line)

if not os.path.exists("cm"):
    os.makedirs("cm")

with open("cm/cm.csv", "w") as cm_csv:
    lines = cm_lines[1:]
    csv = []
    for line in lines:
        line = line.strip().split(",")[1:]
        csv.append(",".join(line))
    cm_csv.write("\n".join(csv))

with open("cm/label.json", "w") as label_file:
    json.dump(labels, label_file, indent=4)

