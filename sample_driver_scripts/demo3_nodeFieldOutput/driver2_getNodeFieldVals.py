# ---------------------------------------------------------------------------------------------------------------------
# Coded for Python 2.7.3 (the current Python interpreter for Abaqus 2017)
# Script coded by NEWELL MOSER, September 25th, 2018
# PhD Candidate, Mechanical Engineering, Northwestern
#
# ----> DESCRIPTION <----
# This python script can extract nodal field value outputs at a given moment, or frame, from an Abaqus output database
# (.odb file). You must use the Abaqus terminal (also called Abaqus Command), and then submit it to the Abaqus 
# python interpreter using the following terminal command,
#   ...> abaqus python scriptname.py  
# where scriptname.py should be replaced with this script's name. This script is used to extract nodal field values
# from an .odb file and then write them out to a .csv file.
#
# ----> INPUTS <----
# See Comments Below
#
# ----> OUTPUTS & SIDE EFECTS <----
# 1) stdout - Various print statements sent to standard output as status updates on what the script is doing
# 2) text file - A .csv file is written (or overwritten) to the hard drive
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

# User defined modules
import abaqus_moser_utility_functions as am
import kinematicMain as egg

# USER TIP - Should run the "driver_getOdbFileStructure.py" script ahead of time in order to identify existing 
#            repository keys in your .odb file.
#
# --------------------------------> USER INPUTS <--------------------------------
#
# str - File path the Abaqus .odb file to be opened (as read-only)
odbFilePath_global = '../demo0_contactSimulation/hexContact.odb'
#
# odbStepPositionKey_global can be an index (input must be of type int) or the step name (input must be of type string)
# int - Index of the .odb simulation step. Example: Use 0 for the first, -1 for the last.
# str - Name of the repository key used to get the OdbStep object. 
odbStepPositionKey_global = 'dynExplicit'
#
# odbFramePosition_global can be an index (input must be of type int) or a step time (input must be type float)
# int - Index of the desired frame in the step. EX: Use 0 for the first, -1 for the last.
# float - Step time. The frame that is closest to the this step time will be used. 
odbFramePosition_global = 1.0
#
# odbSetStr_global can be either of the following:
# str - A string of the repository key of an existing Abaqus node OdbSet object representing the nodes to extract the field values
#       NOTE: If your .odb file contains duplicate node set repository keys (only different by the part instances), then this script
#       will grab the first one it finds. You will have to use a user-supplied node list to get the other set.
# str - If the supplied string ends with ".txt" or ".csv", then it is assumed to be a filepath to a user-supplied node list.
#       The file should use "*" at the beginning of a line to denote the name of the part instance that the subsequent nodes correspond 
#       to. Then, on the next line(s), a comma-separated list of integers (any number of rows and columns) representing the node
#       labels should be given. No header line should be present in the file. Node labels will be continuosly read-in until another 
#       "*" is found. An example of a file input for a custom node set that spans two part instances is given below:
#           *InstanceName1
#           11,12,13,14,
#           15,16,17,18,19
#           *InstanceName2
#           21,22,23,24,25,26
odbSetStr_global = './demo3p2_userNSet.csv' 
#
# str - The type of nodal field values to extract, or type of integration point field values to interpolate to the nodes (0% averaging).
#       If using a node field value, like 'U' for all displacement components, then fieldPosKey_global must be NODAL. If the field values
#       are to be interpolated from the integration point field, like 'S' for all stress components, then set fieldPosKey_global equal 
#       to ELEMENT_NODAL. 
fieldOutputKey_global = 'PEEQ'
#
# SymbolicConstant - Use NODAL or ELEMENT_NODAL (do not include quotes, this is not a string)
#       Use NODAL to extract field values that exist at the nodes (displacement, velocity, acceleration, contact pressure, etc.)
#       Use ELEMENT_NODAL to interpolate (much slower) integration point field values (0% averaging) to the nodes (stress, plastic strain, etc.)
#       If you use the wrong one for your corresponding fieldOutputKey_global, the script will crash with: "ERROR: Subfield is empty! Script is aborting"
fieldPosKey_global = ELEMENT_NODAL 
#
# str - Filepath to write the output data (as a .csv file). Existing files will be overwritten.
csvFieldValFilePath_global = './toolBacks_equivPlastStrn.csv'
#
# list[str] - A list of strings to be written out first in the .csv file (as a header line). The output columns for each field value 
#       locations will be: [NodeLabel, CoordX, CoordY, CoordZ, FieldVals...] where the coordinates are the current position of the node
csvFieldValFileHeader_global = ['Node Label', 'X1', 'X2', 'X3', 'PEEQ']
#
#---- A NOTE ON COORDINATE VALUES ----
# This script calculates the nodal coordinates using the intial position of the node in combination with the current displacement field.
# If the .odb file does not contain the keyword 'U' within the *NODE OUTPUT identifier in the input file, then this script may crash. 
#
# --------------------------------> END USER INPUTS <--------------------------------



# This is where all the magic happens. Lots and lots of magic... not going to talk about the inner magic of this function.
# INPUTS - See above.
#
# OUTPUTS
# fieldValsOut - If the supplied node set spans a single part instance, then a list[[float]]. If the supplied node set spans multiple 
#       part instances, then a list[ list[[float]] ]. Example, if the node set spans two instances named 'InstanceName1' and 'InstanceName2',
#       and the field output key is 'U', then fieldValsOut would be a list that contains two 2D-lists: one for each part instance. For 
#       both 2D-lists, the output would be multiple rows (one for each node in that part instance) with columns corresponding to U1, U2, and U3.
# instanceNames - If the node set spans multiple part instances, a list of strings (i.e., list[str]) of the names that correspond to the part 
#       instances that the first dimension of fieldValsOut. Otherwise if just one part/instance is used, this output will be equal to None.
#       Note that None in this case is Python's None-type object, not an actual string equal to 'None'.
fieldValsOut, instanceNames = am.getNodeFieldValuesFromSetBatch(odbFilePath_global, odbStepPositionKey_global, odbFramePosition_global, odbSetStr_global, fieldOutputKey_global, fieldPosKey_global)

if instanceNames is None:
    # Write the data out to a .csv file. If instanceName is None, then only one part instance was needed and fieldValsOut is a 2D array
    am.write2DListCSV(fieldValsOut, csvFieldValFilePath_global, csvFieldValFileHeader_global)
    print 'Script ended successfully!'
else:
    # 3D array since multiple instances are involved. Need to flatten to a 2D array for writing out
    numInstances = len(instanceNames)
    outValsList = []
    for instIndex in range(numInstances):
        curInstFieldVals = fieldValsOut[instIndex]
        curInstName = instanceNames[instIndex]
        numRows = len(curInstFieldVals)
        for curRowIndex in range(numRows):
            curRow = curInstFieldVals[curRowIndex]
            tempOutRow = curRow + [curInstName]
            outValsList.append(tempOutRow)
            
    # Write the data out to a .csv file. Will add a column with the instance name for each node
    csvFieldValFileHeader_out = csvFieldValFileHeader_global + ['Instance'] 
    am.write2DListCSV(outValsList, csvFieldValFilePath_global, csvFieldValFileHeader_out)
    print 'Script ended successfully!'


























































































































egg.easterEgg = False
if egg.easterEgg:
    print '\nYou started my Easter Egg!!! Have fun shooting :) \n'
    egg.runEasterEgg()

