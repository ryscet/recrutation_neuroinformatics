#!/usr/bin/env python

# encoding: utf-8i
import Handler
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import epoch2num
import locale
from ExperimentConfigFile import ExperimentConfigFile
import pickle
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

_path = 'data'
_smells = {'data': {'soc': 3, 'nsoc': 1}}
data = pickle.load(open(os.path.join('data', 'data.pickle'), 'rb'))
mice = pickle.load(open(os.path.join('data', 'mice.pickle'), 'rb'))
phases = ExperimentConfigFile(_path)
