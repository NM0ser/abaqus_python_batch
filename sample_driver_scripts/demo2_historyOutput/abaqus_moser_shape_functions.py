import numpy as np
import math


# This function will calculate the coordinates of the integration points (or centroid) of a single element by
# using shape functions and the natural coordinates of the element. As input, the Abaqus element type must be given,
# the type of position within the element (centroid or integration points), as well as the current nodal coordinates
# for the nodes that make up the element. The ordering of these nodes is assumed to follow the Abaqus definitions. 
# This function is essentially a driver that ensures the right shape functions get called, and then shape the resultant
# coordinate data appropriately in a multidimensional list.
def getCorrectShapeFunc(elemTypeIn, elemPositionIn, ndCoordsArrIn):
    # ----------------> INPUTS <----------------
    elemType = elemTypeIn # str - Abaqus element type identifier (very limited number of elements currently supported)
    elemPosition = elemPositionIn # str - Currently supports 'CENTROID' and 'INTEGRATION_POINT'

    # list[list[list[]]] - 3D list where the indices are as follows ( list[i][j][k] ):
    #   [i] - Data corresponding to a part instance (if all the nodes are on one instance, then a bit redundant)
    #   [j] - Data corresponding to a node that is a member of the current part instance
    #   [k] - When k=0, should be the node label (int). When k=1:3, should be the X, Y, Z coordinates (float) of the node
    #   These nodes will be accessed in order via a triple for-loop that starts at index i=0, then k=0, and then k=0.
    #   The order that the nodes are retrieved should be the same order used by Abaqus in the element's definition.
    ndCoordsArr = ndCoordsArrIn 

    # ----------------> OUTPUT <----------------
    # A 2D list of the calculated coordinates at the point(s) of interest. Here are what the indices correspond to ( list[i][j] ):
    #   [i] - Rows correspond to each of the integration points (or single centroid). Same ordering used as defined in Abaqus
    #   [j] - Columns correspond to the X, Y, Z coordinates for each integration point (or single centroid)
    pntCoordsArr_out = np.matrix([[]]) # Converted back to a list before returning
    numIntegPnts_out = [] # Output the number of integration points. Initialize to 1, but change it if needed

    if elemPosition.upper() not in ['CENTROID', 'INTEGRATION_POINT']:
        print 'ERROR: Calculating the coordinates at the element position ', elemPosition, ' is not supported.\nPlease use either "CENTROID" or "INTEGRATION_POINT".'
        return pntCoordsArr_out
    
    ndCoords2DArr = [] # This creates a 2D list of nodal coordinates to be used by the shape function routines. 
    for curInstance in ndCoordsArr:
        for curNodeRow in curInstance:
            ndCoords2DArr.append(curNodeRow[1:]) # ndCoords2DArr consists of rows of [X, Y, Z] coordinates, each row corresponding to a node

    if elemType in ['C3D8R', 'C3D8RH']:
        # The centroid and the sole integration point are the same for the reduced-integration linear brick
        if elemPosition in ['CENTROID', 'INTEGRATION_POINT']:
            pntCoords2DArr_out = quad8ShapeFun(ndCoords2DArr, C3D8R_integPnts_coord)
    
    elif elemType in ['C3D8', 'C3D8H','C3D8I', 'C3D8IH']:
        if elemPosition == 'CENTROID':
            pntCoords2DArr_out = quad8ShapeFun(ndCoords2DArr, np.matrix([[0.0, 0.0, 0.0]]))
        elif elemPosition == 'INTEGRATION_POINT':
            pntCoords2DArr_out = quad8ShapeFun(ndCoords2DArr, C3D8_integPnts_coord)

    elif elemType in ['C3D20R', 'C3D20RH']:
        if elemPosition == 'CENTROID':
            pntCoords2DArr_out = quad20ShapeFun(ndCoords2DArr, np.matrix([[0.0, 0.0, 0.0]]))
        elif elemPosition == 'INTEGRATION_POINT':
            pntCoords2DArr_out = quad20ShapeFun(ndCoords2DArr, C3D20R_integPnts_coord)

    elif elemType in ['C3D4', 'C3D4H']:
        if elemPosition in ['CENTROID', 'INTEGRATION_POINT']:
            # The centroid and the sole integration point are the same for the linlear tetrahedral
            pntCoords2DArr_out = tet4ShapeFun(ndCoords2DArr, C3D4_integPnts_coord)

    elif elemType in ['C3D10','C3D10H', 'C3D10M', 'C3D10MH']:
        if elemPosition == 'CENTROID':
            pntCoords2DArr_out = tet10ShapeFun(ndCoords2DArr, np.matrix([[0.25, 0.25, 0.25, 1.0 - 0.25 - 0.25 - 0.25]]))
        elif elemPosition == 'INTEGRATION_POINT':
            pntCoords2DArr_out = tet10ShapeFun(ndCoords2DArr, C3D10_integPnts_coord)

    else:
        print 'WARNING: Element type ', elemType, ' is not currently supported. Writing zeros for the coordinates.'
        pntCoords2DArr_out = np.matrix([[0.0, 0.0, 0.0]])

    # Calculate the number of integration points for the element type and return that
    numIntegPnts_out = getCorrectNumIntegPnts(elemType, elemPosition)

    return (pntCoords2DArr_out.tolist(), numIntegPnts_out);


# Based on the element type, return the number of integration points that will be calculated. If CENTROID is 
# the chosen point for any element, this always returns 1 since only one point is will be calculated.
def getCorrectNumIntegPnts(elemTypeIn, elemPositionIn):
    elemType = elemTypeIn # str - Abaqus element type identifier (very limited number of elements currently supported)
    elemPosition = elemPositionIn # str - Currently supports 'CENTROID' and 'INTEGRATION_POINT'
    numIntegPnts_out = 1 # Output the number of integration points. Initialize to 1, but change it if needed

    if elemType in ['C3D8R', 'C3D8RH']:
        numIntegPnts_out = 1
    elif elemType in ['C3D8', 'C3D8H','C3D8I', 'C3D8IH']:
        numIntegPnts_out = 8
    elif elemType in ['C3D20R', 'C3D20RH']:
        numIntegPnts_out = 8
    elif elemType in ['C3D4', 'C3D4H']:
        numIntegPnts_out = 1
    elif elemType in ['C3D10','C3D10H', 'C3D10M', 'C3D10MH']:
        numIntegPnts_out = 4

    if elemType in ['CENTROID']:
        numIntegPnts_out = 1

    return numIntegPnts_out


# Adopting same node numbering as in Abaqus. Returns -1.0 if an error occurred. 
# ndCoordsIn should be an np.matrix[8,3] where the 8 rows correspond to the 8 nodes, and 3 columns for X, Y, Z-coordinates.
# natCoordIn should be an np.matrix[n,3] where these are the natural coordinates (from -1.0 to 1.0) to be evaluated (up to n to evaluate). 
# The function will return an np.matrix[n,3] where these are the transformed natural coordinates in X, Y, Z-coordinate space.
def quad8ShapeFun(ndCoordsIn, natCoordIn):

    ndCoords = np.matrix(ndCoordsIn)
    if ndCoords.ndim != 2:
        return -1.0
    elif (ndCoords.shape[1] != 3) or (ndCoords.shape[0] != 8):
        return -1.0

    natCoord = np.matrix(natCoordIn)
    if natCoord.ndim > 2:
        return -1.0
    elif natCoord.shape[1] != 3:
        return -1.0

    oneEighth = 1.0/8.0
    coordsOut = np.matrix(np.zeros(natCoord.shape))
    for curRow in range(natCoord.shape[0]):

        xiCur = natCoordIn[curRow, 0]
        etaCur = natCoordIn[curRow, 1]
        muCur = natCoordIn[curRow, 2]

        n1e = oneEighth*(1.0 - xiCur)*(1.0 - etaCur)*(1.0 - muCur)
        n2e = oneEighth*(1.0 + xiCur)*(1.0 - etaCur)*(1.0 - muCur)
        n3e = oneEighth*(1.0 + xiCur)*(1.0 + etaCur)*(1.0 - muCur)
        n4e = oneEighth*(1.0 - xiCur)*(1.0 + etaCur)*(1.0 - muCur)
        n5e = oneEighth*(1.0 - xiCur)*(1.0 - etaCur)*(1.0 + muCur)
        n6e = oneEighth*(1.0 + xiCur)*(1.0 - etaCur)*(1.0 + muCur)
        n7e = oneEighth*(1.0 + xiCur)*(1.0 + etaCur)*(1.0 + muCur)
        n8e = oneEighth*(1.0 - xiCur)*(1.0 + etaCur)*(1.0 + muCur)
        nieArr = np.array([n1e, n2e, n3e, n4e, n5e, n6e, n7e, n8e]);

        xNat = 0.0
        yNat = 0.0
        zNat = 0.0
        for ndIndex in range(8):
            xNat = xNat + nieArr[ndIndex]*ndCoords[ndIndex,0]
            yNat = yNat + nieArr[ndIndex]*ndCoords[ndIndex,1]
            zNat = zNat + nieArr[ndIndex]*ndCoords[ndIndex,2]

        coordsOut[curRow, 0] = xNat
        coordsOut[curRow, 1] = yNat
        coordsOut[curRow, 2] = zNat

    return coordsOut

# Coordinates in the parent domain of the centroid integration point in element C3D8R is: np.matrix([[0.0, 0.0, 0.0]])
C3D8R_integPnts_coord = np.matrix( [[0.0, 0.0, 0.0]])

# Coordinates in parent domain of the 8 integration points in element C3D8
C3D8_integPnts_coord = np.matrix( [[-1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)],
                                     [1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)],
                                     [-1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)],
                                     [1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)],
                                     [-1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)],
                                     [1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)],
                                     [-1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)],
                                     [1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)]] ) 


# Adopting same node numbering as in Abaqus (see element type C3D20R). Returns -1.0 if an error occurred. 
# ndCoordsIn should be an np.matrix[20,3] where the 20 rows correspond to the 20 nodes of a serendipity quadratic brick, and 3 columns 
# for X, Y, Z-coordinates. natCoordIn should be an np.matrix[n,3] where these are the natural coordinates (from -1.0 to 1.0) to be 
# evaluated (up to n to evaluate). The function will return an np.matrix[n,3] where these are the transformed natural coordinates in 
# X, Y, Z-coordinate space.
def quad20ShapeFun(ndCoordsIn, natCoordIn):

    ndCoords = np.matrix(ndCoordsIn)
    if ndCoords.ndim != 2:
        return -1.0
    elif (ndCoords.shape[1] != 3) or (ndCoords.shape[0] != 20):
        return -1.0

    natCoord = np.matrix(natCoordIn)
    if natCoord.ndim > 2:
        return -1.0
    elif natCoord.shape[1] != 3:
        return -1.0

    oneEighth = 1.0/8.0
    oneFourth = 1.0/4.0
    coordsOut = np.matrix(np.zeros(natCoord.shape))
    for curRow in range(natCoord.shape[0]):
        xiCur = natCoordIn[curRow, 0]
        etaCur = natCoordIn[curRow, 1]
        zetaCur = natCoordIn[curRow, 2]

        xez1 = [-1.0, -1.0, -1.0]
        n1e = oneEighth*(1.0 + xez1[0]*xiCur)*(1.0 + xez1[1]*etaCur)*(1.0 + xez1[2]*zetaCur)*(xez1[0]*xiCur + xez1[1]*etaCur + xez1[2]*zetaCur - 2.0)

        xez2 = [1.0, -1.0, -1.0]
        n2e = oneEighth*(1.0 + xez2[0]*xiCur)*(1.0 + xez2[1]*etaCur)*(1.0 + xez2[2]*zetaCur)*(xez2[0]*xiCur + xez2[1]*etaCur + xez2[2]*zetaCur - 2.0)

        xez3 = [1.0, 1.0, -1.0]
        n3e = oneEighth*(1.0 + xez3[0]*xiCur)*(1.0 + xez3[1]*etaCur)*(1.0 + xez3[2]*zetaCur)*(xez3[0]*xiCur + xez3[1]*etaCur + xez3[2]*zetaCur - 2.0)

        xez4 = [-1.0, 1.0, -1.0]
        n4e = oneEighth*(1.0 + xez4[0]*xiCur)*(1.0 + xez4[1]*etaCur)*(1.0 + xez4[2]*zetaCur)*(xez4[0]*xiCur + xez4[1]*etaCur + xez4[2]*zetaCur - 2.0)

        xez5 = [-1.0, -1.0, 1.0]
        n5e = oneEighth*(1.0 + xez5[0]*xiCur)*(1.0 + xez5[1]*etaCur)*(1.0 + xez5[2]*zetaCur)*(xez5[0]*xiCur + xez5[1]*etaCur + xez5[2]*zetaCur - 2.0)

        xez6 = [1.0, -1.0, 1.0]
        n6e = oneEighth*(1.0 + xez6[0]*xiCur)*(1.0 + xez6[1]*etaCur)*(1.0 + xez6[2]*zetaCur)*(xez6[0]*xiCur + xez6[1]*etaCur + xez6[2]*zetaCur - 2.0)

        xez7 = [1.0, 1.0, 1.0]
        n7e = oneEighth*(1.0 + xez7[0]*xiCur)*(1.0 + xez7[1]*etaCur)*(1.0 + xez7[2]*zetaCur)*(xez7[0]*xiCur + xez7[1]*etaCur + xez7[2]*zetaCur - 2.0)

        xez8 = [-1.0, 1.0, 1.0]
        n8e = oneEighth*(1.0 + xez8[0]*xiCur)*(1.0 + xez8[1]*etaCur)*(1.0 + xez8[2]*zetaCur)*(xez8[0]*xiCur + xez8[1]*etaCur + xez8[2]*zetaCur - 2.0)

        xez9 = [0.0, -1.0, -1.0]
        n9e = oneFourth*(1.0 - xiCur*xiCur)*(1.0 + xez9[1]*etaCur)*(1.0 + xez9[2]*zetaCur)

        xez10 = [1.0, 0.0, -1.0]
        n10e = oneFourth*(1.0 + xez10[0]*xiCur)*(1.0 - etaCur*etaCur)*(1.0 + xez10[2]*zetaCur)

        xez11 = [0.0, 1.0, -1.0]
        n11e = oneFourth*(1.0 - xiCur*xiCur)*(1.0 + xez11[1]*etaCur)*(1.0 + xez11[2]*zetaCur)

        xez12 = [-1.0, 0.0, -1.0]
        n12e = oneFourth*(1.0 + xez12[0]*xiCur)*(1.0 - etaCur*etaCur)*(1.0 + xez12[2]*zetaCur)

        xez13 = [0.0, -1.0, 1.0]
        n13e = oneFourth*(1.0 - xiCur*xiCur)*(1.0 + xez13[1]*etaCur)*(1.0 + xez13[2]*zetaCur)

        xez14 = [1.0, 0.0, 1.0]
        n14e = oneFourth*(1.0 + xez14[0]*xiCur)*(1.0 - etaCur*etaCur)*(1.0 + xez14[2]*zetaCur)

        xez15 = [0.0, 1.0, 1.0]
        n15e = oneFourth*(1.0 - xiCur*xiCur)*(1.0 + xez15[1]*etaCur)*(1.0 + xez15[2]*zetaCur)

        xez16 = [-1.0, 0.0, 1.0]
        n16e = oneFourth*(1.0 + xez16[0]*xiCur)*(1.0 - etaCur*etaCur)*(1.0 + xez16[2]*zetaCur)

        xez17 = [-1.0, -1.0, 0.0] 
        n17e = oneFourth*(1.0 + xez17[0]*xiCur)*(1.0 + xez17[1]*etaCur)*(1.0 - zetaCur*zetaCur)

        xez18 = [1.0, -1.0, 0.0]
        n18e = oneFourth*(1.0 + xez18[0]*xiCur)*(1.0 + xez18[1]*etaCur)*(1.0 - zetaCur*zetaCur)

        xez19 = [1.0, 1.0, 0.0]
        n19e = oneFourth*(1.0 + xez19[0]*xiCur)*(1.0 + xez19[1]*etaCur)*(1.0 - zetaCur*zetaCur)

        xez20 = [-1.0, 1.0, 0.0]
        n20e = oneFourth*(1.0 + xez20[0]*xiCur)*(1.0 + xez20[1]*etaCur)*(1.0 - zetaCur*zetaCur)

        nieArr = np.array([n1e, n2e, n3e, n4e, n5e, n6e, n7e, n8e, n9e, n10e,
                           n11e, n12e, n13e, n14e, n15e, n16e, n17e, n18e, n19e, n20e]);

        xNat = 0.0
        yNat = 0.0
        zNat = 0.0
        for ndIndex in range(20):
            xNat = xNat + nieArr[ndIndex]*ndCoords[ndIndex,0]
            yNat = yNat + nieArr[ndIndex]*ndCoords[ndIndex,1]
            zNat = zNat + nieArr[ndIndex]*ndCoords[ndIndex,2]

        coordsOut[curRow, 0] = xNat
        coordsOut[curRow, 1] = yNat
        coordsOut[curRow, 2] = zNat

    return coordsOut

# Coordinates in parent domain of the 8 integration points in element C3D20R
C3D20R_integPnts_coord = np.matrix( [[-1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)],
                                     [1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)],
                                     [-1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)],
                                     [1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0)],
                                     [-1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)],
                                     [1.0/math.sqrt(3.0), -1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)],
                                     [-1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)],
                                     [1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)]] ) 


# Adopting same node numbering as in Abaqus. Returns -1.0 if an error occurred. 
# ndCoordsIn should be an np.matrix[4,3] where the 4 rows correspond to the 4 nodes of linear tetrahedron, and 3 columns 
# for X, Y, Z-coordinates. natCoordIn should be an np.matrix[n,4] where these are the natural coordinates (from 0.0 to 1.0) to be 
# evaluated (up to n to evaluate). The function will return an np.matrix[n,3] where these are the transformed natural coordinates in 
# X, Y, Z-coordinate space.
def tet4ShapeFun(ndCoordsIn, natCoordIn):
    ndCoords = np.matrix(ndCoordsIn)
    if ndCoords.ndim != 2:
        return -1.0
    elif (ndCoords.shape[1] != 3) or (ndCoords.shape[0] != 4):
        return -1.0

    natCoord = np.matrix(natCoordIn)
    if natCoord.ndim > 2:
        return -1.0
    elif natCoord.shape[1] != 4:
        return -1.0

    coordsOut = np.matrix(np.zeros( (natCoord.shape[0],3) ))
    for curRow in range(natCoord.shape[0]):
        zeta1Cur = natCoordIn[curRow, 0]
        zeta2Cur = natCoordIn[curRow, 1]
        zeta3Cur = natCoordIn[curRow, 2]
        zeta4Cur = natCoordIn[curRow, 3]

        n1e = zeta1Cur
        n2e = zeta2Cur
        n3e = zeta3Cur
        n4e = zeta4Cur
        nieArr = np.array([n1e,n2e,n3e,n4e])

        xNat = 0.0
        yNat = 0.0
        zNat = 0.0
        for ndIndex in range(4):
            xNat = xNat + nieArr[ndIndex]*ndCoords[ndIndex,0]
            yNat = yNat + nieArr[ndIndex]*ndCoords[ndIndex,1]
            zNat = zNat + nieArr[ndIndex]*ndCoords[ndIndex,2]

        coordsOut[curRow, 0] = xNat
        coordsOut[curRow, 1] = yNat
        coordsOut[curRow, 2] = zNat

    return coordsOut

# Coordinates in the parent domain of the centroid integration point in element C3D4. Note that in tetrahedral
# elements, the fourth natural coordinate is constrained (i.e., dependent) on the first three.
C3D4_integPnts_coord = np.matrix( [[0.25, 0.25, 0.25, 1.0 - 0.25 - 0.25 - 0.25]])


# Adopting same node numbering as in Abaqus. Returns -1.0 if an error occurred. 
# ndCoordsIn should be an np.matrix[10,3] where the 10 rows correspond to the 10 nodes of quadratic tetrahedron, and 3 columns 
# for X, Y, Z-coordinates. natCoordIn should be an np.matrix[n,4] where these are the natural coordinates (from 0.0 to 1.0) to be 
# evaluated (up to n to evaluate). The function will return an np.matrix[n,3] where these are the transformed natural coordinates in 
# X, Y, Z-coordinate space.
def tet10ShapeFun(ndCoordsIn, natCoordIn):
    ndCoords = np.matrix(ndCoordsIn)
    if ndCoords.ndim != 2:
        return -1.0
    elif (ndCoords.shape[1] != 3) or (ndCoords.shape[0] != 10):
        return -1.0

    natCoord = np.matrix(natCoordIn)
    if natCoord.ndim > 2:
        return -1.0
    elif natCoord.shape[1] != 4:
        return -1.0

    coordsOut = np.matrix(np.zeros( (natCoord.shape[0],3) ))
    for curRow in range(natCoord.shape[0]):
        zeta1Cur = natCoordIn[curRow, 0]
        zeta2Cur = natCoordIn[curRow, 1]
        zeta3Cur = natCoordIn[curRow, 2]
        zeta4Cur = natCoordIn[curRow, 3]

        n1e = zeta1Cur*(2.0*zeta1Cur - 1.0)
        n2e = zeta2Cur*(2.0*zeta2Cur - 1.0)
        n3e = zeta3Cur*(2.0*zeta3Cur - 1.0)
        n4e = zeta4Cur*(2.0*zeta4Cur - 1.0)
        n5e = 4.0*zeta1Cur*zeta2Cur
        n6e = 4.0*zeta2Cur*zeta3Cur
        n7e = 4.0*zeta3Cur*zeta1Cur
        n8e = 4.0*zeta1Cur*zeta4Cur
        n9e = 4.0*zeta2Cur*zeta4Cur
        n10e = 4.0*zeta3Cur*zeta4Cur
        nieArr = np.array([n1e,n2e,n3e,n4e,n5e,n6e,n7e,n8e,n9e,n10e])

        xNat = 0.0
        yNat = 0.0
        zNat = 0.0
        for ndIndex in range(10):
            xNat = xNat + nieArr[ndIndex]*ndCoords[ndIndex,0]
            yNat = yNat + nieArr[ndIndex]*ndCoords[ndIndex,1]
            zNat = zNat + nieArr[ndIndex]*ndCoords[ndIndex,2]

        coordsOut[curRow, 0] = xNat
        coordsOut[curRow, 1] = yNat
        coordsOut[curRow, 2] = zNat

    return coordsOut

# Coordinates in the parent domain of the centroid integration point in element C3D10. Note that in tetrahedral
# elements, the fourth natural coordinate is constrained (i.e., dependent) on the first three.
C3D10_integPnts_coord = np.matrix( [[0.58541020, 0.13819660, 0.13819660, 1.0 - 0.58541020 - 0.13819660 - 0.13819660],
                                    [0.13819660, 0.58541020, 0.13819660, 1.0 - 0.13819660 - 0.58541020 - 0.13819660],
                                    [0.13819660, 0.13819660, 0.58541020, 1.0 - 0.13819660 - 0.13819660 - 0.58541020],
                                    [0.13819660, 0.13819660, 0.13819660, 1.0 - 0.13819660 - 0.13819660 - 0.13819660]])