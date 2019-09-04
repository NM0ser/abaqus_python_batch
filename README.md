# abaqus_python_batch
Python scripts for the Abaqus FEA Python interpreter that allows for flexible batch processing of Abaqus output (.odb) files.

---------- Overview ---------- 
The driver Python scripts in the following "demo" subdirectories showcase the various capabilities of my post-
processing scripts for Abaqus .odb files. These scripts were tested used Abaqus 2017 with the built-in Python 2.7
interpreter, but the provided scripts should be general enough for older versions of Abaqus. While it is certainly 
possible to modify an .odb file (e.g., creating new element sets or field output variables), all of the provided 
scripts open Abaqus .odb files in solely read-only mode. The purpose of these scripts is to extract various types of 
simulation data from an .odb file and output it into an organized .csv text file on the hard drive. To run a script, 
you must first start an Abaqus Command terminal. For more information, see the Abaqus manual in sections, "Abaqus -> 
Execution -> Execution Procedures -> Python Execution" as well as, "Abaqus -> Scripting -> About the Abaqus Scripting 
Interface". Within the Abaqus Command terminal, a user Python script can be executed by typing: 

> abaqus python myScriptName.py

where myScriptName.py is the python script you wish to run. Make sure you are in the same directory as the script that 
you wish to execute. The provided demonstrations should be executed in numerical order (i.e., start with Demo 0). In 
each subdirectory, there will be a "driver_" python script, which is the script to submit to the Abaqus Python 
interpreter that drives the post-processing functions. Each demonstration subdirectory has a local, identical copy of 
these helper post-processing scripts. Note that the available post-processing helper functions are in the following 
files:

1) abaqus_moser_shape_functions.py
2) abaqus_moser_utility_functions.py


---------- Demo 0 ----------
Run the supplied Abaqus Explicit simulation, provided as a text-based "hexContact_custom.inp" file. It should take 
less than 10 minutes to run on 6 CPU's. The simulation is a double-contact problem that utilizes both brick and 
tetrahedral elements. The resultant "hexContact.odb" must remain in this directory, since it will be utilized to 
showcase the capabilities of the scripts.


---------- Demo 1 ----------
Execute the "driver_getOdbFileStructure.py" script. This script creates a text file that informs the user of the names 
of existing sets and output data in the .odb file, which will be needed in order to retrieve these data later. 
Similar to the other driver scripts, all of these scripts have been coded with generality in mind. So, the only 
modifications that should be required to use these scripts for other .odb files are to just change the well-commented 
user inputs. 


---------- Demo 2 ----------
Execute the "driver_getHistoryVals.py" script. This script demonstrates how to extract multiple history outputs and 
output them to a single .csv file. By default, the script extracts the X-, Y-, and Z-components of the contact force 
for both the top and bottom rods. For this script to work properly, however, the history outputs should be the same 
length implying that they were outputted at the same time intervals. Note that the keywords used for the inputs were 
found from the resultant text file in Demo 1.


---------- Demo 3.1 ----------
Execute the "driver1_getNodeFieldVals.py" script. This script extracts a NODAL field value (velocity) from nodes along 
the back of both the top and bottom rods. Since the node set spans multiple part instances, the output file also 
automatically includes the nodes' corresponding instance names in the last column. Also, the element type in both part 
instances are different, which is not a problem for this script so long as all of the nodes in the set contain the 
desired field output type. Notice that the coordinates are automatically calculated for the selected nodes. The 
scripts will utilize the COORD node output key if it's available. Otherwise, the coordinates will be calculated using 
the initial coordinates and displacement field.


---------- Demo 3.2 ----------
Execute the "driver2_getNodeFieldVals.py" script. This script reads a user-defined node set that spans multiple 
instances (see the file "demo3p2_userNSet.csv"), and then calculates the ELEMENT_NODAL field values (equivalent 
plastic strain) and writes it out to a file. Generally speaking, however, it is NOT recommended to interpolate the 
field values to the nodes via the ELEMENT_NODAL procedure; this script uses the closest integration point relative to 
the desired node and simply interpolates this single field value to the node. There is no averaging by the 
interpolation of other neighboring integration points, which could significantly affect the result. Abaqus CAE by 
default uses a 75% threshold averaging scheme when stresses and strains (field values at the integration points) are 
visualized on the surfaces of elements and nodes. When possible, use the example scripts in Demo 4 to extract the data 
at the integration points, since these will be the actual numbers that were utilized by the solver during the 
simulation. 


---------- Demo 4.1 ----------
Execute the "driver1_getIntegPntFieldVals.py" script. This script extracts the six unique components of the stress 
tensor at the centroid of the elements along the top surface of the sheet. However, since these elements are 
reduced-integration linear bricks, this is the same as extracting the stress at the sole integration point. Just like 
the node field script, the instance label for each element will be appended to the output if the element set spans 
multiple part instances. Also, the coordinates of the centroid locations are given. These values are extracted 
from the COORD element output key if it's available. Otherwise, the coordinates are calculated using the element's 
current nodal coordinates and manually-coded element shape functions. Since this is a lot of work, only a select few 
element types are currently supported (see the comments in driver script for more information).


---------- Demo 4.2 ----------
Execute the "driver2_getIntegPntFieldVals.py" script. This script extracts the six unique components of the stress 
tensor at all of the integration points for the elements in both Rod 1 and Rod 2. This example is particularly tricky, 
because this set of elements spans multiple part instances, which in themselves, contain different types of fully 
integrated elements. When extracting the data, the script first looks for the element type with the largest number of 
integration points. In this case, it is the fully integrated linear brick (8 integration points) since the quadratic 
tetrahedral contains 4 integration points. When outputting, the script will simply padd the extra columns - 
corresponding to the nonexistent integration points - with zeros for the tetrahedral elements. As with the CENTROID 
case, the coordinates for all of the integration points are also provided. Also, when multiple integration points are 
discovered, the driver script automatically replicates the header and appends each of the header strings with "_IP#" 
to denote which integration point the data corresponds to (i.e., "_IP2" corresponds to integration point 2 for that 
element). 