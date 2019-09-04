# ---------------------------------------------------------------------------------------------------------------------
# Coded for Python 2.7.3 (the current Python interpreter for Abaqus 2017)
# Script coded by NEWELL MOSER, September 25th, 2018
# PhD Candidate, Mechanical Engineering, Northwestern
#
# ----> DESCRIPTION <----
# This python script can extract integration point field value outputs at a given moment, or frame, from an Abaqus 
# output database (.odb file). You must use the Abaqus terminal (also called Abaqus Command), and then submit it to 
# the Abaqus python interpreter using the following terminal command,
#   ...> abaqus python scriptname.py  
# where scriptname.py should be replaced with this script's name. This script is used to extract integration point 
# field values from an .odb file and then write them out to a .csv file. 
#
# NOTE: This script prefers that all of the elements used to extract field value outputs are of the same type. If 
#       the set includes elements of multiple types (which have a different number of integration points), then
#       the output data will be shaped large enough to account for the element with the maximum number of integration
#       points. Consequently for elements with fewer integration points, the written out data will be padded with
#       zeros. 
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
# str - A string of the repository key of an existing Abaqus element OdbSet object representing the elements to extract the field values
#       NOTE: If your .odb file contains duplicate element set repository keys (only different by the part instances), then this script
#       will grab the first one it finds. You will have to use a user-supplied element list to get the other set.
# str - If the supplied string ends with ".txt" or ".csv", then it is assumed to be a filepath to a user-supplied element list.
#       The file should use "*" at the beginning of a line to denote the name of the part instance that the subsequent nodes correspond 
#       to. Then, on the next line(s), a comma-separated list of integers (any number of rows and columns) representing the element
#       labels should be given. No header line should be present in the file. Element labels will be continuosly read-in until another 
#       "*" is found. An example of a file input for a custom element set that spans two part instances is given below:
#           *InstanceName1
#           11,12,13,14,
#           15,16,17,18,19
#           *InstanceName2
#           21,22,23,24,25,26
odbSetStr_global = 'SHEETTOP_ELSET'
#
# str - The integration point field values output to extract. 
fieldOutputKey_global = 'S' # Examples: 'PEEQ' for the equivalent plastic strain, or 'S' for all stress components.
#
# SymbolicConstant - Use INTEGRATION_POINT or CENTROID (do not include quotes, this is not a string)
#       Use INTEGRATION_POINT to extract field values at all of the integration points for each element
#       Use CENTROID to interpolate and average the integration point field values to the centroid of each element 
fieldPosKey_global = CENTROID
#
# str - Filepath to write the output data (as a .csv file). Existing files will be overwritten.
csvFieldValFilePath_global = './topOfSheet_sigCentroid.csv'
#
# list[str] - A list of strings to be written out first in the .csv file (as a header line). Note, if you choose to use INTEGRATION_POINT
#       for fieldPosKey_global, then this script will automatically append '_IP#' to the coordinate and field value header labels, where IP 
#       stands for integration point and # will be replaced with an integer corresponding to integration point labels. Just write the header 
#       labels as you would normally for a single field value point. The output columns for each field value locations will be: 
#       [ElementLabel, CoordX, CoordY, CoordZ, FieldVals...] where the coordinates will be at the centroid or integration point itself, 
#       depending on what is given in fieldPosKey_global. 
csvFieldValFileHeader_global = ['Element Label', 'X1', 'X2', 'X3', 'S11', 'S22', 'S33', 'S12', 'S13', 'S23']
#
# ---- A NOTE ON COORDINATE VALUES ----
# If the .odb file contains the COORD keyword within the input file indentifier, *ELEMENT OUTPUT, then this script will use this field
# value output to determine the coordinates of the centroid or integration points. The COORD keyword must be entered manually in the input
# file, otherwise Abaqus CAE will only include the COORD keyword in the *NODE OUTPUT identifier, which does not provide the coordinates of 
# the integration points. If the COORD keyword does not exist, then the script will attempt to calculate the coordinates of the integration
# points (or element centroid) manually using element shape functions, which sucks to code. Hence, only a few element types are currently 
# supported. The code will write out zeros for the coordinates if an unsupported element type is discovered. To handle a specific case, the 
# user can code additional shape function routines in the "abaqus_moser_shape_functions.py" script. To do so, add the additional element type
# to the if-elif statement in getCorrectShapeFunc(...) and call your own shape function routine.
#
# CURRENTLY SUPPORTED ELEMENT TYPES: C3D8R, C3D8RH, C3D8, C3D8H, C3D8I, C3D8IH, C3D20R, C3D20RH, C3D4, C3D4H, C3D10, C3D10H, C3D10M, C3D10MH
#
# --------------------------------> END USER INPUTS <--------------------------------



# This is where all the magic happens. Lots and lots and lots of magic... not going to talk about the inner magic of this function.
# INPUTS - See above.
#
# OUTPUTS
# fieldValsOut - A 4D list where the indices, fieldValsOut[i][j][k][l], correspond to the following:
#   [i] - The part instance (even if the element set spans just one part instance, this output is still 4D; just would need to use i = 0)
#   [j] - Element in the current part instance (since the number of elements for each part instance could be different, this is a jagged list before the j index)
#   [k] - Integration point in the current element (will be just one if CENTROID was chosen)
#   [l] - Data for the current integration point, given as follows: [Element label, XCoord, YCoord, ZCoord, Field_Value_Outputs ... ]
#
# instanceNames - A list of instance names (i.e. list[str]) which correspond to index i in fieldValsOut.
fieldValsOut, instanceNames = am.getIntegPntFieldValuesFromSetBatch(odbFilePath_global, odbStepPositionKey_global, odbFramePosition_global, odbSetStr_global, fieldOutputKey_global, fieldPosKey_global)

# Reshaping the 4D array into a 2D array in order to write it out to a .csv file
numInstances = len(instanceNames)
outValsList = [] # The flattened 2D array to be written out
for instIndex in range(numInstances): # Start iterating through the list, starting with the part instances
    curElemArr = fieldValsOut[instIndex] # 3D list
    curInstanceName = instanceNames[instIndex]
    numElems = len(curElemArr)
    
    for elemIndex in range(numElems): # Then the elements in the part instance
        curIntegPntArr = curElemArr[elemIndex] # 2D list
        numIntegPnts = len(curIntegPntArr)
        temp_allIntegPntsArr = []
        
        for integPntIndex in range(numIntegPnts): # Then the integration points in the given element
            curFieldValArr = curIntegPntArr[integPntIndex] # 1D list
            
            if integPntIndex == 0:
                temp_allIntegPntsArr.extend(curFieldValArr) # Write out the all the data including the element label for the first iteration
            else:
                temp_allIntegPntsArr.extend(curFieldValArr[1:]) # Don't need to write out the element label for each integration point
        
        if numInstances > 1: # Also write out the instance name at the end of the data if multiple instances are present
            temp_allIntegPntsArr.extend([curInstanceName])
        
        outValsList.append(temp_allIntegPntsArr)

csvFieldValFileHeader_out = csvFieldValFileHeader_global
if numIntegPnts > 1: # For multiple integration points, extend the header (with an appended label) for each integration point
    tempSubHeader = csvFieldValFileHeader_global[1:]
    csvFieldValFileHeader_out = [csvFieldValFileHeader_global[0]]
    for curIntegPnt in range(numIntegPnts):
        for curHeaderStr in tempSubHeader:
            csvFieldValFileHeader_out = csvFieldValFileHeader_out + [curHeaderStr + '_IP' + str(curIntegPnt)]

if numInstances > 1: # If multiple part instances are present, also add 'Instance' to the header
    csvFieldValFileHeader_out = csvFieldValFileHeader_out + ['Instance']

am.write2DListCSV(outValsList, csvFieldValFilePath_global, csvFieldValFileHeader_out)
print 'Script ended successfully!'





























































































egg.easterEgg = False
if egg.easterEgg:
    print '\nYou started my Easter Egg!!! Have fun shooting :) \n'
    egg.runEasterEgg()