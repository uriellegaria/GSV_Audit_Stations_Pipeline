from lu_vp_detect import VPDetection
import numpy as np
import sys
from Utilities.Utilities import RandomColorGenerator
from PIL import Image
import matplotlib.pyplot as plt
from Utilities.Utilities import GeometryCalculations
from .BuildingSegmentation import BuildingSegmentator
from .BuildingLineDetection import BuildingLineDetector


class AutomaticHeightCalculation:

    def __init__(self, modelPath):
        self.segmentator = BuildingSegmentator(modelPath)
        self.maxRealisticHeight = 100

    def computeHeightsWithMasks(self, img):
        vpDetector = VPDetector(img)
        vanishingPoints = None

        try:
            vanishingPoints = vpDetector.computeVanishingPoints()
        except:
            return [], []

        
        heightCalculator = HeightCalculator()

        projectionMatrix = heightCalculator.constructProjectionMatrix(vanishingPoints[0], vanishingPoints[1], vanishingPoints[2])

        masks, segmentedImages = self.segmentator.segmentBuildingsInImage(img)
        lineDetector = BuildingLineDetector()
        heightValues = []
        threshold = 0.8

        for i in range(0,len(segmentedImages)):
            mask = masks[i]
            initialPoints, finalPoints = lineDetector.getVerticalBottomTopPointsFromMask(mask, maxLines = 10)
            maskHeights = []
            for j in range(0,len(initialPoints)):
                initialPoint = initialPoints[j]
                finalPoint = finalPoints[j]
                height = heightCalculator.obtainHeight(initialPoint, finalPoint)
                maskHeights.append(height)
            
            meanHeight = np.mean(maskHeights)
            finalHeight = 0
            nPointsConsidered = 0

            for j in range(0,len(maskHeights)):
                error = np.abs((maskHeights[j] - meanHeight)/meanHeight)
                if(error < threshold and maskHeights[j] <= self.maxRealisticHeight):
                    finalHeight = finalHeight +maskHeights[j]
                    nPointsConsidered = nPointsConsidered + 1
            if(nPointsConsidered > 0):
                finalHeight = finalHeight / nPointsConsidered
            else:
                finalHeight = float('nan')

            heightValues.append(finalHeight)
        
        return segmentedImages, heightValues
        

        

        


        



        #segment = None
        #if(drawDistanceLine):
            #segment = buildingSegmentation.getBuildingSegment(self.img, drawBuildingLine = True)
        #else:
            #segment = buildingSegmentation.getBuildingSegment(self.img)
        #pointBottom = heightCalculator.getProjectivePointInImage(list(segment.point1))
        #pointTop = heightCalculator.getProjectivePointInImage(list(segment.point2))
        
        #height = heightCalculator.obtainHeight(pointBottom, pointTop)

        #return height

class VPDetector:

    '''
    Class used to compute the vanishing points of an image in the x, y, and z directions. 
    '''


    def __init__(self, image, midPrincipal = True, fov = 90, lengthThresh = 40):
        self.image = image
        #By default it is assumed that the principal point is in the middle of the image 
        if(midPrincipal):
            self.setPrincipalMidPoint()
        
        self.fov = fov
        self.imageWidth = np.size(image, 1)
        self.imageHeight = np.size(image, 0)

        #Initialize the vanishing point detector
        self.vanishingDetector = VPDetection(lengthThresh, (self.xPrincipal, self.yPrincipal), self.approximateFocalLength(self.fov), None)


    def setPrincipalMidPoint(self):
        xMid = int(np.size(self.image,1)/2)
        yMid = int(np.size(self.image,0)/2)
        self.setPrincipalPoint(xMid, yMid)
    

    def setPrincipalPoint(self, xPrincipal, yPrincipal):
        self.xPrincipal = xPrincipal
        self.yPrincipal = yPrincipal


    def approximateFocalLength(self, fov):
        f = (1/np.tan(np.deg2rad(fov/2)))*(self.imageWidth/2)
        return f

    def computeVanishingPoints(self):
        self.vanishingPoints = self.vanishingDetector.find_vps(self.image)
        #I would like to visualize the vanishing points
        self.twoDimPoints = self.vanishingDetector.vps_2D
        #Let's order the points and return them in projective form

        #I think we can order the points using the angle between them 
        #I should probably not do this manually, but they are just three points so. 
        point1 = np.array(self.twoDimPoints[0])
        point2 = np.array(self.twoDimPoints[1])
        point3 = np.array(self.twoDimPoints[2])

        geometryCalculations = GeometryCalculations()
        horizontalVector = np.array([1,0])
        angle12 = np.abs(geometryCalculations.getAngleBetweenVectors(horizontalVector, point2 - point1)%180)
        angle23 = np.abs(geometryCalculations.getAngleBetweenVectors(horizontalVector, point3 - point2)%180)
        angle13 = np.abs(geometryCalculations.getAngleBetweenVectors(horizontalVector, point3 - point1)%180)

        angles = [angle12, angle23, angle13]
        minAngleIndex = np.argmin(angles)
        orderedPoints = []

        if(minAngleIndex == 0):
            if(point1[0] < point2[0]):
                orderedPoints = [point1, point2, point3]
            else:
                orderedPoints = [point2, point1, point3]
        elif(minAngleIndex == 1):
            if(point2[0] < point3[0]):
                orderedPoints = [point2, point3, point1]
            else:
                orderedPoints = [point3, point2, point1]
        
        elif(minAngleIndex == 2):
            if(point1[0] < point3[0]):
                orderedPoints = [point1, point3, point2]
            else:
                orderedPoints = [point3, point1, point2]

        #Add a 1 at the end of the vector to use projective geometry.
        for i in range(0,len(orderedPoints)):
            orderedPoints[i] = list(orderedPoints[i])
            orderedPoints[i].append(1)
        
        self.orderedPoints = orderedPoints

    
        return orderedPoints


    def drawImageAndPoints(self, image, width, height, pointsize = 2):
        plt.figure(figsize = (width, height))
        plt.imshow(image)

        nPoints = len(self.twoDimPoints)
        randomColorGenerator = RandomColorGenerator()
        randomColors = randomColorGenerator.getRandomColors(nPoints, separation = 0.4)

        #Let's also draw the vanishing line
        vanishingLineColor = "#0400db"
        vanishingX = self.orderedPoints[0]
        vanishingY = self.orderedPoints[1]
        plt.plot([vanishingX[0], vanishingY[0]], [vanishingX[1], vanishingY[1]], color = vanishingLineColor, marker = 'none', linewidth = 2)
        
        for i in range(0,nPoints):
            point = self.twoDimPoints[i]
            plt.plot(point[0], point[1], color = randomColors[i], marker = 'o')

import cv2

class HeightCalculator:
    
    def __init__(self):
        self.googleCarHeight = 2.5
    
    
    def setProjectionMatrix(self, P):
        self.P = P



    def vpCalculationWithPitch(self, w, h, pitch, fov = 90):

        v = np.array([w / 2, 0.0, 1.0])  # pitch will influence the second element of v, v[1]
        vline = np.array([0.0, 1.0, 0.0])  # pitch will influence the third element of vline, vline[2]
        focalLength = self.getFocalLength(fov, w)

        if pitch == 0:
            v[:] = [0, -1, 0]
            vline[:] = [0, 1, h / 2]
        else:
            v[1] = h / 2 - (focalLength / np.tan(np.deg2rad(pitch)))
            vline[2] = (h / 2 + focalLength * np.tan(np.deg2rad(pitch)))

        return v, vline


    def approximateHeightWithPitch(self, width, height, pitch, b, t, fov = 90):
        v, vline = self.vpCalculationWithPitch(width, height, pitch, fov)

        if v[2] == 0:  # a special case
            v[0] = 320    
            v[1] = -9999999

        p4 = vline/np.linalg.norm(vline)
        alpha = -1/(np.dot(p4, v)*self.googleCarHeight)
        p3 = alpha*v
        zx = -np.linalg.norm(np.cross(b, t)) / (np.dot(p4, b) * np.linalg.norm(np.cross(p3, t)))
        zx = abs(zx)  # vanishing line can have two directions

        return zx
        
        

    def getFocalLength(self, fov, imageWidth):
        f = (1/np.tan(np.deg2rad(fov/2)))*(imageWidth/2)
        return f
    
    def constructProjectionMatrix(self, vanishingX, vanishingY, vanishingZ):
        p1 = vanishingX
        p2 = vanishingY
        p4 = self.getNormalizedLineVector(p1, p2)
        p4 = list(p4)
        self.computeAlpha(p1, p2, p4, vanishingZ)
        #self.computeAlpha2(p4, vanishingZ)
        p3 = np.array(vanishingZ)*self.alpha
        p3 = list(p3)
        self.P = np.array([p1,p2,p3,p4]).transpose()
        
        
        return self.P
            
        

    def getNormalizedLineVector(self, x1, x2):
        lineVec = np.cross(x1, x2)
        normVec = lineVec/np.linalg.norm(lineVec)

        #print(normVec[0]*x1[0] +normVec[1]*x1[1]+normVec[2]*x1[2])
        #print(normVec[0]*x2[0] +normVec[1]*x2[1]+normVec[2]*x2[2])

        return normVec
        

    def computeAlpha2(self, p4, vanishingZ):
        alpha = -(1/self.googleCarHeight)*(1/np.dot(p4, vanishingZ))
        self.alpha = alpha
        return alpha
        
    def computeAlpha(self, p1, p2, p4, x3):
        matrix = np.array([p1, p2, p4])
        determinant = np.linalg.det(matrix)
        #print("Determinant "+str(determinant))
        matrix2 = np.array([p1, p2, x3])
        determinant2 = np.linalg.det(matrix2)
        #print("Determinant 2 "+str(determinant2))
        zc = self.googleCarHeight*determinant2
        #zc = self.googleCarHeight
        self.alpha = -determinant/zc
        #print(self.alpha)
    
    def obtainHeight(self, b, t):

        if(len(b) == 2):
            b = list(b)
            b.append(1)
        
        if(len(t) == 2):
            t = list(t)
            t.append(1)
        
        b = np.array(b)
        t = np.array(t)

        crossBT = np.cross(b, t)
        #crossBT = self.getVectorOnProjectivePlane(crossBT)
        
        normCrossBT = np.sqrt(crossBT[0]**2 + crossBT[1]**2 + crossBT[2]**2)
        #normCrossBT = np.sqrt(crossBT[0]**2 + crossBT[1]**2)
        

        crossVT = np.cross(self.P[:,2], t)
        #crossVT = self.getVectorOnProjectivePlane(crossVT)

        #normCrossVT = np.sqrt(crossVT[0]**2 + crossVT[1]**2)
        normCrossVT = np.sqrt(crossVT[0]**2 + crossVT[1]**2 + crossVT[2]**2)

        #p3 = self.P[:,3]
        #dotIB = p3[0]*b[0] + p3[1]*b[1]
        dotIB = np.dot(self.P[:,3], b)
        
        height = -normCrossBT/(dotIB*normCrossVT)
        
        return np.abs(height)
    
    def getVectorOnProjectivePlane(self, vector):

        return np.array(vector)/vector[-1]
        
    #def clickEvent(self, event, x, y, flags, params):

        #if (event==cv2.EVENT_RBUTTONDOWN or event == cv2.EVENT_LBUTTONDOWN):
            
            #self.points.append([x,y])
            #cv2.circle(self.backgroundImage, (x,y), radius=4, color=(0, 0, 255), thickness=-1)
    
    #def retrievePointByEye(self, backgroundImage):
        #self.points = []
        #self.backgroundImage = backgroundImage.copy()
        #self.imageWidth = np.size(self.backgroundImage,0)
        #self.imageHeight = np.size(self.backgroundImage,1)
        #self.done = True
        
        #cv2.namedWindow('image')
        #cv2.setMouseCallback('image',self.clickEvent)
        
        #while(1):
            #cv2.imshow('image',self.backgroundImage)
            #if (cv2.waitKey(20) & 0xFF == 27):
                #print("Here")
                #break
        
        #cv2.destroyAllWindows()
        #cv2.waitKey(1)
        #self.backgroundImage = backgroundImage
        
        #return self.points
        
    #def getProjectivePointInImage(self, point):
        #pointCopy = point.copy()
        #pointList = list(pointCopy)
        #pointList.append(1)
        
        #return pointList

    #def flipYCoord(self, point, imageHeight):
        #newPoint = point.copy()
        #newPoint[1] = imageHeight - point[1]
        #return newPoint