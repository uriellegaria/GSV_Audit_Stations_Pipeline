

import math
import numpy as np
from lu_vp_detect import VPDetection
from .BHUtilities import CameraOperations
import matplotlib.pyplot as plt
from .BHUtilities import GeometryCalculations
from .BHUtilities import RandomColorGenerator

class VanishingPointCalculator:


    def getGSVVPLine(self, image, pitch, fov = 90):

        '''
        Computes the vertical vanishing point and line joining the horizontal points using the pitch angle.
        The method assumes a perfect sideview of the building. 
        '''
        cameraOperations = CameraOperations()
        imageWidth = np.size(image, 1)
        imageHeight = np.size(image, 0)


        focalLength = cameraOperations.approximateFocalLength(imageWidth, fov)

        pitchRad = np.deg2rad(pitch)
    
        # Calculate the vertical vanishing point y-coordinate
        y0 = imageHeight / 2
        yVp = y0 - focalLength * np.tan(pitchRad)
    
        # Vanishing point (x, y) assuming the vanishing point is vertically aligned with the principal point
        vanishingPoint = (0, yVp)
    
        a = 0
        b = 1
        c = -yVp
    
        vanishingLineCoefficients = (a, b, c)
    
        return vanishingPoint, vanishingLineCoefficients



    def getVerticalVanishingPointHeuristic(self, vanishingPoints2D):
    
        #Get angles between the different lines joining vanishing points
        lineSegments = [np.array(vanishingPoints2D[1]) - np.array(vanishingPoints2D[0]), 
                        np.array(vanishingPoints2D[2]) - np.array(vanishingPoints2D[0]), 
                        np.array(vanishingPoints2D[2]) - np.array(vanishingPoints2D[1])]

        #normalize segments
        lineSegments = [x/np.linalg.norm(x) for x in lineSegments]

        dotProducts = [np.abs(np.dot(x, [1,0])) for x in lineSegments]

        maxIndex = np.argmax(dotProducts)

        #The order in which the points are returned are horizontalPoint1, horizontalPoint2, verticalVanishingPoint

        if(maxIndex == 0):
            return [vanishingPoints2D[0], vanishingPoints2D[1], vanishingPoints2D[2]]
        elif(maxIndex == 1):
            return [vanishingPoints2D[0], vanishingPoints2D[2], vanishingPoints2D[1]]
        elif(maxIndex == 2):
            return [vanishingPoints2D[1], vanishingPoints2D[2], vanishingPoints2D[0]]


    def getVanishingPointsLu(self, image, fov = 90, ordered = True, draw = False, flipYAxis = True, lengthThresh = 50, focalLength = -1):
        imageWidth = np.size(image,1)
        imageHeight = np.size(image,0)
        
        cameraOperations = CameraOperations()
        if(focalLength == -1):
            focalLength = cameraOperations.approximateFocalLength(imageWidth, fov)

        vanishingPointDetector = VPDetection(length_thresh = lengthThresh, principal_point = (imageWidth/2, imageHeight/2), focal_length =focalLength, seed = 20)
        vanishingPoints = vanishingPointDetector.find_vps(image)

        #Project them to 2d space
        projectedPoints = []
        for i in range(0, np.size(vanishingPoints,0)):
            vanishingPoint = vanishingPoints[i,:]
            imagePoint = cameraOperations.projectPointToImageMidPrincipal(vanishingPoint, imageWidth, imageHeight)
            projectedPoints.append(imagePoint)
        
        if(ordered):
            projectedPoints = self.getVerticalVanishingPointHeuristic(projectedPoints)

        if(flipYAxis):
            for i in range(0,len(projectedPoints)):
                projectedPoints[i][1] = imageHeight - projectedPoints[i][1]
        
        if(draw):
            pointsToDraw = self.getVerticalVanishingPointHeuristic(projectedPoints)
            self.drawVanishingPointsLu(pointsToDraw, image)

        return vanishingPoints, projectedPoints
    


    def drawVanishingPointsLu(self, vanishingPoints, image, pointSize = 4, lineSize = 2, width = 7, height = 7, colorLine = "#9d4dff", flipY = True):

        horizontalPoint1 = vanishingPoints[0]
        horizontalPoint2 = vanishingPoints[1]
        verticalPoint = vanishingPoints[2]

        plt.figure(figsize = (width, height))
        plt.imshow(image)
        if(flipY):
            plt.imshow(np.flipud(image)/255.0)
            plt.gca().invert_yaxis()
        else:
            plt.imshow(image)
        

        plt.plot([horizontalPoint1[0], horizontalPoint2[0]], [horizontalPoint1[1], horizontalPoint2[1]], linewidth = lineSize, color = colorLine)
        colorGenerator = RandomColorGenerator()
        colors = colorGenerator.getRandomColors(2)

        #Plot the horizontal vanishing points
        plt.plot(horizontalPoint1[0], horizontalPoint1[1], marker = "o", color = colors[0], markersize = pointSize)
        plt.plot(horizontalPoint2[0], horizontalPoint2[1], marker = "o", color = colors[0], markersize = pointSize)

        #Plot the vertical vanishing point
        plt.plot(verticalPoint[0], verticalPoint[1], marker = "o", color = colors[1], markersize = pointSize)



