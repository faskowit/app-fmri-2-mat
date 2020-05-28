FROM ubuntu:18.04
MAINTAINER j faskowitz <jfaskowi@iu.edu>

# pip and jq
RUN apt-get update && apt-get install -y python3-pip jq && apt clean

# python packages
RUN pip3 install numpy scipy nibabel==3.1.0 pandas==0.25.3 scikit-learn==0.23.0 nilearn==0.6.2 h5py==2.10.0

#make it work under singularity
RUN ldconfig && mkdir -p /N/u /N/home /N/dc2 /N/soft

#https://wiki.ubuntu.com/DashAsBinSh
RUN rm /bin/sh && ln -s /bin/bash /bin/sh
