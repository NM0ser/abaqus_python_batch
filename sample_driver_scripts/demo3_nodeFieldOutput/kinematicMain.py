# Creator: Newell Moser
# Python 3 (compatible with Python 2)
# 7/16/2015
#
# EASTER EGG
#
# Simple text-based game that randomly places a "plane" in space. Based on
# user-specified launch angle and velocity, a projectile is launched with
# normal Earth gravity. The streamline is visualized, and the game is over when
# the projectile collides with the plane.
#
from __future__ import print_function
import random
import math
#import numpy as np

# Screen class
class Screen:
    def __init__(self):
        self.__width = 71 # INTEGERS; Screen is initially set to 51 characters wide
        self.__height = 36 # and 26 characters tall
        self.__xUnit = 2 # 2 meters/character in the x-direction
        self.__yUnit = 4 # 4 meters/character in the y-direction
        self.__win = [[' ' for m in range(0,self.__width)] for n in range(0,self.__height)]
        self.clear() # Clear the just initialized array representing the to-be printed "window"

    # Function methods to get or set data members/attributes   
    def getWidth(self):
        return self.__width
    def getHeight(self):
        return self.__height
    def getXUnit(self):
        return self.__xUnit
    def getYUnit(self):
        return self.__yUnit
    def setWidth(self,width):
        self.__width = int(width)
        self.__win = [[' ' for m in range(0,self.__width)] for n in range(0,self.__height)]
        self.clear()
    def setHeight(self,height):
        self.__height = int(height)
        self.__win = [[' ' for m in range(0,self.__width)] for n in range(0,self.__height)]
        self.clear()
    def setXUnit(self,xUnit):
        self.__xUnit = xUnit
    def setYUnit(self,yUnit):
        self.__yUnit = yUnit

    # Clears the screen array to spaces and creates the border
    def clear(self):
        for m in range(0,self.__height):
            for n in range(0,self.__width):
                if m >= self.__height-1 and n <= 0:
                    self.__win[m][n] = '#'
                elif m <= 0 or m >= self.__height-1:
                    self.__win[m][n] = '-'
                elif n <= 0 or n >= self.__width-1:
                    self.__win[m][n] = '|'
                else:
                    self.__win[m][n] = ' '

    # Prints the screen array to the standard output (i.e. the screen)
    def show(self):
        print("\n"*80)
        print("*** PLANE DESTROYER ***     (Type -1 to exit)")
        for m in range(0,self.__height):
            for n in range(0,self.__width):
                print(self.__win[m][n], end="")
            print("")

    # Writes a text-character to a location in the screen array.
    # It's assumed that the location is given in meters, thus will
    # be automatically converted into character spacing.
    def addText(self, text, xLoc, yLoc):
        try:
            if len(text) > 1:
                print("Cannot add text to screen, must be only one character.")
        except TypeError:
            print("Oops, can only print text characters to the screen!")

        #print(xArr, math.floor(xArr))
        xArr = float(xLoc) / self.__xUnit
        yArr = (self.__height - 1.0) - float(yLoc) / self.__yUnit

        if xArr < 0 or xArr >= self.__width:
            print("X-location is out of the domain. Current max width is ", (self.__width-1)*self.__xUnit, " meters.")
        elif yArr < 0 or yArr >= self.__height:
            print("Y-location is out of the domain. Current max height is ", (self.__height-1)*self.__yUnit, " meters.")
        else:
            self.__win[self.regRound(yArr)][self.regRound(xArr)] = text
            return [self.regRound(xArr),self.regRound(yArr)]

    # Python 3.x uses Banker's rounding, this is a function to utilize
    # traditional rounding techniques
    def regRound(self,value):
        fracPart = math.modf(value)
        fracPart = fracPart[0]

        if fracPart < 0.5:
            return int(math.floor(value))
        else:
            return int(math.ceil(value))
        

# Python 3.x uses Banker's rounding, this is a function to utilize
# traditional rounding techniques
def regRound(value):
    fracPart = math.modf(value)
    fracPart = fracPart[0]

    if fracPart < 0.5:
        return int(math.floor(value))
    else:
        return int(math.ceil(value))

def checkCollision(shipXY,bulletXY):
    if bulletXY[0] >= shipXY[0]-1 and bulletXY[0] <= shipXY[0]+1:
        if bulletXY[1] == shipXY[1]:
            return True
    return False

def frange(start,stop, step=1.0):
    while start < stop:
        yield start
        start +=step

def runEasterEgg():
    PI = 355.0/113.0
    GRAV = 9.81

    # Initialize a Screen object
    scn = Screen()

    # Store maximum values for width and height [meters] that can be plotted
    xUnit = scn.getXUnit() #Unit conversions in meters/character
    yUnit = scn.getYUnit()
    maxWidth = (scn.getWidth() - 1) * xUnit
    maxHeight = (scn.getHeight() - 1) * yUnit

    # Initialize the ship's location
    shipX = random.randint(round(maxWidth/5),round(maxWidth - xUnit))
    shipY = random.randint(round(maxHeight/5),round(maxHeight - yUnit))

    scn.addText('<',shipX - xUnit,shipY)
    shipWin = scn.addText('=',shipX,shipY)
    scn.addText('>',shipX + xUnit,shipY)
    scn.show()

    # This is the main game loop    
    collFlag = False
    exFlag = 1
    while exFlag != -1:

        print("Current location of enemy plane: (X,Y) = (",shipX,",",shipY,") meters")

        flag = False
        while flag == False:
            try:
                ang = float(input("Launch Angle (0 - 90deg): "))
                if ang == -1:
                    break
                spd = float(input("Projectile Speed (30 - 70 [m/s]): "))
                if spd == -1:
                    break
                elif ang >= 0 and ang <= 90 and spd > 0:
                    flag = True
                else:
                    print("Not valid numbers...")
            except ValueError:
                print("Not valid numbers...")

        if ang == -1 or spd == -1:
            exFlag = -1
            continue
        
        scn.clear()
        scn.addText('<',shipX - xUnit,shipY)
        scn.addText('=',shipX,shipY)
        scn.addText('>',shipX + xUnit,shipY)

        ang = ang*PI/180 #Convert to radians 
        vx = spd*math.cos(ang)
        vy = spd*math.sin(ang)
        totT = 2*spd*math.sin(ang)/GRAV

        for x in frange(0.0,maxWidth,xUnit):
            tcur = x/vx
            ycur = vy*tcur-0.5*GRAV*tcur**2

            if ycur >= 0 and ycur <= maxHeight:
                bulletWin = scn.addText('*',x,ycur)

            collFlag = checkCollision(shipWin,bulletWin)
            if collFlag == True:
                break
                
        if collFlag == False:
            scn.show()
        else:
            scn.show()
            print("We got 'em Captain!")
            break

easterEgg = False