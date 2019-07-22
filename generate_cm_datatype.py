#!/usr/bin/env python3

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
        catalog[parcellation] = {"name": name, "label": label, "voxel_value": int(parcellation)}

labels = [ {"name": "self-loop", "desc": "index(x,x) is the diagonal"} ]

#parse the csv
with open(input_csv) as cm_csv:
    cm_lines = cm_csv.readlines()
    parcs = cm_lines[0].split(",")
    for parc in parcs[1:-14]:
        try:
            rec = catalog[parc.strip()]
            labels.append(rec)
        except:
            print("no %s in key.txt" % parc)

    #https://github.com/faskowit/app-fmri-2-mat/issues/5
    #last 14 are for 14 freesurferaseg  (https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/AnatomicalROI/FreeSurferColorLUT)
    f14 = [
            {"name": "Freesurfer Aseg / Left thalamus", "label": "10"},
            {"name": "Freesurfer Aseg / Left caudate", "label": "11"},
            {"name": "Freesurfer Aseg / Left putamen", "label": "12"},
            {"name": "Freesurfer Aseg / Left pallidum", "label": "13"},
            {"name": "Freesurfer Aseg / Left hippocampus", "label": "17"},
            {"name": "Freesurfer Aseg / Left amygdala", "label": "18"},
            {"name": "Freesurfer Aseg / Left accumbens", "label": "26"},

            {"name": "Freesurfer Aseg / Right thalamus", "label": "49"},
            {"name": "Freesurfer Aseg / Right caudate", "label": "50"},
            {"name": "Freesurfer Aseg / Right putamen", "label": "51"},
            {"name": "Freesurfer Aseg / Right pallidum", "label": "52"},
            {"name": "Freesurfer Aseg / Right hippocampus", "label": "53"},
            {"name": "Freesurfer Aseg / Right amygdala", "label": "54"},
            {"name": "Freesurfer Aseg / Right accumbens", "label": "58"},
    ]

    idx=0
    for parc in parcs[-14:]:
        labels.append({"name": f14[idx]["name"], "label": f14[idx]["label"], "voxel_value": int(parc)}) 
        idx+=1

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

