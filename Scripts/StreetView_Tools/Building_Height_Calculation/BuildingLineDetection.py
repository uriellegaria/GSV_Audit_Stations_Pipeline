from Utilities.Utilities import GeometryCalculations
import cv2
import numpy as np
import matplotlib.pyplot as plt

class BuildingLineDetector:

    def __init__(self):
        self.cannyThreshold1 = 50
        self.cannyThreshold2 = 150
        self.cannyAperture = 3
        self.houghDist = 50
    

    def getVerticalBottomTopPointsFromMask(self, mask, maxLines = 10):

        n = np.size(mask,0)
        m = np.size(mask,1)

        bottomPoints = []
        topPoints = []

        for i in range(0,m):
            topPointAdded = False
            bottomPointAdded = False
            for j in range(0,n):
                if(mask[j,i] == 1 and not topPointAdded):
                    topPoints.append([i, j])
                    topPointAdded = True
                elif(mask[j,i] == 0 and topPointAdded and not bottomPointAdded):
                    bottomPoints.append([i, j])
                    bottomPointAdded = True 
                    break
                elif(j == n-1 and topPointAdded and mask[j,i] == 1):
                    bottomPoints.append([i,j])
                    bottomPointAdded = True 
                    break
        
        bottomPoints = [bottomPoints[i] for i in range(0,len(bottomPoints)) if i%(len(bottomPoints)//maxLines) == 0]
        topPoints = [topPoints[i] for i in range(0,len(topPoints)) if i%(len(topPoints)//maxLines) == 0]

        return bottomPoints, topPoints
        

    def detectLineSegments(self, imageArray, initAngle, finalAngle, drawSegments = False):
        '''
        Detects line segments that fall within a constrained angle interval. 
        '''
        lineSegments = []
        grayImage = cv2.cvtColor(imageArray, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(grayImage, self.cannyThreshold1, self.cannyThreshold2, apertureSize = self.cannyAperture)
        lines = cv2.HoughLinesP(edges,1,np.pi/180,threshold=100,minLineLength=5,maxLineGap=10)
        height = np.size(imageArray,0)
        width = np.size(imageArray,1)
        xMin = 0
        xMax = width
        yMin = 0
        yMax = height
        imgCopy = imageArray.copy()
        geometryCalculator = GeometryCalculations()
        horizontalVector = np.array([1,0])

        for points in lines:
            x1,y1,x2,y2=points[0]
            #cv2.line(image,(x1,y1),(x2,y2),(0,255,0),2)

            lineSegment = LineSegment([x1, y1], [x2, y2])
            lineSegment.constrainToBoundaries(xMin, xMax, yMin, yMax)

            segmentVector = np.array([lineSegment.point2[0] - lineSegment.point1[0], lineSegment.point2[1] - lineSegment.point1[1]])
            angle = geometryCalculator.getAngleBetweenVectors(segmentVector, horizontalVector)%360

            if(angle >= initAngle and angle <= finalAngle):
                lineSegments.append(lineSegment)

                if(drawSegments):
                    cv2.line(imgCopy, (x1, y1), (x2, y2), (0, 0, 255), 2)

        if(drawSegments):
            plt.figure(figsize = (5,5))
            plt.imshow(np.array(imgCopy))
        
        return lineSegments
    

    def detectMaskLineSegments(self, image, mask, initAngle, finalAngle, *args, drawSegments = False):
        '''
        Detects all segments that pass through mask, and returns initial and final points for all 
        such segments (i hope this will help me give an estimate for the building height in the end).
        '''

        #First let's get all line segments
        lineSegments = self.detectLineSegments(image, initAngle, finalAngle)
        initialPoints = []
        finalPoints = []

        #Now we impose constrictions to the line segments so that they only pass through the mask 
        nSegments = len(lineSegments)
        for i in range(0,nSegments):
            initialPoint, finalPoint = lineSegments[i].constrainToMask(mask)
            if(not(initialPoint is None) and not(finalPoint is None)):
                initialPoints.append(initialPoint)
                finalPoints.append(finalPoint)
        

        if(drawSegments):
            
            ax = args[0]
            ax.imshow(image)
            for i in range(0,len(initialPoints)):
                initialPoint = initialPoints[i]
                finalPoint = finalPoints[i]
                ax.plot([initialPoint[0], finalPoint[0]], [initialPoint[1], finalPoint[1]], color = "#9c002c", linewidth = 2)
            
        
        return initialPoints, finalPoints



class LineSegment:
    def __init__(self, point1, point2):
        self.point1 = point1 
        self.point2 = point2

    def __eq__(self, other):
        return self.point1[0] == other.point1[0] and self.point1[1] == other.point1[1] and self.point2[0] == other.point2[0] and self.point2[1] == other.point2[1]
        

    def constrainToBoundaries(self, xMin, xMax, yMin, yMax, nPoints = 1000):
        vector1 = None
        vector2 = None
        geoCalculator = GeometryCalculations()

        if(self.point1[1] > self.point2[1]):
            vector1 = np.array(self.point2)
            vector2 = np.array(self.point1)
        else:
            vector1 = np.array(self.point1)
            vector2 = np.array(self.point2)

        alphaValues = np.linspace(0,1,nPoints)
        inferiorPoint = vector1

        #If we are already in the box we go down until we are no longer in it 
        if(geoCalculator.pointInsideBox(inferiorPoint, xMin, xMax, yMin, yMax)):
            for i in range(0,nPoints):
                alpha = alphaValues[i]
                inferiorPoint = vector1 - alpha*(vector2 - vector1)
                if(not geoCalculator.pointInsideBox(inferiorPoint, xMin, xMax, yMin, yMax)):
                    #Use the previous point
                    inferiorPoint = vector1 - alphaValues[i-1]*(vector2 - vector1)
                    break
            
        #Else we go up until we enter the box 
        else:
            for i in range(0,nPoints):
                alpha = alphaValues[i]
                inferiorPoint = vector1 + alpha*(vector2 - vector1)
                if(geoCalculator.pointInsideBox(inferiorPoint, xMin, xMax, yMin, yMax)):
                    break
            
        superiorPoint = vector2

        if(geoCalculator.pointInsideBox(superiorPoint, xMin, xMax, yMin, yMax)):
            #We go up until we go outside the box (we creative but dumb)
            for i in range(0,nPoints):
                alpha = alphaValues[i]
                superiorPoint = vector2 - alpha*(vector1 - vector2)
                if(not geoCalculator.pointInsideBox(superiorPoint, xMin, xMax, yMin, yMax)):
                    superiorPoint = vector2 - alphaValues[i-1]*(vector1 - vector2)
                    break
            
        else:
            #We go down until we go inside the box (normal + boring but not weird)
            for i in range(0,nPoints):
                alpha = alphaValues[i]
                superiorPoint = vector2 + alpha*(vector1 - vector2)
                if(geoCalculator.pointInsideBox(superiorPoint, xMin, xMax, yMin, yMax)):
                    break
            

        self.point1 = inferiorPoint
        self.point2 = superiorPoint
        self.constrainedToBox = True
    
    def constrainToMask(self, mask, nPoints = 1000):
        xMin = 0
        xMax = np.size(mask, 1)
        yMin = 0
        yMax = np.size(mask, 0)

        self.constrainToBoundaries(xMin, xMax, yMin, yMax, nPoints = nPoints)

        #Get the vectors
        vector1 = self.point1
        vector2 = self.point2

        #Since we have constrained the line to the boundaries of the image it is a matter of traversing some
        #line points and verifying that these fall inside the mask area. 
        
        alphaValues = np.linspace(0,1,nPoints)
        initialPoint = None
        finalPoint = None

        for i in range(0,nPoints):
            alpha = alphaValues[i]
            point = vector1 + alpha*(vector2 - vector1)

            index2 = int(point[0])
            index1 = int(point[1])

            if(index1 == yMax):
                index1 = index1 - 1
            
            if(index2 == xMax):
                index2 = index2 - 1

            if(mask[index1, index2] == 1 and initialPoint is None):
                initialPoint = point
            
            if(mask[index1, index2] == 0 and (finalPoint is None) and not(initialPoint is None)):
                finalPoint = point
                break
        
        return initialPoint, finalPoint
    
    def getPoints(self):
        return self.point1, self.point2