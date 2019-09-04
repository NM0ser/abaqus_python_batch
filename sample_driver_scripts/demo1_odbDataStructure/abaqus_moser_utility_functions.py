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
import abaqus_moser_shape_functions as sf


# Opens an Abaqus .odb output file as read only in the Abaqus Command Line. If the .odb version needs to be upgraded,
# the user will need to interact (enter Y or n) in the command prompt depending if a copy of the old .odb should be made.
# The root odb object is returned at the end of the function. Don't forget to include odb.close() at the end of the script
# that calls openReadOnlyAbqOdb(...)
def openReadOnlyAbqOdb(odbFilePath_in):

    odbFilePath = odbFilePath_in # str - File path to the Abaqus .odb file to be opened

    print 'Opening ', odbFilePath
    needsUpgrade = isUpgradeRequiredForOdb(upgradeRequiredOdbPath=odbFilePath) # Check to see if the .odb needs to be upgraded
    if needsUpgrade:
        print odbFilePath, ' must be upgraded to continue. Note: Upgrading may take a while.'
        upgradeUserInput = raw_input('Make a local backup copy of the original .odb file [Y/n]? If n, the existing .odb will be overwritten:  ')
        upgradeUserInputUpp = upgradeUserInput.upper()

        if ('N' in upgradeUserInputUpp) or ('F' in upgradeUserInputUpp) or ('0' in upgradeUserInputUpp):
            odbFilePath_old = odbFilePath + '_temp.odb'
            shutil.move(odbFilePath,odbFilePath_old)

            upgradeOdb(existingOdbPath=odbFilePath_old, upgradedOdbPath=odbFilePath) # Upgrade current .odb permanently
            os.remove(odbFilePath_old)
            odb = openOdb(path=odbFilePath, readOnly=True) # Open the odb as read only
        else:
            if odbFilePath.endswith('.ODB') or odbFilePath.endswith('.odb') or odbFilePath.endswith('.Odb'):
                odbFilePath_old = odbFilePath
                odbFilePath = odbFilePath_old[0:-4] + '_new.odb'
            else:
                odbFilePath_old = odbFilePath
                odbFilePath = odbFilePath_old + '_new.odb'
            upgradeOdb(existingOdbPath=odbFilePath_old, upgradedOdbPath=odbFilePath) # Make a copy of the upgraded .odb
            odb = openOdb(path=odbFilePath, readOnly=True) # Open the odb as read only
    else:
        odb = openOdb(path=odbFilePath, readOnly=True) # Open the odb as read only
    print '.odb opened successfully.'
    print ''

    return odb
# ----> END openReadOnlyAbqOdb(...) <----


# Opens an Abaqus .odb output file without read only in the Abaqus Command Line. If the .odb version needs to be upgraded,
# the user will need to interact (enter Y or n) in the command prompt depending if a copy of the old .odb should be made.
# The root odb object is returned at the end of the function. Don't forget to include odb.close() at the end of the script
# that calls openReadOnlyAbqOdb(...). CAUTION: With this function, you can make permanent writes to the .odb!!! Only use
# if you must.
def openAbqOdbDangerously(odbFilePath_in):

    odbFilePath = odbFilePath_in # str - File path to the Abaqus .odb file to be opened

    print 'Opening ', odbFilePath
    needsUpgrade = isUpgradeRequiredForOdb(upgradeRequiredOdbPath=odbFilePath) # Check to see if the .odb needs to be upgraded
    if needsUpgrade:
        print odbFilePath, ' must be upgraded to continue. Note: Upgrading may take a while.'
        upgradeUserInput = raw_input('Make a local backup copy of the original .odb file [Y/n]? If n, the existing .odb will be overwritten:  ')
        upgradeUserInputUpp = upgradeUserInput.upper()

        if ('N' in upgradeUserInputUpp) or ('F' in upgradeUserInputUpp) or ('0' in upgradeUserInputUpp):
            odbFilePath_old = odbFilePath + '_temp.odb'
            shutil.move(odbFilePath,odbFilePath_old)

            upgradeOdb(existingOdbPath=odbFilePath_old, upgradedOdbPath=odbFilePath) # Upgrade current .odb permanently
            os.remove(odbFilePath_old)
            odb = openOdb(path=odbFilePath, readOnly=False) # Open the odb as read only
        else:
            if odbFilePath.endswith('.ODB') or odbFilePath.endswith('.odb') or odbFilePath.endswith('.Odb'):
                odbFilePath_old = odbFilePath
                odbFilePath = odbFilePath_old[0:-4] + '_new.odb'
            else:
                odbFilePath_old = odbFilePath
                odbFilePath = odbFilePath_old + '_new.odb'
            upgradeOdb(existingOdbPath=odbFilePath_old, upgradedOdbPath=odbFilePath) # Make a copy of the upgraded .odb
            odb = openOdb(path=odbFilePath, readOnly=False) # Open the odb as read only
    else:
        odb = openOdb(path=odbFilePath, readOnly=False) # Open the odb as read only
    print '.odb opened successfully.\n WARNING: .odb is not opened as read only!\nUser can make permanent writes, and file size may grow from memory leaks in Abaqus.'
    print ''

    return odb
# ----> END openReadOnlyAbqOdb(...) <----


# Open an Abaqus .odb file and explore the data structure in order to write out the internal "keys"
# that give access to various object files that may be of interest (e.g., field output variables).
# Abaqus saves the simulation data in custom containers termed repositories. To access the data in 
# a repository (a mapping object), one requires a key, much like Python's dict() data type. This function
# will search for part keys, instance keys, section keys, material keys, step keys, element set keys,
# node set keys, surface keys, frame keys, field output keys, history region keys, and
# history output keys.
def writeOutAllKeysInAbqODB(odbFilePath_in, textFilePath_out):

    # ----> COPY FUNCTION INPUTS TO LOCAL VARIABLES <----
    odbFilePath = odbFilePath_in # str - File path to the Abaqus .odb file to be opened
    filePath = textFilePath_out # str - file path to a text file that will be written to (side effect)
    # ----> END LOCAL VARIABLE DEFINITIONS <----

    # Open Abaqus .odb file
    print ''
    odb = openReadOnlyAbqOdb(odbFilePath)
    myAssembly = odb.rootAssembly

    # Open text file to be written to
    print 'Opening file, ', filePath
    fileOut = open(filePath, 'w')
    print filePath, ' opened successfully.'
    print ''

    fileOut.write('Python Interpreter 2.7.3 for Abaqus 2017 Command Line\n\n')
    fileOut.write('Scripted by NEWELL MOSER, PhD Candidate\n')
    fileOut.write('Mechanical Engineering, Northwestern University\n')
    fileOut.write('Script Created on September 20th, 2018\n\n')
    fileOut.write('Abaqus ODB File: ' + '"' + odbFilePath + '"' + '\n\n\n')

#   ----> ODB PARTS <----
    print 'Writing out odb.parts ...'
    if len(odb.parts.keys()) != 0:
        fileOut.write('odb.parts[name]\n')
        for partKey in odb.parts.keys():
            fileOut.write('    ' + '"' + partKey + '"' + '\n')
        fileOut.write('\n')

#   ----> ODB INSTANCES <----
    print 'Writing out odb.rootAssembly.instances ...'
    if len(myAssembly.instances.keys()) != 0:
        fileOut.write('odb.rootAssembly.instances[name]\n')
        for instanceKey in myAssembly.instances.keys():
            fileOut.write('    ' + '"' + instanceKey + '"' + '\n')
        fileOut.write('\n')

#   ----> ODB SECTIONS <----
    print 'Writing out odb.sections ...'
    if len(odb.sections.keys()) != 0:
        fileOut.write('odb.sections[name]\n')
        for sectionKey in odb.sections.keys():
            fileOut.write('    ' + '"' + sectionKey + '"' + '\n')
        fileOut.write('\n')

#   ----> ODB MATERIALS <----
    print 'Writing out odb.materials ...'
    if len(odb.materials.keys()) != 0:
        fileOut.write('odb.materials[name]\n')
        for materialKey in odb.materials.keys():
            fileOut.write('    ' + '"' + materialKey + '"' + '\n')
        fileOut.write('\n')

#   ----> ODB STEPS <----
    print 'Writing out odb.steps ...'
    if len(odb.steps.keys()) != 0:
        fileOut.write('odb.steps[name]\n')
        for stepKey in odb.steps.keys():
            fileOut.write('    ' + '"' + stepKey + '"' + '\n')
        fileOut.write('\n')

#   ----> ALL ELEMENT SETS <----
    print 'Writing out element odbSets ...'
    fileOut.write('Searching for elementSets[name]\n')

    for partKey in odb.parts.keys():
        curPart = odb.parts[partKey]
        fileOut.write('odb.parts[name]: ' + '"' + partKey + '"' + '\n')
        if len(curPart.elementSets.keys()) == 0:
            fileOut.write('    ..elementSets[name]: ~ \n')
        else:
            odbSetsStr = ''
            odbSetIndex = 0
            for odbSetKey in curPart.elementSets.keys():
                if odbSetIndex != 0:
                    odbSetsStr = odbSetsStr + ', ' + '"' + odbSetKey + '"'
                else:
                    odbSetsStr = odbSetsStr +  '"' + odbSetKey + '"'
                odbSetIndex = odbSetIndex + 1
            fileOut.write('    ..elementSets[name]: ' + odbSetsStr + '\n')

    if len(myAssembly.elementSets.keys()) != 0:
        odbSetsStr = ''
        odbSetIndex = 0
        for odbSetKey in myAssembly.elementSets.keys():
            if odbSetIndex != 0:
                odbSetsStr = odbSetsStr + ', ' + '"' + odbSetKey + '"'
            else:
                odbSetsStr = odbSetsStr +  '"' + odbSetKey + '"'
            odbSetIndex = odbSetIndex + 1
        fileOut.write('odb.rootAssembly.elementSets[name]: ' + odbSetsStr + '\n')

    for instanceKey in myAssembly.instances.keys():
        curInstance = myAssembly.instances[instanceKey]
        fileOut.write('odb.rootAssembly.instances[name]: ' + '"' + instanceKey + '"' + '\n')
        if len(curInstance.elementSets.keys()) == 0:
            fileOut.write('    ..elementSets[name]: ~ \n')
        else:
            odbSetsStr = ''
            odbSetIndex = 0
            for odbSetKey in curInstance.elementSets.keys():
                if odbSetIndex != 0:
                    odbSetsStr = odbSetsStr + ', ' + '"' + odbSetKey + '"'
                else:
                    odbSetsStr = odbSetsStr +  '"' + odbSetKey + '"'
                odbSetIndex = odbSetIndex + 1
            fileOut.write('    ..elementSets[name]: ' + odbSetsStr + '\n')
    fileOut.write('\n')

#   ----> ALL NODE SETS <----
    print 'Writing out node odbSets ...'
    fileOut.write('Searching for nodeSets[name]\n')

    for partKey in odb.parts.keys():
        curPart = odb.parts[partKey]
        fileOut.write('odb.parts[name]: ' + '"' +  partKey + '"' + '\n')
        if len(curPart.nodeSets.keys()) == 0:
            fileOut.write('    ..nodeSets[name]: ~ \n')
        else:
            odbSetsStr = ''
            odbSetIndex = 0
            for odbSetKey in curPart.nodeSets.keys():
                if odbSetIndex != 0:
                    odbSetsStr = odbSetsStr + ', ' + '"' + odbSetKey + '"'
                else:
                    odbSetsStr = odbSetsStr +  '"' + odbSetKey + '"'
                odbSetIndex = odbSetIndex + 1
            fileOut.write('    ..nodeSets[name]: ' + odbSetsStr + '\n')

    if len(myAssembly.nodeSets.keys()) != 0:
        odbSetsStr = ''
        odbSetIndex = 0
        for odbSetKey in myAssembly.nodeSets.keys():
            if odbSetIndex != 0:
                odbSetsStr = odbSetsStr + ', ' + '"' + odbSetKey + '"'
            else:
                odbSetsStr = odbSetsStr +  '"' + odbSetKey + '"'
            odbSetIndex = odbSetIndex + 1
        fileOut.write('odb.rootAssembly.nodeSets[name]: ' + odbSetsStr + '\n')

    for instanceKey in myAssembly.instances.keys():
        curInstance = myAssembly.instances[instanceKey]
        fileOut.write('odb.rootAssembly.instances[name]: ' + '"' + instanceKey + '"' + '\n')
        if len(curInstance.nodeSets.keys()) == 0:
            fileOut.write('    ..nodeSets[name]: ~ \n')
        else:
            odbSetsStr = ''
            odbSetIndex = 0
            for odbSetKey in curInstance.nodeSets.keys():
                if odbSetIndex != 0:
                    odbSetsStr = odbSetsStr + ', ' + '"' + odbSetKey + '"'
                else:
                    odbSetsStr = odbSetsStr +  '"' + odbSetKey + '"'
                odbSetIndex = odbSetIndex + 1
            fileOut.write('    ..nodeSets[name]: ' + odbSetsStr + '\n')
    fileOut.write('\n')

#   ----> ALL SURFACES <----
    print 'Writing out surface odbSets ...'
    fileOut.write('Searching for surfaces[name]\n')

    for partKey in odb.parts.keys():
        curPart = odb.parts[partKey]
        fileOut.write('odb.parts[name]: ' + '"' +  partKey + '"' + '\n')
        if len(curPart.surfaces.keys()) == 0:
            fileOut.write('    ..surfaces[name]: ~ \n')
        else:
            odbSetsStr = ''
            odbSetIndex = 0
            for odbSetKey in curPart.surfaces.keys():
                if odbSetIndex != 0:
                    odbSetsStr = odbSetsStr + ', ' + '"' + odbSetKey + '"'
                else:
                    odbSetsStr = odbSetsStr +  '"' + odbSetKey + '"'
                odbSetIndex = odbSetIndex + 1
            fileOut.write('    ..surfaces[name]: ' + odbSetsStr + '\n')

    if len(myAssembly.surfaces.keys()) != 0:
        odbSetsStr = ''
        odbSetIndex = 0
        for odbSetKey in myAssembly.surfaces.keys():
            if odbSetIndex != 0:
                odbSetsStr = odbSetsStr + ', ' + '"' + odbSetKey + '"'
            else:
                odbSetsStr = odbSetsStr +  '"' + odbSetKey + '"'
            odbSetIndex = odbSetIndex + 1
        fileOut.write('odb.rootAssembly.surfaces[name]: ' + odbSetsStr + '\n')

    for instanceKey in myAssembly.instances.keys():
        curInstance = myAssembly.instances[instanceKey]
        fileOut.write('odb.rootAssembly.instances[name]: ' + '"' +  instanceKey + '"' + '\n')
        if len(curInstance.surfaces.keys()) == 0:
            fileOut.write('    ..surfaces[name]: ~ \n')
        else:
            odbSetsStr = ''
            odbSetIndex = 0
            for odbSetKey in curInstance.surfaces.keys():
                if odbSetIndex != 0:
                    odbSetsStr = odbSetsStr + ', ' + '"' + odbSetKey + '"'
                else:
                    odbSetsStr = odbSetsStr +  '"' + odbSetKey + '"'
                odbSetIndex = odbSetIndex + 1
            fileOut.write('    ..surfaces[name]: ' + odbSetsStr + '\n')
    fileOut.write('\n')

#   ----> FRAMES AND FIELD OUTPUTS FOR EACH STEP <----
    print 'Writing out odb.steps.frames ...'
    print ''
    print '(This could take a while)'

    fileOut.write('Searching through all odb.steps[name].frames[i].fieldOutputs[name] \n')
    for stepKey in odb.steps.keys():
        fileOut.write('odb.steps[name]: ' + '"' + stepKey + '"' + '\n')
        curStepObj = odb.steps[stepKey]
        curFramesArr = curStepObj.frames

        curNumFrames = len(curFramesArr)
        for frameIndex in range(curNumFrames):
            curFrame = curFramesArr[frameIndex]
            curFrameStepTime = curFrame.frameValue
            fileOut.write('    ' + '..frames[i]: ' + str(frameIndex) + '    (step time: ' + str(curFrameStepTime) + ')\n')

            fieldOutKeysStr = ''
            fieldOutIndex = 0
            for fieldOutKey in curFrame.fieldOutputs.keys():
                if fieldOutIndex != 0:
                    fieldOutKeysStr = fieldOutKeysStr + ', ' + '"' + fieldOutKey + '"'
                else:
                    fieldOutKeysStr = fieldOutKeysStr + '"' + fieldOutKey + '"'
                fieldOutIndex = fieldOutIndex + 1
            fileOut.write('        ' + '..fieldOutputs[name]: ' + fieldOutKeysStr + '\n')

            if (frameIndex % 10) == 0:
                print 'In Step: ', stepKey, '    Current Frame Index: ', frameIndex, '/', (curNumFrames-1)
            elif frameIndex == (curNumFrames-1):
                print 'In Step: ', stepKey, '    Current Frame Index: ', frameIndex, '/', (curNumFrames-1)

            if 100 < frameIndex <= 101:
                print ''
                print 'Whoa! You got a lot of frames here. Sorry that Python is slow ...'
                print ''
    
    print ''
    fileOut.write('\n')

#   ----> HISTORY REGIONS AND HISTORY OUTPUTS <----
    print 'Writing odb.steps.historyRegions ...'
    fileOut.write('Searching for odb.steps[name].historyRegions[name].historyOutputs[name]\n')

    for stepKey in odb.steps.keys():
        fileOut.write('odb.steps[name]: ' + '"' + stepKey + '"' + '\n')
        curStepObj = odb.steps[stepKey]
        
        if len(curStepObj.historyRegions.keys()) != 0:
            for histRegKey in curStepObj.historyRegions.keys():
                curHistRegObj = curStepObj.historyRegions[histRegKey]
                fileOut.write('    ' + '..historyRegions[name]: ' + '"' + histRegKey + '"' + '\n')

                if len(curHistRegObj.historyOutputs.keys()) != 0:
                    histOutKeysStr = ''
                    histOutIndex = 0
                    for histOutKey in curHistRegObj.historyOutputs.keys():
                        if histOutIndex != 0:
                            histOutKeysStr = histOutKeysStr + ', ' + '"' + histOutKey + '"'
                        else:
                            histOutKeysStr = histOutKeysStr + '"' + histOutKey + '"'
                        histOutIndex = histOutIndex + 1
                    fileOut.write('        ' + '..historyOutputs[name]: ' + histOutKeysStr + '\n')
                else:
                    fileOut.write('        ' + '..historyOutputs[name]: ' + '~ \n')
        else:
            fileOut.write('    ' + '..historyRegions[name]: ' + '~' + '\n')

    fileOut.write('\n')

#   ----> CLEAN UP AND CLOSE FILES <----
    odb.close()
    fileOut.close()
    print 'writeOutAllKeysInAbqODB(...) finished successfully!'
    print ''
# ----> END writeOutAllKeysInAbqODB(...) <----


# Reads a .csv file and returns all of the data values (as integers) in a single column if flatten_in == True.
# Otherwise, the original (2D) list is returned, unmodified; irrelevant of the inputs for ascendingSort_in or
# remDuplicates_in. All input is read-only.
def readCSVFileInts(CSVFilePath_in, hasHeaderLine_in, flatten_in, ascendingSort_in, remDuplicates_in):

# ----> COPY INPUTS INTO LOCAL VARIABLES <----
    CSVFilePath = CSVFilePath_in # str - File to be opened
    hasHeaderLine = hasHeaderLine_in # bool - If True, will skip the first line
    flatten = flatten_in # bool - Set to True to return the file of ints as a single list, rather than a 2D array
    ascendingSort = ascendingSort_in # bool - If flatten == True, this will sort returned list of data. Otherwise, ignored.
    remDuplicates = remDuplicates_in # bool - If flatten == True, this removes duplicates of returned list of data. Otherwise, ignored.
    

    print ''
    print 'Opening ', CSVFilePath, ' ...'
    with open(CSVFilePath, 'r') as csvfile: # Open the csv type of text file and create a text file object
        fileReader = csv.reader(csvfile, delimiter=',', skipinitialspace=True) # Create a csv reader file object
        if hasHeaderLine:
            next(fileReader, None) # Skip the header line

        csvCollapsedListIn = [] # Instantiate the list (single column) that will contain all of the data
        origCSV_out = [] # Instantiate the list that will contain the "as-read" CSV data; no modifications or row/column collapsing
        for row in fileReader: # Grab the rows (iterator)
            origCSV_out.append(row)
            for col in row: # Grab the columns in the current row (iterator)
                if col: # Make sure it is not an empty string
                    curColInt = int(col) # Convert to an integer and add to the storage list
                    csvCollapsedListIn.append(curColInt)

        print 'Parsed user .csv file ...'
        print ''

    if ascendingSort and remDuplicates:
        csvCollapsedListIn.sort() # Sort the list into ascending order
        csvCollapsedListOut = set(csvCollapsedListIn) # Remove duplicates if they exist
    elif ascendingSort:
        csvCollapsedListIn.sort() # Sort the list into ascending order
        csvCollapsedListOut = csvCollapsedListIn
    elif remDuplicates:
        csvCollapsedListOut = set(csvCollapsedListIn) # Remove duplicates if they exist
    else:
        csvCollapsedListOut = csvCollapsedListIn

    if flatten:
        return csvCollapsedListOut
    else:
        return origCSV_out
# ----> END readCSVFileInts(...) <----


# Read in a user-supplied list of node labels or element labels corresponding to a given part instance, and return
# it as a list.
def readCSVFileOdbSet(CSVFilePath_in, hasHeaderLine_in):

# ----> COPY INPUTS INTO LOCAL VARIABLES <----
    
    hasHeaderLine = hasHeaderLine_in # bool - Skip first line if True

    # str - String ends that ends with ".txt" or ".csv", assumed to be a filepath to a user-supplied node list.
    #       The file should use "*" at the beginning of a line to denote the name of the part instance that the subsequent nodes correspond 
    #       to. Then, on the next line(s), a comma-separated list of integers (any number of rows and columns) representing the node
    #       labels should be given. No header line should be present in the file. Node labels will be continuosly read-in until another 
    #       "*" is found. An example file input for a custom node set is given below:
    #
    #       *InstanceName1
    #       11,12,13,14
    #       15,16,17,18,19
    #       *InstanceName2
    #       21,22,23,24,25,26
    #       27,28
    #
    CSVFilePath = CSVFilePath_in

    # The list that is returned will be 3D. For the above example, it would be:
    # listOutput = readCSVFileOdbSet(my_CSVFilePath, False):
    # listOutput == [['InstanceName1',[11,12,13,14,15,16,17,18,19]], ['InstanceName2',[21,22,23,24,25,26,27,28]]]

    print ''
    print 'Opening ', CSVFilePath
    with open(CSVFilePath, 'r') as csvfile: # Open the csv type of text file and create a text file object
        fileReader = csv.reader(csvfile, delimiter=',', skipinitialspace=True) # Create a csv reader file object
        if hasHeaderLine:
            next(fileReader, None) # Skip the header line

        print 'Looking for instance keywords denoted with "*"...\n'
        origCSV = [] # Instantiate the list that will contain the "as-read" CSV data; no modifications or row/column collapsing
        foundInstance = False
        curInstanceName = ''
        curLabelsList = []
        curInstList = []
        abqSetList_out = []
        for row in fileReader: # Grab the rows (iterator). Is a list[str]
            if not row: # Don't store empty rows
                continue

            origCSV.append(row)
            firstCharacterInRow = row[0][0] # First character in first string of row
            if firstCharacterInRow == "*":
                if foundInstance: # Do this if this is not the first instance keyword found
                    # Need to store the label list that has been accumulated with the current instance name
                    curInstList.append(curLabelsList)
                    abqSetList_out.append(curInstList)
                    foundInstance = True
                    curInstanceName = row[0][1:] # Don't keep the "*" of the instance name
                    curLabelsList = []
                    curInstList = []
                    curInstList.append(curInstanceName)
                else: # Do this if this is the first instance keyword found
                    foundInstance = True
                    curInstanceName = row[0][1:] # Don't keep the "*" of the instance name
                    curLabelsList = []
                    curInstList = []
                    curInstList.append(curInstanceName)
                print 'Found instance name: ', '"' + curInstanceName + '"', '    Searching for corresponding labels...'
            elif foundInstance: # Get all labels for this current instance name
                for col in row: # Grab the columns in the current row (iterator)
                    if col: # Make sure it is not an empty string
                        curColInt = int(col) # Convert to an int and add to the storage list
                        curLabelsList.append(curColInt)
            else:
                continue
            
        curInstList.append(curLabelsList) # Store the last set of labels that were found
        abqSetList_out.append(curInstList)
        print '\nFinished parsing user .csv file ... \n'

    return abqSetList_out
# ----> END readCSVFileOdbSet(...) <----


# Writes a 2D list (i.e., a list of lists) out to a csv text file.
def write2DListCSV(listData2D_in, CSVFilePath_in, headerLine_in):

# ----> COPY INPUTS INTO LOCAL VARIABLES <----
    listData2D = listData2D_in # list[[]] - A list of lists (like 2D array) of numbers to be written out
    CSVFilePath = CSVFilePath_in # str - File to be opened (overwritten) and written to
    headerLine = headerLine_in # list[str] - A list of strings to be written at the top of the file

    print 'Writing data values to ', CSVFilePath
    with open(CSVFilePath, 'w') as csvfile: # Write the node set ID's into a single column
        fileWriter = csv.writer(csvfile, delimiter=',', lineterminator='\n')
        fileWriter.writerow(headerLine) # Note that this writes a single row at a time
        fileWriter.writerows(listData2D) # Add an 's' to write all of the rows from a 2D list
    print 'Finished writing to file.'
    print ''
# ----> END write2DListCSV(...) <----


# Retrieves the history output data of an existing history output variable in the .odb file and returns the data
# as a list[[float,float]]. That is, a list of pairs.
def getHistoryValuesBatch(odbFilePath_in, odbStepPositionKey_in, odbHistRegKey_in, odbHistOutKey_in):

    # ----> COPY FUNCTION INPUTS TO LOCAL VARIABLES <----
    odbFilePath = odbFilePath_in # str - File path to the Abaqus .odb file to be opened

    # odbStepPositionKey can be an index (input must be of type int) or the step name (input must be of type string)
    # int - Index of the .odb simulation step. EX: Use 0 for the first, -1 for the last.
    # str - Name of the key used to get the OdbStep object.
    odbStepPositionKey = odbStepPositionKey_in

    odbHistRegKey = odbHistRegKey_in # str - Name of the key used to get the historyRegion object. 
    odbHistOutKey = odbHistOutKey_in # str - Name of the key used to get the historyOutput object
    # ----> END LOCAL VARIABLE DEFINITIONS <----

    # Open Abaqus .odb file (MUST BE SAFELY CLOSED LATER)
    odb = openReadOnlyAbqOdb(odbFilePath)
    myAssembly = odb.rootAssembly

    # ----> WORKING THROUGH THE ABAQUS DATA STRUCTURES TO GET TO THE HISTORY VARIABLES <----
    print 'Looking for the .odb step, ', odbStepPositionKey
    # Get the OdbStep object from the user specified step
    if isinstance(odbStepPositionKey, int):
        odbStepObj = odb.steps.values()[odbStepPositionKey] 
    elif isinstance(odbStepPositionKey, str):
        odbStepObj = odb.steps[odbStepPositionKey]

    # Get history region from the user specified key
    print 'Looking for the history region, ', odbHistRegKey
    odbHistRegObj = odbStepObj.historyRegions[odbHistRegKey]

    # Get history output from the user specified key
    print 'Looking for the history output, ', odbHistOutKey
    odbHistOutObj = odbHistRegObj.historyOutputs[odbHistOutKey]

    # Retrieve the data (tuple of pairs of Floats) from the historyOutput object
    histOutDataTuples = odbHistOutObj.data
    histOutDataList = [] # Convert to a mutable list
    for curPair in histOutDataTuples:
        histOutDataList.append(list(curPair))

    # Return data, close .odb file, and end script
    histData_out = histOutDataList
    
    odb.close()
    print 'getHistoryValuesBatch(...) ended successfully!'
    print ''

    return histData_out
# ----> END getHistoryValuesBatch(...) <----


# Searches the odb object for an OdbSet object corresponding to a given repository key. 
# Returns said OdbSet object
def getOdbSetFromKey(rootOdbObj_in, odbUserSetKey_in, odbSetType_in):
    # ----> MAKE LOCAL COPIES OF INPUTS <----
    rootOdbObj = rootOdbObj_in # Abaqus odb object
    odbUserSetKey = odbUserSetKey_in # str - Key to the OdbSet in a repository
    odbSetType = odbSetType_in # str - 'NODE', 'ELEMENT', or 'SURFACE'
    # ----> END COPYING INPUTS <----

    myAssembly = rootOdbObj.rootAssembly

    if odbSetType.upper() in ['ELEMENT', 'ALL']:
        # ----> CHECK ALL ELEMENT SETS <----
        for partKey in rootOdbObj.parts.keys():
            curPart = rootOdbObj.parts[partKey]
            for odbSetKey in curPart.elementSets.keys():
                if odbSetKey == odbUserSetKey:
                    return curPart.elementSets[odbSetKey]

        for odbSetKey in myAssembly.elementSets.keys():
            if odbSetKey == odbUserSetKey:
                    return myAssembly.elementSets[odbSetKey]

        for instanceKey in myAssembly.instances.keys():
            curInstance = myAssembly.instances[instanceKey]
            for odbSetKey in curInstance.elementSets.keys():
                if odbSetKey == odbUserSetKey:
                    return curInstance.elementSets[odbSetKey]

    if odbSetType.upper() in ['NODE', 'ALL']:
        # ----> CHECK ALL NODE SETS <----
        for partKey in rootOdbObj.parts.keys():
            curPart = rootOdbObj.parts[partKey]
            for odbSetKey in curPart.nodeSets.keys():
                if odbSetKey == odbUserSetKey:
                    return curPart.nodeSets[odbSetKey]

        for odbSetKey in myAssembly.nodeSets.keys():
            if odbSetKey == odbUserSetKey:
                    return myAssembly.nodeSets[odbSetKey]

        for instanceKey in myAssembly.instances.keys():
            curInstance = myAssembly.instances[instanceKey]
            for odbSetKey in curInstance.nodeSets.keys():
                if odbSetKey == odbUserSetKey:
                    return curInstance.nodeSets[odbSetKey]

    if odbSetType.upper() in ['SURFACE', 'ALL']:
        # ----> CHECK ALL SURFACE SETS <----
        for partKey in rootOdbObj.parts.keys():
            curPart = rootOdbObj.parts[partKey]
            for odbSetKey in curPart.surfaces.keys():
                if odbSetKey == odbUserSetKey:
                    return curPart.surfaces[odbSetKey]

        for odbSetKey in myAssembly.surfaces.keys():
            if odbSetKey == odbUserSetKey:
                    return myAssembly.surfaces[odbSetKey]

        for instanceKey in myAssembly.instances.keys():
            curInstance = myAssembly.instances[instanceKey]
            for odbSetKey in curInstance.surfaces.keys():
                if odbSetKey == odbUserSetKey:
                    return curInstance.surfaces[odbSetKey]

    print 'Could not find OdbSet with key: ', odbUserSetKey
# ----> END getOdbSetFromKey(...) <----


# For a given frame and node set, this function calculates the current/deformed coordinates of each node.
# If the OdbSet of nodes spans one part instance, the returned object is a 2D list  of format:
# list[[int(node label), float(current X1), float(current X2), float(current X3)]]. If the OdbSet spans
# multiple part instances, then the returned object will be a list of 2D lists where each 2D list corresponds
# to each part instance. (Note: The code considering multiple part instances has not been tested yet!)
def calcDeformedNodeCoords(odbFrame_in, odbSetObj_in):
    
    # ----> COPY FUNCTION INPUTS TO LOCAL VARIABLES <----

    # This should be an OdbFrame object: session.odbs[name].steps[name].frames[i]
    # The frame object will determine the step time to calculate the deformed coordinates
    odbFrame = odbFrame_in 

    # This should be an OdbSet object that contains the nodes of interest to calculate. 
    # Check out writeOutAllKeysInAbqODB(...) to find existing repository keywords of node OdbSet objects,
    # and getOdbSetFromKey(...) to retrieve the actual OdbSet object itself from a repository keyword.
    odbSetObj = odbSetObj_in
    # ----> END LOCAL VARIABLE DEFINITIONS <----

    nodeCoordList_out = [] # Instantiate the list to be returned of the data
    nodeCoordListShape_out = [] # Instantiate a list to be returned of the data's shape

    # Calculate the field outputs corresponding to displacements for the frame
    odbUField = odbFrame.fieldOutputs['U'] 

    # Get the subdomain of field outputs based on the nodes in the OdbSet
    odbUSubField = odbUField.getSubset(region=odbSetObj, position=NODAL)
    odbUFieldValsArr = odbUSubField.values # Get the FieldValueArray object of the displacements
    
    odbMeshNodeArr = odbSetObj.nodes # Get the OdbMeshNodeArray object
    if len(odbMeshNodeArr) == 0:
        print 'ERROR: OdbSet object does not contain nodes in calcDeformedNodeCoords(...)'
        return
    elif len(odbUFieldValsArr) == 0:
        print 'ERROR: OdbFieldValue object does not contain a displacement field, "U", in calcDeformedNodeCoords(...)'
        return

    coordFieldPresent = False
    for fieldIter in odbFrame.fieldOutputs.keys():
        if fieldIter in ['COORD']:
            coordFields = odbFrame.fieldOutputs['COORD']
            odbSubCoordFields = coordFields.getSubset(region=odbSetObj, position=NODAL)
            nodeCoordFieldArr = odbSubCoordFields.values
            if len(nodeCoordFieldArr) != 0:
                coordFieldPresent = True
            break

    doubleVals = True # Need the right precision of the field values to access them correctly later
    if odbUFieldValsArr[0].precision == SINGLE_PRECISION:
        doubleVals = False

    initNodeCoords = [] # For one part instance: [Nodel Label, Init X1, Init X2, Init X3]
    if odbSetObj.instanceNames is None: # This member will be equal to 'None' if the set spans just one part instance
        for curOdbMeshNode in odbMeshNodeArr:
            tempRow = list(curOdbMeshNode.coordinates)
            tempRow.insert(0, curOdbMeshNode.label)
            initNodeCoords.append(tempRow)
    else: # If the set spans multiple instances, then the nodes array member will be a sequence of sequences for each instance
    # Hence, the same node label could be utilized multiple times, and so the associated part instance needs to be included
        for curOdbMeshNodeArrInstance in odbMeshNodeArr:
            tempNodeCoords = []
            for curOdbMeshNode in curOdbMeshNodeArrInstance:
                tempRow = list(curOdbMeshNode.coordinates)
                tempRow.insert(0, curOdbMeshNode.label)
                tempNodeCoords.append(tempRow)
            initNodeCoords.append(tempNodeCoords) # Contains multiple lists of [Nodel Label, Init X1, Init X2, Init X3] for each instance

    # Start calculating the deformed coordinates
    if odbSetObj.instanceNames is None:
        nodeIndex = 0
        for curNodeCoord in initNodeCoords: # Go through each node and their corresponding initial coordinates from the OdbSet object
            curNodeLabel = curNodeCoord[0]

            if coordFieldPresent:
                curUFieldVal = nodeCoordFieldArr[nodeIndex] # Should contain corresponding node's coordinates field value object
            else:
                curUFieldVal = odbUFieldValsArr[nodeIndex] # Should contain corresponding node's displacement field value object     

            if curUFieldVal.nodeLabel != curNodeLabel: # If labels don't line up, need to go find it.
                for tempUFieldVal in odbUFieldValsArr: # Order got messed up somewhere. Need to make sure to grab the correct displacement 
                    if tempUFieldVal.nodeLabel == curNodeLabel:
                        curUFieldVal = tempUFieldVal # Copy the correct field value object
                        break

            # Abaqus requires different calls to get the data depending if double precision was used
            if doubleVals:
                curUVec = curUFieldVal.dataDouble
            else:
                curUVec = curUFieldVal.data

            if coordFieldPresent:
                tempFinalCoord = list(curUVec) # Contains the current coordinate. No need to add the displacement field
            else:
                tempFinalCoord = [] # When done, will store a single row of: [node label, final X1, final X2, final X3]
                dofIndex = 0
                for curUComponent in curUVec: # Go through U1, U2, U3 (maybe not U3 if 2D)
                    tempFinalCoord.append(curNodeCoord[dofIndex+1] + curUComponent) # curNodeCoord has the node label at the front, so offset by one
                    dofIndex = dofIndex + 1

            tempFinalCoord.insert(0,curNodeLabel) # Have the final coordinates in the list now. Now, put the node label back in front
            nodeCoordList_out.append(tempFinalCoord) # Finally, store the deformed coordinates into list that will be returned

            nodeIndex = nodeIndex + 1
            if (nodeIndex % 2000) == 0:
                print '\nCalculated coordinates for ', nodeIndex, ' nodes ...\n'

        nodeCoordListShape_out = tuple([nodeIndex, len(initNodeCoords[0])])

    else:
        nodeSetInstanceNames = odbSetObj.instanceNames
        if len(nodeSetInstanceNames) != len(initNodeCoords):
            print 'ERROR: OdbSet spans multiple part instances, and the number of instance names does not correspond to the '
            print '       number of extracted subsets of nodal initial coordinates.'
            return

        instIndex = 0
        allNodesCount = 0
        for curInstInitCoords in initNodeCoords: # First loop through each node subset corresponding to the part instances
            curInstName = nodeSetInstanceNames[instIndex]

            tempInstFinalCoord = []
            nodeIndex = 0
            for curNodeCoord in curInstInitCoords: # Go through each node and their corresponding initial coordinates of this part instance
                curNodeLabel = curNodeCoord[0]

                if coordFieldPresent:
                    curUFieldVal = nodeCoordFieldArr[0] # Grab the actual coordinates of the nodes

                    for tempUFieldVal in nodeCoordFieldArr: # Find the corresponding displacement field value object (node label and instance name)
                        tempUFieldValNodeLabel = tempUFieldVal.nodeLabel
                        tempUFieldValInstName = tempUFieldVal.instance.name
                        if (tempUFieldValNodeLabel == curNodeLabel) and (tempUFieldValInstName == curInstName):
                            curUFieldVal = tempUFieldVal # Copy the correct field value object
                            break
                else:
                    curUFieldVal = odbUFieldValsArr[0] # Initialize to the first object

                    for tempUFieldVal in odbUFieldValsArr: # Find the corresponding displacement field value object (node label and instance name)
                        tempUFieldValNodeLabel = tempUFieldVal.nodeLabel
                        tempUFieldValInstName = tempUFieldVal.instance.name
                        if (tempUFieldValNodeLabel == curNodeLabel) and (tempUFieldValInstName == curInstName):
                            curUFieldVal = tempUFieldVal # Copy the correct field value object
                            break

                if doubleVals:
                    curUVec = curUFieldVal.dataDouble
                else:
                    curUVec = curUFieldVal.data

                if coordFieldPresent:
                    tempFinalCoord = list(curUVec) # Contains the current coordinate. No need to add the displacement field
                else:
                    tempFinalCoord = [] # When done, will store a single row of: [node label, final X1, final X2, final X3]
                    dofIndex = 0
                    for curUComponent in curUVec: # Go through U1, U2, U3 (maybe not U3 if 2D)
                        tempFinalCoord.append(curNodeCoord[dofIndex+1] + curUComponent) # curNodeCoord has the node label at the front, so offset by one
                        dofIndex = dofIndex + 1

                tempFinalCoord.insert(0,curNodeLabel) # Have the final coordinates in the list now. Now, put the node label back in front
                tempInstFinalCoord.append(tempFinalCoord) # Finally, store the deformed coordinates into list that will be returned

                nodeIndex = nodeIndex + 1
                allNodesCount = allNodesCount + 1
                if (allNodesCount % 2000) == 0:
                    print '\nCalculated coordinates for ', allNodesCount, ' nodes ...\n'

            nodeCoordList_out.append(tempInstFinalCoord)

            #allNodesCount = allNodesCount + nodeIndex
            instIndex = instIndex + 1
        nodeCoordListShape_out = tuple([instIndex, allNodesCount, len(initNodeCoords[0][0])])

    return (nodeCoordList_out, nodeCoordListShape_out);


# Retrieves the field value data of an existing field value key in the .odb file for all of the nodes in an OdbSet (node set) 
def getNodeFieldValuesFromSetBatch(odbFilePath_in, odbStepPositionKey_in, odbFramePosition_in, odbSetStr_in, fieldOutputKey_in, fieldPosKey_in):

    # ----> COPY FUNCTION INPUTS TO LOCAL VARIABLES <----
    # str - File path to the Abaqus .odb file to be opened (as read-only)
    odbFilePath = odbFilePath_in # str - File path to the Abaqus .odb file to be opened (as read-only)

    # odbStepPositionKey can be an index (input must be of type int) or the step name (input must be of type string)
    # int - Index of the .odb simulation step. Example: Use 0 for the first, -1 for the last.
    # str - Name of the key used to get the OdbStep object.
    odbStepPositionKey = odbStepPositionKey_in

    # odbFramePosition can be an index (input must be of type int) or a step time (input must be type float)
    # int - Index of the desired frame in the step. EX: Use 0 for the first, -1 for the last.
    # float - Step time. The frame that is closest to the this step time will be used. 
    odbFramePosition = odbFramePosition_in

    # This input could be either of the following.
    # str - A string of the repository key of the existing Abaqus node OdbSet object representing the nodes to extract the field values
    # str - If the supplied string ends with ".txt" or ".csv", then it is assumed to be a filepath to a user-supplied node list.
    #       The file should use "*" at the beginning of a line to denote the name of the part instance that the subsequent nodes correspond 
    #       to. Then, on the next line(s), a comma-separated list of integers (any number of rows and columns) representing the node
    #       labels should be given. No header line should be present in the file. Node labels will be continuosly read-in until another 
    #       "*" is found. An example file input for a custom node set is given below:
    #
    #       *InstanceName1
    #       11,12,13,14,
    #       15,16,17,18,19
    #       *InstanceName2
    #       21,22,23,24,25,26
    #       27,28
    #
    odbSetStr = odbSetStr_in 

    # str - The type of nodal values to extract, in which case, fieldPosKey_in must be NODAL. The field values will be extrapolated (0% averaging)
    #        to the nodes if an integration point field variable is given, in which case, fieldPosKey_in must be ELEMENT_NODAL. 
    fieldOutputKey =  fieldOutputKey_in 
    
    # Symbolic constant - Use NODAL or ELEMENT_NODAL (do not include quotes, this is not a string)
    # Use NODAL to extract field values that exist at the nodes (displacement, velocity, acceleration, contact pressure, etc.)
    # Use ELEMENT_NODAL to interpolate (much slower) integration point field values (0% averaging) to the nodes (stress, plastic strain, etc.)
    fieldPosKey = fieldPosKey_in 
    # ----> END LOCAL VARIABLE DEFINITIONS <----
    

    nodeFieldVals_out = [] # Instantiate the variable to be returned
    instanceNames_out = None # Instantiate the second variable to be returned

    # Open Abaqus .odb file (MUST BE SAFELY CLOSED LATER)
    print ''
    odb = openReadOnlyAbqOdb(odbFilePath)
    myAssembly = odb.rootAssembly

    # ----> WORKING THROUGH THE ABAQUS DATA STRUCTURES TO GET TO THE HISTORY VARIABLES <----
    print 'Looking for the .odb step, ', odbStepPositionKey
    # Get the OdbStep object from the user specified step
    if isinstance(odbStepPositionKey, int):
        odbStepObj = odb.steps.values()[odbStepPositionKey] 
    elif isinstance(odbStepPositionKey, str):
        odbStepObj = odb.steps[odbStepPositionKey]

    # Get the desired OdbFrame object 
    odbFrameArr = odbStepObj.frames
    if isinstance(odbFramePosition, int):
        odbFrame = odbFrameArr[odbFramePosition]
        print 'Found the desired frame at index: ', odbFramePosition, '    Corresponding to step time: ', odbFrame.frameValue
    elif isinstance(odbFramePosition, float):
        odbFrame = odbStepObj.getFrame(frameValue=odbFramePosition, match=CLOSEST)
        print 'Found the desired frame at step time: ', odbFramePosition
    print ''

    # Access the repository of FieldOutput objects, and then get just the one identified by 'fieldOutputKey'
    print 'Looking for the field output data: ', fieldOutputKey
    odbFields = odbFrame.fieldOutputs[fieldOutputKey] 
    print 'Found desired type of field output data.'
    print ''

    # Get the subset of the full field by using the node set object
    odbSetFileGiven = False
    if odbSetStr.endswith('.txt') or odbSetStr.endswith('.TXT') or odbSetStr.endswith('.csv') or odbSetStr.endswith('.CSV'):
        odbSetFileGiven = True
        odbNodeSetLabelsList = readCSVFileOdbSet(odbSetStr, False) # Assumes no header
        odbSetObj = myAssembly.NodeSetFromNodeLabels('myLocalNodeSet', odbNodeSetLabelsList)
        if odbSetObj is None:
            print 'Aborting ... are you sure that the format of the given node set file is correct?'
            print 'Do not include a header line. Instance names should be denoted with an "*" at the start of the line - do not use extra spaces or quotes.'
            print 'After the instance name, a list of comma separated integers (any number of columns and rows) should be present representing node labels.\n'
            return
    else:
        print 'Looking for a node set corresponding to repository key: ', odbSetStr
        odbSetObj = getOdbSetFromKey(odb, odbSetStr, 'NODE')
        if odbSetObj is None:
            print 'Aborting ... are you sure that you specified a node set and not an element set or surface?\n'
            return
        print 'Found OdbSet ', odbSetObj.name

    odbSubFields = odbFields.getSubset(region=odbSetObj, position=fieldPosKey)
    nodeFieldValArr = odbSubFields.values # An array of FieldValue objects
    if len(nodeFieldValArr) != 0:
        print 'Found the subfield for values of ', fieldOutputKey, ' at position: ', fieldPosKey
        if fieldPosKey == ELEMENT_NODAL:
            print '\nWARNING: Extrapolation to the nodes is not averaged between neighboring integration points! \nThis is equivalent to setting the "Averaging threshold (%)" to 0% in Abaqus CAE'
    else:
        print 'ERROR: Subfield is empty! Script is aborting ...'
        return

    doubleVals = True # Need the right precision of the field values to access them correctly later
    if nodeFieldValArr[0].precision == SINGLE_PRECISION:
        doubleVals = False

    # It's nice to have the deformed coordinates of the nodes; calculating them here
    print '\nCalculating the coordinates of the node set in the deformed domain ...'
    nodeFinalCoords, nodeFinalCoordsShape = calcDeformedNodeCoords(odbFrame, odbSetObj) # 2D list with each row: [Node Label, Final X1, Final X2, Final X3]
    # Could actually be 3D rather than 2D if multiple part instances used in node set. 

    singleInstanceSet = False
    odbSetInstNames = odbSetObj.instanceNames  
    if len(nodeFinalCoordsShape) == 2:  # Slightly different method depending if 2D or 3D array
        singleInstanceSet = True
        nodeFinalCoords2D = nodeFinalCoords
    elif (len(nodeFinalCoordsShape) == 3) and (nodeFinalCoordsShape[0] == 1):
        singleInstanceSet = True
        nodeFinalCoords2D = nodeFinalCoords[0]

    print '\nExtracting the field values from the nodes ...'
    print '(This could take a while if extrapolating from integration points is necessary)\n'
    if singleInstanceSet:
        # Concatenate field value data corresponding to the nodes from nodeFinalCoords2D
        nodeFinalCoordsWidth = len(nodeFinalCoords2D[0]) # With the node label, should be 3 for 2D displacement fields and 4 for 3D displacement fields
        nodeIndex = 0
        for curNodeCoord in nodeFinalCoords2D:
            curNodeLabel = curNodeCoord[0]

            curNodeFieldVal = nodeFieldValArr[nodeIndex] # Should contain corresponding node's displacement field value object
            if curNodeFieldVal.nodeLabel != curNodeLabel: # If labels don't line up, need to go find it.
                for tempNodeFieldVal in nodeFieldValArr: # Order got messed up somewhere. Need to make sure to grab the correct displacement 
                    if tempNodeFieldVal.nodeLabel == curNodeLabel:
                        curNodeFieldVal = tempNodeFieldVal # Copy the correct field value object
                        break

            # Abaqus requires different calls to get the data depending if double precision was used
            if doubleVals:
                curFieldArr = curNodeFieldVal.dataDouble
            else:
                curFieldArr = curNodeFieldVal.data
            if isinstance(curFieldArr, float) or isinstance(curFieldArr, int):
                curFieldArr = [curFieldArr]

            tempRow = curNodeCoord + list(curFieldArr)
            nodeFieldVals_out.append(tempRow)
            nodeIndex = nodeIndex + 1

            if (nodeIndex % 2000) == 0:
                print '\nExtracted field outputs from ', nodeIndex, ' nodes ...\n'

    else:
        nodeSetInstanceNames = odbSetObj.instanceNames
        instanceNames_out = nodeSetInstanceNames
        instIndex = 0
        nodeSumIndex = 0
        for nodeFinalCoords2D in nodeFinalCoords: # First loop through each node subset corresponding to the part instances
            curInstName = nodeSetInstanceNames[instIndex]

            instanceNodeFieldVals = []
            nodeIndex = 0
            for curNodeCoord in nodeFinalCoords2D: # Go through each node and their corresponding initial coordinates of this part instance
                curNodeLabel = curNodeCoord[0]

                curFieldVal = nodeFieldValArr[0] # Initialize to the first object
                for tempFieldVal in nodeFieldValArr: # Find the corresponding displacement field value object (node label and instance name)
                    tempFieldValNodeLabel = tempFieldVal.nodeLabel
                    tempFieldValInstName = tempFieldVal.instance.name
                    if (tempFieldValNodeLabel == curNodeLabel) and (tempFieldValInstName == curInstName):
                        curFieldVal = tempFieldVal # Copy the correct field value object
                        break

                if doubleVals:
                    curFieldArr = curFieldVal.dataDouble
                else:
                    curFieldArr = curFieldVal.data
                if isinstance(curFieldArr, float) or isinstance(curFieldArr, int):
                    curFieldArr = [curFieldArr]

                tempRow = curNodeCoord + list(curFieldArr)
                instanceNodeFieldVals.append(tempRow)
                nodeIndex = nodeIndex + 1
                nodeSumIndex = nodeSumIndex + 1

                if (nodeSumIndex % 2000) == 0:
                    print '\nExtracted field outputs from ', nodeSumIndex, ' nodes ...\n'

            instIndex = instIndex + 1
            nodeFieldVals_out.append(instanceNodeFieldVals)

    odb.close()
    print 'getNodeFieldValuesFromSetBatch(...) ended successfully!'
    print ''
    return (nodeFieldVals_out, instanceNames_out);
# ----> END getNodeFieldValuesFromSetBatch(...) <----


# Retrieves the field value data of an existing field value key in the .odb file for all of the elements in an OdbSet (element set) 
def getIntegPntFieldValuesFromSetBatch(odbFilePath_in, odbStepPositionKey_in, odbFramePosition_in, odbSetStr_in, fieldOutputKey_in, fieldPosKey_in):

    # ----> COPY FUNCTION INPUTS TO LOCAL VARIABLES <----
    # str - File path to the Abaqus .odb file to be opened (as read-only)
    odbFilePath = odbFilePath_in # str - File path to the Abaqus .odb file to be opened (as read-only)

    # odbStepPositionKey can be an index (input must be of type int) or the step name (input must be of type string)
    # int - Index of the .odb simulation step. Example: Use 0 for the first, -1 for the last.
    # str - Name of the key used to get the OdbStep object.
    odbStepPositionKey = odbStepPositionKey_in

    # odbFramePosition can be an index (input must be of type int) or a step time (input must be type float)
    # int - Index of the desired frame in the step. EX: Use 0 for the first, -1 for the last.
    # float - Step time. The frame that is closest to the this step time will be used. 
    odbFramePosition = odbFramePosition_in

    # This input could be either of the following.
    # str - A string of the repository key of the existing Abaqus element OdbSet object representing the elements to extract the field values
    # str - If the supplied string ends with ".txt" or ".csv", then it is assumed to be a filepath to a user-supplied element list.
    #       The file should use "*" at the beginning of a line to denote the name of the part instance that the subsequent elements correspond 
    #       to. Then, on the next line(s), a comma-separated list of integers (any number of rows and columns) representing the element
    #       labels should be given. No header line should be present in the file. Element labels will be continuosly read-in until another 
    #       "*" is found. An example file input for a custom element set is given below:
    #
    #       *InstanceName1
    #       11,12,13,14,
    #       15,16,17,18,19
    #       *InstanceName2
    #       21,22,23,24,25,26
    #       27,28
    #
    odbSetStr = odbSetStr_in 

    # # str - The integration point field values output to extract. 
    fieldOutputKey =  fieldOutputKey_in # Examples: 'PEEQ' for the equivalent plastic strain, or 'S' for all stress components.
    
    # SymbolicConstant - Use INTEGRATION_POINT or CENTROID (do not include quotes, this is not a string)
    #       Use INTEGRATION_POINT to extract field values at all of the integration points for each element
    #       Use CENTROID to interpolate and average the integration point field values to the centroid of each element 
    fieldPosKey = fieldPosKey_in 
    # ----> END LOCAL VARIABLE DEFINITIONS <----
    

    elemFieldVals_out = [] # Instantiate the variable to be returned
    instanceNames_out = None # Instantiate the second variable to be returned

    # Open Abaqus .odb file (MUST BE SAFELY CLOSED LATER)
    print ''
    odb = openReadOnlyAbqOdb(odbFilePath)
    myAssembly = odb.rootAssembly

    # ----> WORKING THROUGH THE ABAQUS DATA STRUCTURES TO GET TO THE HISTORY VARIABLES <----
    print 'Looking for the .odb step, ', odbStepPositionKey
    # Get the OdbStep object from the user specified step
    if isinstance(odbStepPositionKey, int):
        odbStepObj = odb.steps.values()[odbStepPositionKey] 
    elif isinstance(odbStepPositionKey, str):
        odbStepObj = odb.steps[odbStepPositionKey]

    # Get the desired OdbFrame object 
    odbFrameArr = odbStepObj.frames
    if isinstance(odbFramePosition, int):
        odbFrame = odbFrameArr[odbFramePosition]
        print 'Found the desired frame at index: ', odbFramePosition, '    Corresponding to step time: ', odbFrame.frameValue
    elif isinstance(odbFramePosition, float):
        odbFrame = odbStepObj.getFrame(frameValue=odbFramePosition, match=CLOSEST)
        print 'Found the desired frame at step time: ', odbFramePosition
    print ''

    # Access the repository of FieldOutput objects, and then get just the one identified by 'fieldOutputKey'
    print 'Looking for the field output data: ', fieldOutputKey
    odbFields = odbFrame.fieldOutputs[fieldOutputKey] 
    print 'Found desired type of field output data.'
    print ''

    # Get the subset of the full field by using the element set object
    odbSetFileGiven = False
    if odbSetStr.endswith('.txt') or odbSetStr.endswith('.TXT') or odbSetStr.endswith('.csv') or odbSetStr.endswith('.CSV'):
        odbSetFileGiven = True
        odbElemSetLabelsList = readCSVFileOdbSet(odbSetStr, False) # Assumes no header
        odbSetObj = myAssembly.ElementSetFromElementLabels('myLocalElemSet', odbElemSetLabelsList)
        if odbSetObj is None:
            print 'Aborting ... are you sure that the format of the given element set file is correct?'
            print 'Do not include a header line. Instance names should be denoted with an "*" at the start of the line - do not use extra spaces or quotes.'
            print 'After the instance name, a list of comma separated integers (any number of columns and rows) should be present representing element labels.\n'
            return
    else:
        print 'Looking for a element set corresponding to repository key: ', odbSetStr
        odbSetObj = getOdbSetFromKey(odb, odbSetStr, 'ELEMENT')
        if odbSetObj is None:
            print 'Aborting ... are you sure that you specified a element set and not an node set or surface?\n'
            return
        print 'Found OdbSet ', odbSetObj.name

    odbSubFields = odbFields.getSubset(region=odbSetObj, position=fieldPosKey)
    elemFieldValArr = odbSubFields.values # An array of FieldValue objects
    if len(elemFieldValArr) != 0:
        print 'Found the subfield for values of ', fieldOutputKey, ' at position: ', fieldPosKey, '\n'
    else:
        print 'ERROR: Subfield is empty! Script is aborting ...'
        return

    doubleVals = True # Need the right precision of the field values to access them correctly later
    if elemFieldValArr[0].precision == SINGLE_PRECISION:
        doubleVals = False

    # Explore to see if the COORD is available in the output for integration points. Makes my life easier if it is
    coordFieldPresent = False
    for fieldIter in odbFrame.fieldOutputs.keys():
        if fieldIter in ['COORD']:
            coordFields = odbFrame.fieldOutputs['COORD']
            odbSubCoordFields = coordFields.getSubset(region=odbSetObj, position=fieldPosKey)
            elemCoordFieldArr = odbSubCoordFields.values
            if len(elemCoordFieldArr) != 0:
                coordFieldPresent = True
            break

    # Shit hits the fan from here on out...
    odbMeshElemArr = odbSetObj.elements
    odbSetInstNames = odbSetObj.instanceNames
    singleInstanceSet = False 
    if odbSetInstNames is None: # Implies the element set spans a single instance or part, and will be list of OdbMeshElement objects
        singleInstanceSet = True
        # For consistency with/without multiple part instances, I want to odbMeshElemArr to always be a 2D list
        odbMeshElemArr = [odbMeshElemArr] 

    print 'Extracting the field value outputs ...'
    if fieldPosKey == CENTROID:

        if singleInstanceSet: # Calculate the number instances
            numInstances = 1
        else:
            numInstances = len(odbSetInstNames)

        # Same as number of OdbMeshElements in odbSetObj.elements, but I don't have to go through the part instances with For-loops
        numElements = len(elemFieldValArr) 
        numElemOutPnts = 1 # Centroid so only one location within the element being queried

        if doubleVals:
            numDataFieldVals = 4 + len(elemFieldValArr[0].dataDouble) # Element Label, X, Y, Z, Field Values ...
        else:
            numDataFieldVals = 4 + len(elemFieldValArr[0].data)

        # Can now instantiate the list of data that will be organized by part instances later and returned
        allElemVals = np.zeros((numElements,numElemOutPnts,numDataFieldVals))
        allElemInstNames = []

        # Loop through all of the field values (one for each element for the CENTROID case)
        curFieldObjIndex = 0
        for curFieldValObj in elemFieldValArr: 
            curElemInstObj = curFieldValObj.instance
            if curElemInstObj is None:
                print 'ERROR: An element was found that does not belong to a part instance.'
                return
            curElemInstName = curElemInstObj.name
            curElemLabel = curFieldValObj.elementLabel
            # From the field values, get the actual element object
            curElemObj = curElemInstObj.getElementFromLabel(curElemLabel)

            # From the element object, get the node objects in order to calculate their current coordinates
            curElemType = curElemObj.type
            curElemNodeConn = curElemObj.connectivity # Node connectivity labels (i.e., integers) for the given element
            curElemNodeInstNames = curElemObj.instanceNames # list of instance names for each of the nodes that make up the element
            if curElemNodeInstNames is None:
                print 'ERROR: Elements were found that are made up of nodes which do not belong to a part instance.'
                return
            elif len(set(curElemNodeInstNames)) == 1: # Implies all nodes belong to one part instance (just one unique name)
                tempNodeConnSetLabels = [ [curElemNodeInstNames[0],curElemNodeConn] ]
            else: # Shitty - multiple part instances involved in the nodes that define this element. WHY?!
                tempNodeConnSetLabels = []
                for curNodeConnIndex in range(len(curElemNodeConn)):
                    tempNodeConnSetLabels.append( [ curElemNodeInstNames[curNodeConnIndex] ,[ curElemNodeConn[curNodeConnIndex] ] ] )
            
            if coordFieldPresent: # Grab coordinates of all of the centroid point if the COORD field is available
                curIntegPntCoords = []
                curNumIntegPnts = 1
                tempCoordValObj = elemCoordFieldArr[curFieldObjIndex]
                if doubleVals:
                    curCoordFieldData = tempCoordValObj.dataDouble # Tuple of floats
                else:
                    curCoordFieldData = tempCoordValObj.data
                curIntegPntCoords.append(list(curCoordFieldData))

            else: # Otherwise, need to calculate the centroid of the element manually with shape functions
                tempNodeOdbSet = myAssembly.NodeSetFromNodeLabels('tempNodeSetName' + str(curFieldObjIndex), tempNodeConnSetLabels)
                curElemNodalCoords, curElemNodalCoordsShape = calcDeformedNodeCoords(odbFrame, tempNodeOdbSet) # Calculate the current coordinates of the element's nodes

                if len(curElemNodalCoordsShape) == 2: # Make a 3D list, even if only one part instance was used in the node set
                    curElemNodalCoords = [curElemNodalCoords]

                # Use these node coordinates and element type to calculate the centroid via hand-coded element shape functions
                curIntegPntCoords, curNumIntegPnts = sf.getCorrectShapeFunc(curElemType, 'CENTROID', curElemNodalCoords) # Returns a 2D List

            if doubleVals:
                curFieldData = curFieldValObj.dataDouble # Tuple of floats
            else:
                curFieldData = curFieldValObj.data
            if isinstance(curFieldData, float) or isinstance(curFieldData, int):
                curFieldData = [curFieldData]

            # Have everything, but it needs to be indexed correctly for storage
            for integPntIndex in range(numElemOutPnts):
                tempDataList = [curElemLabel] + curIntegPntCoords[integPntIndex] + list(curFieldData)
                for curTempValIndex in range(len(tempDataList)):
                    allElemVals[curFieldObjIndex,integPntIndex,curTempValIndex] = tempDataList[curTempValIndex]

            allElemInstNames.append(curElemInstName) # Instance names that match up with the element index in allElemVals
            curFieldObjIndex = curFieldObjIndex + 1

            if (curFieldObjIndex % 2000) == 0:
                print '\nExtracted field outputs from ', curFieldObjIndex, ' elements ...\n'

    elif fieldPosKey == INTEGRATION_POINT:
        if singleInstanceSet: # Calculate the number instances
            numInstances = 1
        else:
            numInstances = len(odbSetInstNames)

        if doubleVals:
            numDataFieldVals = 4 + len(elemFieldValArr[0].dataDouble) # Element Label, X, Y, Z, Field Values ...
        else:
            numDataFieldVals = 4 + len(elemFieldValArr[0].data)

        allElemInstNames = []

        # Loop through all of the field values (multiple for each element, so it gets really messy)
        curFieldObjIndex = 0 # Index in the entire field value array (includes all integration points for all elements)
        curUniqueElemIndex = 0 # Keeps track of the number of (unique) elements encountered
        integPntIndex = 0 # Integration point index for the current element
        foundNewElem = True # Will be True if next field value object corresponds to a new element object
        for curFieldValObj in elemFieldValArr:

            if foundNewElem:
                foundNewElem = False
                integPntIndex = 0

                curElemInstObj = curFieldValObj.instance
                if curElemInstObj is None:
                    print 'ERROR: An element was found that does not belong to a part instance.'
                    return
                curElemInstName = curElemInstObj.name
                allElemInstNames.append(curElemInstName) # Instance names that match up with the element index in allElemVals
                curElemLabel = curFieldValObj.elementLabel
                # From the field values, get the actual element object
                curElemObj = curElemInstObj.getElementFromLabel(curElemLabel)

                # From the element object, get the node objects in order to calculate their current coordinates
                curElemType = curElemObj.type
                curElemNodeConn = curElemObj.connectivity # Node connectivity labels (i.e., integers) for the given element
                curElemNodeInstNames = curElemObj.instanceNames # list of instance names for each of the nodes that make up the element
                if curElemNodeInstNames is None:
                    print 'ERROR: Elements were found that are made up of nodes which do not belong to a part instance.'
                    return
                elif len(set(curElemNodeInstNames)) == 1: # Implies all nodes belong to one part instance (just one unique name)
                    tempNodeConnSetLabels = [ [curElemNodeInstNames[0],curElemNodeConn] ]
                else: # Shitty - multiple part instances involved in the nodes that define this element. WHY?!
                    tempNodeConnSetLabels = []
                    for curNodeConnIndex in range(len(curElemNodeConn)):
                        tempNodeConnSetLabels.append( [ curElemNodeInstNames[curNodeConnIndex] ,[ curElemNodeConn[curNodeConnIndex] ] ] )
                
                if coordFieldPresent: # Grab coordinates of all of the integration points of the same element from the COORD field
                    peekAheadNewElement = False
                    tempElemIndex = curFieldObjIndex
                    elemArrLen = len(elemCoordFieldArr)
                    curIntegPntCoords = []
                    numIntegPnts = 0
                    while (not peekAheadNewElement):
                        tempCoordValObj = elemCoordFieldArr[tempElemIndex]
                        tempPeekElemLabel = tempCoordValObj.elementLabel
                        tempPeekInstObj = tempCoordValObj.instance
                        tempPeekInstName = tempPeekInstObj.name
                        
                        if ((tempPeekInstName == curElemInstName) and (tempPeekElemLabel == curElemLabel)):
                            numIntegPnts = numIntegPnts + 1
                            if doubleVals:
                                curCoordFieldData = tempCoordValObj.dataDouble # Tuple of floats
                            else:
                                curCoordFieldData = tempCoordValObj.data
                            curIntegPntCoords.append(list(curCoordFieldData))
                        else:
                            peekAheadNewElement = True

                        tempElemIndex = tempElemIndex + 1
                        if tempElemIndex >= elemArrLen:
                            peekAheadNewElement = True

                else: # Need to calculate the coordinates manually from shape functions
                    tempNodeOdbSet = myAssembly.NodeSetFromNodeLabels('tempNodeSetName' + str(curFieldObjIndex), tempNodeConnSetLabels)
                    curElemNodalCoords, curElemNodalCoordsShape = calcDeformedNodeCoords(odbFrame, tempNodeOdbSet) # Calculate the current coordinates of the element's nodes

                    if len(curElemNodalCoordsShape) == 2: # Make a 3D list, even if only one part instance was used in the node set
                        curElemNodalCoords = [curElemNodalCoords]

                    # Use these node coordinates and element type to calculate the integration point locations via hand-coded element shape functions
                    curIntegPntCoords, numIntegPnts = sf.getCorrectShapeFunc(curElemType, 'INTEGRATION_POINT', curElemNodalCoords) # Returns a 2D List
                
                if curFieldObjIndex == 0: # First time through; need to allocate the output array to the right size
                    numIntegPnts_sum = 0 # Need to peek ahead and determine all the element types and number of respective integration points
                    numUniqueElems_sum = 0
                    maxIntegPnts = 1
                    tempFoundNewElem = True
                    tempUniqueElemIndex = 0
                    for tempElemFieldVal in elemFieldValArr:
                        if tempFoundNewElem:
                            tempFoundNewElem = False
                            tempElemInstObj = tempElemFieldVal.instance
                            tempElemObj = tempElemInstObj.getElementFromLabel(tempElemFieldVal.elementLabel)
                            tempElemType = tempElemObj.type
                            tempNumIntegPnts = sf.getCorrectNumIntegPnts(tempElemType, 'INTEGRATION_POINT')
                            if tempNumIntegPnts > maxIntegPnts:
                                maxIntegPnts = tempNumIntegPnts
                            numIntegPnts_sum = numIntegPnts_sum + tempNumIntegPnts
                            numUniqueElems_sum = numUniqueElems_sum + 1

                        tempUniqueElemIndex = tempUniqueElemIndex + 1

                        if tempUniqueElemIndex >= tempNumIntegPnts:
                            tempFoundNewElem = True
                            tempUniqueElemIndex = 0

                    # len(elemFieldValArr) includes integration points (thanks Abaqus). So have to skip past integration points to get number of unique elements
                    numElements = numUniqueElems_sum
                    # Can now instantiate the list of data that will be organized by part instances later and returned
                    allElemVals = np.zeros((numElements,maxIntegPnts,numDataFieldVals))

            if doubleVals:
                curFieldData = curFieldValObj.dataDouble # Tuple of floats
            else:
                curFieldData = curFieldValObj.data
            if isinstance(curFieldData, float) or isinstance(curFieldData, int):
                curFieldData = [curFieldData]

            tempDataList = [curElemLabel] + curIntegPntCoords[integPntIndex] + list(curFieldData)
            for curTempValIndex in range(len(tempDataList)):
                allElemVals[curUniqueElemIndex,integPntIndex,curTempValIndex] = tempDataList[curTempValIndex]

            curFieldObjIndex = curFieldObjIndex + 1
            integPntIndex = integPntIndex + 1

            if integPntIndex >= numIntegPnts:
                foundNewElem = True
                integPntIndex = 0

            if foundNewElem:
                curUniqueElemIndex = curUniqueElemIndex + 1
                if (curUniqueElemIndex % 2000) == 0:
                    print '\nExtracted field outputs from ', curUniqueElemIndex, ' elements ...\n'

    # Reshaping the element data into a 4D list by, [instance][element][integ pnt][field data]
    allElemValsList = allElemVals.tolist()
    elemInstNamesUnique = sorted(set(allElemInstNames)) # Returns as a list
    allElemVals_out = [ [] for _ in range(len(elemInstNamesUnique))] # Syntatic magic
    for curElemIndex in range(len(allElemInstNames)):
        curInstName = allElemInstNames[curElemIndex]
        curInstIndex = elemInstNamesUnique.index(curInstName)
        allElemVals_out[curInstIndex].append(allElemValsList[curElemIndex]) # This shit just went to a jagged 4D list; good stuff

    odb.close()
    print 'getNodeFieldValuesFromSetBatch(...) ended successfully!\n'
    return (allElemVals_out, elemInstNamesUnique);
# ----> END getIntegPntFieldValuesFromSetBatch(...) <----


# Creates a field output variable and permanently writes it to an Abaqus .odb file for each frame in a given step.
def writeFieldOutputData(odbFilePath_in, odbStepPositionKey_in, odbFramePosition_in, odbInstanceName_in):
    # ----> COPY FUNCTION INPUTS TO LOCAL VARIABLES <----
    # str - File path to the Abaqus .odb file to be opened (as read-only)
    odbFilePath = odbFilePath_in # str - File path to the Abaqus .odb file to be opened (as read-only)

    # odbStepPositionKey can be an index (input must be of type int) or the step name (input must be of type string)
    # int - Index of the .odb simulation step. Example: Use 0 for the first, -1 for the last.
    # str - Name of the key used to get the OdbStep object.
    odbStepPositionKey = odbStepPositionKey_in

    # odbFramePosition can be an index (input must be of type int) or a step time (input must be type float)
    # int - Index of the desired frame in the step. EX: Use 0 for the first, -1 for the last.
    # float - Step time. The frame that is closest to the this step time will be used.
    # str - If given as 'ALL', then all of the frames in the given step will be written to.
    odbFramePosition = odbFramePosition_in

    # Key to the instance within the .odb repository. All the nodes or integration points within this instance will be used.
    odbInstanceName = odbInstanceName_in

# ----> END writeFieldOutputData(...) <----

    # Open Abaqus .odb file (MUST BE SAFELY CLOSED LATER)
    print ''
    odb = openAbqOdbDangerously(odbFilePath)
    myAssembly = odb.rootAssembly
    myInstance = myAssembly.instances[odbInstanceName]

    # ----> WORKING THROUGH THE ABAQUS DATA STRUCTURES TO GET TO THE HISTORY VARIABLES <----
    print 'Looking for the .odb step, ', odbStepPositionKey
    # Get the OdbStep object from the user specified step
    if isinstance(odbStepPositionKey, int):
        odbStepObj = odb.steps.values()[odbStepPositionKey] 
    elif isinstance(odbStepPositionKey, str):
        odbStepObj = odb.steps[odbStepPositionKey]

    # Get the desired OdbFrame object 
    odbFrameArr = odbStepObj.frames
    calcOneFrame = True
    if isinstance(odbFramePosition, int):
        odbFrame = odbFrameArr[odbFramePosition]
        print 'Found the desired frame at index: ', odbFramePosition, '    Corresponding to step time: ', odbFrame.frameValue
    elif isinstance(odbFramePosition, float):
        odbFrame = odbStepObj.getFrame(frameValue=odbFramePosition, match=CLOSEST)
        print 'Found the desired frame at step time: ', odbFramePosition
    elif isinstance(odbFramePosition, str):
        if odbFramePosition.upper() in ['ALL']:
            calcOneFrame = False
            print 'Will calculate and write new field values for ALL of the frames in the current step.'
    print ''

    # ----> Inputs of the new field outputs being created <----
    userFieldName = 'TrIaX' # NOTE: This must be a unique field output name
    userFieldDescrip = 'Stress triaxiality (1/3 tr[sig] / mises)'
    userFieldType = SCALAR

    print 'Calculating field outputs. This could take a while ...'
    frameObjIndex = 0
    for curOdbFrameObj in odbFrameArr:
        if calcOneFrame:
            curFrameTime = curOdbFrameObj.frameValue
            if curFrameTime != odbFrame.frameValue:
                continue

        # Create a new, empty field output object in the current frame. Will fill this up later.    
        userFieldOutObj = curOdbFrameObj.FieldOutput(name=userFieldName, description=userFieldDescrip, type=userFieldType)

        # Instantiate variables here to be used to addData to this new field output object later
        userPosition = INTEGRATION_POINT
        userLabels = []
        userData = []

        # ----> Specific calculations to get the new field output <----
        # I'm trying to calculate the stress triaxiality in this case.

        # First, get the array of FieldOutput objects corresponding to the part instance
        sigAllFieldOut = curOdbFrameObj.fieldOutputs['S']
        sigFieldOut = sigAllFieldOut.getSubset(region=myInstance, position=userPosition)
        sigFieldOut.setValidInvariants(validInvariants=[MISES,PRESS])
        sigFieldVals = sigFieldOut.values # Array of FieldValue objects
        oneThird = 1.0/3.0

        # Next, loop through all of the values and calculate the new data to be stored
        curFieldIndex = 0
        for curFieldVal in sigFieldVals:
            if userPosition in [ELEMENT_NODAL, NODAL]:
                curLabel = curFieldVal.nodeLabel
            else:
                curLabel = curFieldVal.elementLabel

            curMises = curFieldVal.mises # sqrt( (3/2)*(sig_dev : sig_dev) ) where sig_dev is the deviatoric stress tensor
            curPress = curFieldVal.press # -(1/3)*tr[sig]
            if curMises != 0.0:
                curTriax = -curPress/curMises # Pressure includes a negative sign, so need to "reverse" that with another
            elif curPress != 0.0:
                if curPress < 0.0:
                    curTriax = -10.0 # This would go to infinity, but 10 is big enough in the world of stress triaxiality
                else:
                    curTriax = 10.0
            else:
                curTriax = 0.0 # Undefined if both numerator and denominator are zero, so just picked zero.

            if userPosition in [INTEGRATION_POINT]:
                if curFieldVal.integrationPoint == 1: # Only store the element label once for each unique element
                    userLabels.append(curLabel)  # Achieved by checking if on the first integration point (starts on 1 rather than 0 in this case)

            userData.append([curTriax])
            curFieldIndex = curFieldIndex + 1

        # ----> Add the new data to the empty field output <----
        userFieldOutObj.addData(position=userPosition, instance=myInstance, labels=userLabels, data=userData)

        frameObjIndex = frameObjIndex + 1
        if ((frameObjIndex-1)%2) == 0:
            print 'Calculated ', frameObjIndex-1, ' frames ...'

    odb.save()
    odb.close()
    print '\nwriteFieldOutputData(...) ended successfully!\n'
    return 
# ----> END writeFieldOutputData(...) <----