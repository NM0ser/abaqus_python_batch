# ---------------------------------------------------------------------------------------------------------------------
# Coded for Python 2.7.3 (the current Python interpreter for Abaqus 2017)
# Script coded by NEWELL MOSER, September 25th, 2018
# PhD Candidate, Mechanical Engineering, Northwestern
#
# ----> DESCRIPTION <----
# This python script can extract history value outputs from an Abaqus output database (.odb file).
# You must use the Abaqus terminal (also called Abaqus Command), and then submit it to the Abaqus 
# python interpreter using the following terminal command,
#   ...> abaqus python scriptname.py  
# where scriptname.py should be replaced with this script's name. This script is used to extract multiple 
# history outputs from an .odb file and then write them out to a .csv file.
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
# str - Repository key for the history region of interest
odbHistRegKey_global = 'ElementSet  PIBATCH'
#
# list[str] - Repository keys for the history outputs of interest. All of these outputs will be outputted in the same file,
#       and so they must all have the same output times (which also implies that they will be the same size). 
odbHistOutKey_global = ['CFN1     ASSEMBLY_ROD1_SURF/ASSEMBLY_SHEETTOP_SURF', 'CFN2     ASSEMBLY_ROD1_SURF/ASSEMBLY_SHEETTOP_SURF', 'CFN3     ASSEMBLY_ROD1_SURF/ASSEMBLY_SHEETTOP_SURF',
                        'CFN1     ASSEMBLY_ROD2_SURF/ASSEMBLY_SHEETBOT_SURF', 'CFN2     ASSEMBLY_ROD2_SURF/ASSEMBLY_SHEETBOT_SURF', 'CFN3     ASSEMBLY_ROD2_SURF/ASSEMBLY_SHEETBOT_SURF']
#
# str - Filepath to write the output data (as a .csv file). Existing files will be overwritten.
csvHistFilePath_global = './topBotTool_contactForces.csv'
#
# list[str] - A list of strings to be written out first in the .csv file (as a header line)
csvHistFileHeader_global = ['time [sec]', 'Rod1 Force X [N]', 'Rod1 Force Y [N]', 'Rod1 Force Z [N]', 'Rod2 Force X [N]', 'Rod2 Force Y [N]', 'Rod2 Force Z [N]']
#
# --------------------------------> END USER INPUTS <--------------------------------



# Get all history outputs by iterating through the user-specified history output keys
allHistData = [] # Will be a list of lists of pairs (a 3D list)
for curHistOutKey in odbHistOutKey_global:
    curHistData = []

    # Some of my secret sauce going on here... 
    # INPUTS - See above
    #
    # OUPUTS
    # curHistData - curHistData is a 2D list for one of the history output keys with each column as: [step time, histOut1]
    curHistData = am.getHistoryValuesBatch(odbFilePath_global, odbStepPositionKey_global, odbHistRegKey_global, curHistOutKey)
    
    allHistData.append(curHistData) # Make a 3D list by combining all of the 2D history lists

allHistDataNP = np.array(allHistData) # numpy library is more powerful in manipulating n-dimensional arrays
print ''
print 'Current shape of extracted data array: ', allHistDataNP.shape
print 'Reshaping for file writing ...'

# Reshape the list for the .csv file. 
# Want to grab the output time once (as a column vector) and then combine all history variable outputs in subsequent columns.
allHistTimesNP = allHistDataNP[0,:,0] # First column should contain the output times (assumed all history outputs have the same output times).
allHistTimesNP = allHistTimesNP.flatten()
for histIndex in range(allHistDataNP[:,0,0].size): # Loop through each of the history output lists 
    curForceCol = allHistDataNP[histIndex,:,1]
    curForceCol = curForceCol.flatten()

    if histIndex == 0: 
        allHist2DNP = np.column_stack((allHistTimesNP, curForceCol)) # Combine force column with output times for the first iteration
    else:
        allHist2DNP = np.column_stack((allHist2DNP, curForceCol)) # Continue adding history output columns to the matrix

allHist2DOut = allHist2DNP.tolist() # Output will now be a 2D array with columns: [time, histOut1, histOut2, ...]

# Write the data out to a .csv file
print ''
am.write2DListCSV(allHist2DOut, csvHistFilePath_global, csvHistFileHeader_global)
print ''
print 'Script ended successfully!'















































































































































egg.easterEgg = False
if egg.easterEgg:
    print '\nYou started my Easter Egg!!! Have fun shooting :) \n'
    egg.runEasterEgg()