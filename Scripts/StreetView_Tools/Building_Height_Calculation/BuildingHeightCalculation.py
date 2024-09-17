from .BHUtilities import CameraOperations
import numpy as np
import sys
from PIL import Image
import matplotlib.pyplot as plt
from .BHUtilities import GeometryCalculations
from .BuildingSegmentation import BuildingSegmentator
from .BHUtilities import GeometryCalculations
from enum import Enum
from .VanishingPointsCalculation import VanishingPointCalculator
from .BuildingLineDetection import BuildingLineDetectorPrimitive
from .BuildingLineDetection import LineSegmentPostProcessor




class ApproximationType(Enum):
    MEAN = 0
    MAX_HEIGHT = 1
    NO_APPROXIMATION = 2



class AutomaticHeightCalculation:

    def __init__(self, modelPath):
        #Instantiate the Building segmentator
        self.segmentator = BuildingSegmentator(modelPath)
        
    

    def computeHeightsWithMask(self, img, approximationType = ApproximationType.MEAN, focalLength = 300, drawVPImage = False, drawLinesImage = False, fov = 90, lengthThresh = 40, threshold1Canny = 50, thresholdCanny2 = 150, apertureSize = 3, rho = 1, thresholdHough = 50, thresholdAngle = 5, thresholdMerge = 40):
        #Detect the vanishing points
        vpDetector = VanishingPointCalculator()
        vanishingPoints = None
        projectedPoints = None

        try:
            vanishingPoints, projectedPoints = vpDetector.getVanishingPointsLu(img, draw = drawVPImage, focalLength = focalLength,  lengthThresh = lengthThresh, fov = fov)
        except:
            return [], []

        #Segment buildings in the provided image
        masks, segmentedImages = self.segmentator.segmentBuildingsInImage(img)
        heightValues = []
        nDetections = len(masks)
        lineDetector = BuildingLineDetectorPrimitive()
        lineProcessor = LineSegmentPostProcessor()

        for i in range(0,nDetections):
            mask = masks[i]
            lines = lineDetector.detectLineSegments(img, thresholdCanny1 = threshold1Canny, thresholdCanny2 = thresholdCanny2, apertureSize = apertureSize, rho = rho, thresholdHough = thresholdHough)
            processedLines = lineProcessor.lineSegmentPostProcessing(img, lines, mask, projectedPoints[2], draw = drawLinesImage, thresholdAngle = thresholdAngle, thresholdMerge = thresholdMerge)
            heightValue = self.computeLineHeights(processedLines, projectedPoints, approximationType)
            heightValues.append(heightValue)
        
        return segmentedImages, heightValues
    

    def applyLinearCorrection(self, heights, coeffs):
        b0 = coeffs[0]
        b1 = coeffs[1]

        correctedHeights = [b0 + b1*x for x in heights]

        return correctedHeights

    


    def computeLineHeights(self, lines, vanishingPoints, approximationType):
        '''
        Vanishing points are assumed to be ordered (horizontal 1, horizontal 1, vertical)
        In the lines array members are supposed to be of the form (bottomPointTuple, topPointTuple), where bottomPointTuple denotes the coordinates of the lower point in the line and 
        topPointTuple denotes the upper point in the line. 
        '''
        heightCalculator = HeightCalculator()

        if(approximationType == ApproximationType.MEAN):
            #Get the mean of heights over all line heights
            nLines = len(lines)
            meanHeight = 0
            for i in range(0,nLines):
                line = lines[i]
                height = heightCalculator.computeHeightMethod2(vanishingPoints[0], vanishingPoints[1], vanishingPoints[2], line[0], line[1])
                if(not height is None):
                    meanHeight = meanHeight + (1/nLines)*heightCalculator.computeHeightMethod2(vanishingPoints[0], vanishingPoints[1], vanishingPoints[2], line[0], line[1])
            
            return meanHeight
        
        elif(approximationType == ApproximationType.MAX_HEIGHT):
            nLines = len(lines)
            maxHeight = float('-inf')

            for i in range(0,nLines):
                line = lines[i]
                height = heightCalculator.computeHeightMethod2(vanishingPoints[0], vanishingPoints[1], vanishingPoints[2], line[0], line[1])
                if(not height is None and height > maxHeight):
                    maxHeight = height
            
            return maxHeight
        
        elif(approximationType == ApproximationType.NO_APPROXIMATION):
            #For no approximation we need to convey the information of the lines too
            #We will return 5-tuples of the form (x1, y1, x2, y2, height)
            allHeights = []
            nLines = len(lines)
            for i in range(0,nLines):
                line = lines[i]
                height = heightCalculator.computeHeightMethod2(vanishingPoints[0], vanishingPoints[1], vanishingPoints[2], line[0], line[1])
                x1 = line[0][0]
                y1 = line[0][1]
                x2 = line[1][0]
                y2 = line[1][1]

                if(not height is None):
                    allHeights.append((x1,y1,x2,y2,height))
            
            return allHeights











            












#class AutomaticHeightCalculation:

   # def __init__(self, modelPath):
        #self.segmentator = BuildingSegmentator(modelPath)
        #self.maxRealisticHeight = 100

    #def computeHeightsWithMasks(self, img):
        #vpDetector = VPDetector(img)
        #vanishingPoints = None

        #try:
            #vanishingPoints = vpDetector.computeVanishingPoints()
        #except:
            #return [], []

        
        #heightCalculator = HeightCalculator()

        #projectionMatrix = heightCalculator.constructProjectionMatrix(vanishingPoints[0], vanishingPoints[1], vanishingPoints[2])

        #masks, segmentedImages = self.segmentator.segmentBuildingsInImage(img)
        #lineDetector = BuildingLineDetector()
        #heightValues = []
        #threshold = 0.8

        #for i in range(0,len(segmentedImages)):
            #mask = masks[i]
            #initialPoints, finalPoints = lineDetector.getVerticalBottomTopPointsFromMask(mask, maxLines = 10)
            #maskHeights = []
            #for j in range(0,len(initialPoints)):
                #initialPoint = initialPoints[j]
                #finalPoint = finalPoints[j]
                #height = heightCalculator.obtainHeight(initialPoint, finalPoint)
                #maskHeights.append(height)
            
            #meanHeight = np.mean(maskHeights)
            #finalHeight = 0
            #nPointsConsidered = 0

            #for j in range(0,len(maskHeights)):
                #error = np.abs((maskHeights[j] - meanHeight)/meanHeight)
                #if(error < threshold and maskHeights[j] <= self.maxRealisticHeight):
                    #finalHeight = finalHeight +maskHeights[j]
                    #nPointsConsidered = nPointsConsidered + 1
            #if(nPointsConsidered > 0):
                #finalHeight = finalHeight / nPointsConsidered
            #else:
                #finalHeight = float('nan')

            #heightValues.append(finalHeight)
        
        #return segmentedImages, heightValues
        





class HeightCalculator:
    

    def computeHeight(self, horizontal1, horizontal2, vertical1, ptBottom, ptTop, zc = 2.5):

        '''
        Compute the height given 3 vanishing points horizontal1, horizontal2, vertical1, and two points in the image:

        a point at the bottom ptBottom, and a point at the top ptTop
        '''

        cameraOperations = CameraOperations()
        v1 = cameraOperations.getHomogeneousPoint(horizontal1)
        v2 = cameraOperations.getHomogeneousPoint(horizontal2)
        v3 = cameraOperations.getHomogeneousPoint(vertical1)
        x1 = cameraOperations.getHomogeneousPoint(ptBottom)
        x2 = cameraOperations.getHomogeneousPoint(ptTop)

        vLine = np.cross(v1, v2)
        p4 = vLine/np.linalg.norm(vLine)
        zc = zc*np.linalg.det([v1,v2,v3])
        alpha = -np.linalg.det([v1, v2, p4])/zc
        p3 = alpha*v3
        height = -np.linalg.norm(np.cross(x1,x2))/ (np.dot(p4, x1) * np.linalg.norm(np.cross(p3, x2)))
        height = np.abs(height)
        return height
    

    def computeHeightGSVApproximation2(self, vLine, vertical1, ptBottom, ptTop, zc = 2.5):
        geometryCalculator = GeometryCalculations()
        verticalLine = geometryCalculator.getLineCoefficients(ptBottom, ptTop)
        pC = geometryCalculator.getIntersection(vLine, verticalLine)
        if(not pC is None):
            pC = np.array(pC)

            #Distance between vanishing point and pC
            distAC = np.linalg.norm(np.array(vertical1) - pC)
            #Distance between the vanishing point and the top of the building
            distAB = np.linalg.norm(np.array(vertical1) - np.array(ptTop))
            #Distance between the top and bottom points of the building
            distBD = np.linalg.norm(np.array(ptTop) - np.array(ptBottom))
            #Distance between the bottom point and pC
            distCD = np.linalg.norm(pC - np.array(ptBottom))
        
            height = ((distBD*distAC)/(distCD*distAB))*zc

            return height
        
        else:
            return None
    

    def computeHeightMethod2(self, horizontal1, horizontal2, vertical1, ptBottom, ptTop, zc = 2.5):
        '''
        Method that computes the height using cross ratios. In principle the result should be the same as in 
        computeHeight
        '''

        geometryCalculator = GeometryCalculations()
        vanishingLineCoeffs = geometryCalculator.getLineCoefficients(horizontal1, horizontal2)
        verticalLineCoeffs = geometryCalculator.getLineCoefficients(ptBottom, ptTop)
        pC = geometryCalculator.getIntersection(vanishingLineCoeffs, verticalLineCoeffs)
        if(not pC is None):
            pC = np.array(pC)

            #Distance between vanishing point and pC
            distAC = np.linalg.norm(np.array(vertical1) - pC)
            #Distance between the vanishing point and the top of the building
            distAB = np.linalg.norm(np.array(vertical1) - np.array(ptTop))
            #Distance between the top and bottom points of the building
            distBD = np.linalg.norm(np.array(ptTop) - np.array(ptBottom))
            #Distance between the bottom point and pC
            distCD = np.linalg.norm(pC - np.array(ptBottom))
        
            height = ((distBD*distAC)/(distCD*distAB))*zc

            return height
        
        else:
            return None