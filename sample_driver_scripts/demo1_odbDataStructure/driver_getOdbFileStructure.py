# ---------------------------------------------------------------------------------------------------------------------
# Coded for Python 2.7.3 (the current Python interpreter for Abaqus 2017)
# Script coded by NEWELL MOSER, September 25th, 2018
# PhD Candidate, Mechanical Engineering, Northwestern
#
# ----> DESCRIPTION <----
# This python script opens an Abaqus .odb file and explores the data structure. It looks for existing keywords for
# repositories (which is a Abaqus Python API data structure that is very similar to Python's dict data type). These
# keywords are then written out to a text file in an organized format. These keywords are necessary in order to 
# gain access to the .odb simulation data like field values and history outputs. To use this script, you must use the 
# the Abaqus terminal (also called Abaqus Command), and then submit it to the Abaqus python interpreter using the 
# following terminal command,
#   ...> abaqus python scriptname.py  
# where scriptname.py should be replaced with this script's name.
#
# ----> INPUTS <----
# See Comments Below
#
# ----> OUTPUTS & SIDE EFECTS <----
# 1) stdout - Various print statements sent to standard output as status updates on what the script is doing
# 2) text file - A text file is written (or overwritten) to the hard drive
# ---------------------------------------------------------------------------------------------------------------------

# Abaqus imports
from odbAccess import *
from abaqusConstants import *

# Python imports
import csv
from math import *
import shutil
import os
import numpy as np

# User-defined modules
import abaqus_moser_utility_functions as am
import kinematicMain as egg

# --------------------------------> USER INPUTS <--------------------------------
#
# 1) str - File path to .odb to be opened (as read only)
odbFilePath_global = '../demo0_contactSimulation/hexContact.odb'
#
# 2) str - File path to a text file that will be created/over-written as output
dataStructFilePath_global = './hexContactOdb_dataStruct.txt'
#
# --------------------------------> END USER INPUTS <--------------------------------


am.writeOutAllKeysInAbqODB(odbFilePath_global, dataStructFilePath_global)







































































































































































































egg.easterEgg = False
if egg.easterEgg:
    print '\nYou started my Easter Egg!!! Have fun shooting :) \n'
    egg.runEasterEgg()