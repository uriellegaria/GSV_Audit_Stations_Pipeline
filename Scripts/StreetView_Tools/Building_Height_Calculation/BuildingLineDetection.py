
import cv2
import numpy as np
import matplotlib.pyplot as plt
from .BHUtilities import GeometryCalculations


class BuildingLineDetectorPrimitive:


    def detectLineSegments(self, imageArray, thresholdCanny1 = 50, thresholdCanny2 = 150, apertureSize = 3, rho = 1, thresholdHough = 50, minLineLength = 50, maxLineGap = 10, draw = False, drawImageWidth = 7, drawImageHeight = 7):

        grayImage = cv2.cvtColor(imageArray, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(grayImage, thresholdCanny1, thresholdCanny2, apertureSize = apertureSize)
        lines = cv2.HoughLinesP(edges, rho, np.pi/180, threshold = thresholdHough, minLineLength = minLineLength, maxLineGap = maxLineGap)

        segments = []

        drawImage = np.copy(imageArray)
        imageHeight = np.size(imageArray,0)

        if(lines is not None):
            for line in lines:
                for x1, y1, x2, y2 in line:
                    segments.append([(x1, imageHeight - 1 - y1), (x2, imageHeight - 1 - y2)])
                    if(draw):
                        cv2.line(drawImage, (x1, y1), (x2, y2), (0, 255, 0), 2)
        

        if(draw):
            plt.figure(figsize = (drawImageWidth, drawImageHeight))
            plt.imshow(drawImage)
        
        return segments


class LineSegmentPostProcessor:



    def lineSegmentPostProcessing(self, image, segments, buildingMask, vanishingPoint, thresholdAngle= 10, thresholdMerge = 2, draw = False, imageDrawWidth = 7, imageDrawHeight = 7):

        #Get segments inside mask
        filteredSegments = self.filterSegmentsInsideMask(segments, buildingMask)

        #Stay with segments where angle to the vertical is less than threshold
        angleFiltered = self.filterByAngleToVanishing(filteredSegments, vanishingPoint, thresholdAngle = thresholdAngle)

        #Merge close segments
        mergedSegments = self.mergeCloseSegments(angleFiltered, thresholdMerge=thresholdMerge)

        #Extend lines
        extendedLines = self.extendLines(mergedSegments, buildingMask)

        imageHeight = np.size(image, 0)

        if(draw):
            drawImage = np.copy(image)
            for i in range(0,len(extendedLines)):
                segment = extendedLines[i]
                cv2.line(drawImage, (segment[0][0], imageHeight - 1 - segment[0][1]), (segment[1][0], imageHeight - 1 - segment[1][1]), (0, 255, 0), 2)
            

            plt.figure(figsize  = (imageDrawWidth, imageDrawHeight))
            plt.imshow(drawImage)
        
        return extendedLines
        

    def mergeCloseSegments(self, segments, thresholdMerge = 10):
        mergedSegments = []
        geometryCalculations = GeometryCalculations()
        nSegments = len(segments)
        discards = np.zeros(nSegments)
        for i in range(0,nSegments):
            segment1 = segments[i]
            for j in range(i+1,nSegments):
                segment2 = segments[j]
                dst = geometryCalculations.getDistanceBetweenSegments(segment1, segment2)
                if(discards[j] == 0 and discards[i] == 0 and dst < thresholdMerge):
                    discards[j] = 1
        

        for i in range(0,nSegments):
            if(discards[i] == 0):
                mergedSegments.append(segments[i])
        
        return mergedSegments

    def filterByAngleToVanishing(self, segments, vanishingPoint, thresholdAngle = 5):

        nSegments = len(segments)
        filteredSegments = []
        vanishingPoint = np.array(vanishingPoint)
        geometryCalculator = GeometryCalculations()

        for i in range(0,len(segments)):
            segment = segments[i]
            middlePoint = np.array(self.getMiddlePoint(segment))
            verticalSegment = vanishingPoint - middlePoint
            differenceSegment = np.array(segment[1]) - np.array(segment[0])
            angle = np.min([geometryCalculator.angleBetweenVectors(np.array(verticalSegment), np.array(segment[1]) - np.array(segment[0])), geometryCalculator.angleBetweenVectors(np.array(verticalSegment), np.array(segment[0]) - np.array(segment[1]))])

            if(angle < thresholdAngle):
                #Here i have to do some rotaiton operation around the middle point, i need to figure out the
                #equation first in my notebook
                filteredSegments.append(segment)
        
        return filteredSegments





    def getMiddlePoint(self, segment):
        xMiddle = (segment[0][0] + segment[1][0])/2.0
        yMiddle = (segment[0][1] + segment[1][1])/2.0

        return (xMiddle, yMiddle)
    

    def filterSegmentsInsideMask(self, segments, buildingMask):

        imageHeight = np.size(buildingMask, 0)
        filteredSegments = []

        for i in range(0,len(segments)):
            segment = segments[i]
            middlePoint= self.getMiddlePoint(segment)
            point1  = segment[0]
            point2 = segment[1]
            points = [point1, point2, middlePoint]

            keepSegment = True

            for j in range(0,len(points)):
                point = points[j]
                index2 = int(point[0])
                index1 = imageHeight - 1 - int(point[1])

                if(buildingMask[index1, index2] == 0):

                    keepSegment = False
            
            if(keepSegment):
                filteredSegments.append(segment)
    

        return filteredSegments
    


    def extendLines(self, lines, buildingMask):
        #Define some functions

        nLines = len(lines)
        extendedLines = []
        
        for i in range(0, nLines):
            line = lines[i]
            point1 = line[0]
            point2 = line[1]
            extendedPoint1 = self.extendPoint(point1, point2, buildingMask)
            extendedPoint2 = self.extendPoint(point2, point1, buildingMask)
            if(extendedPoint1[1] > extendedPoint2[1]):
                extendedLines.append([extendedPoint2, extendedPoint1])
            
            else:
                extendedLines.append([extendedPoint1, extendedPoint2])
        
        return extendedLines


    

    def extendPoint(self, point1, point2, buildingMask):
        isWithinBounds = lambda x, mask: 0 <= x[0] <np.size(mask,1) and 0 <= x[1] < np.size(mask,0)
        isBuildingPixel = lambda x, mask: mask[np.size(mask,0) - 1 - int(x[1]), int(x[0])] == 1

        x1,y1 = point1
        x2,y2 = point2
        direction = np.array([x2 - x1, y2 - y1])
        normDirection = direction/np.linalg.norm(direction)

        currentPoint = np.array(point2)
        while (isWithinBounds(currentPoint, buildingMask) and isBuildingPixel(currentPoint, buildingMask)):
            currentPoint = currentPoint + normDirection
        
        if(not isWithinBounds(currentPoint, buildingMask)):
            currentPoint = np.clip(currentPoint, [0, 0], [np.size(buildingMask,1) - 1, np.size(buildingMask, 0) - 1])

        return tuple(currentPoint.astype(int))







    











