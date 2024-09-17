import math
import numpy as np
import random 

class CameraOperations:



    def approximateFocalLength(self, imageWidth, fov):
        '''
        Approximates focal length from FOV
        '''
        fovRadians = math.radians(fov)
        focalLength = imageWidth/(2*math.tan(fovRadians/2))

        return focalLength
    

    def projectPointToImageMidPrincipal(self, point, imageWidth, imageHeight):

        if (point[2] != 0):
            x = (point[0]/point[2])*(imageWidth/2) + (imageWidth/2)
            y = (point[1]/point[2])*(imageHeight/2) + (imageHeight/2)

            return [x, y]
        

        else:
            return None
    

    def getHomogeneousPoint(self, imagePoint):
        '''
        imagePoint is assumed to contain 2 coordinates
        '''

        homogeneousPoint = np.array([imagePoint[0], imagePoint[1], 1])
        
        return homogeneousPoint


class GeometryCalculations:
    '''
    Class that encapsulates some special geometrical calculations
    '''
    def __init__(self):
        self.earthRadius = 6378.14 *10**3


    def getOrthogonalityMeasure(self, vector1, vector2):
        # Ensure the inputs are numpy arrays
        vector1 = np.array(vector1)
        vector2 = np.array(vector2)

        # Calculate the dot product of the two vectors
        dotProduct = np.dot(vector1, vector2)
        
        # Calculate the magnitudes (norms) of the two vectors
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)

        # Ensure norms are not zero to avoid division by zero
        if norm1 == 0 or norm2 == 0:
            raise ValueError("Input vectors must be non-zero.")

        # Calculate the cosine of the angle
        cosAngle = dotProduct / (norm1 * norm2)

        # Orthogonality measure is 1 - absolute value of cosAngle
        orthogonalityMeasure = 1 - abs(cosAngle)

        return orthogonalityMeasure
    

    def angleBetweenVectors(self, v1, v2):
        # Normalize the vectors
        v1Norm = v1 / np.linalg.norm(v1)
        v2Norm = v2 / np.linalg.norm(v2)
    
        # Calculate the dot product
        dotProduct = np.dot(v1Norm, v2Norm)
    
        # Clamp the dot product to avoid numerical errors outside the range [-1, 1]
        dotProduct = np.clip(dotProduct, -1.0, 1.0)
    
        # Calculate the angle in radians
        angleRad = np.arccos(dotProduct)
    
        # Convert the angle to degrees
        angleDeg = np.degrees(angleRad)
    
        return angleDeg

    def pointInsideBox(self, point, xMin, xMax, yMin, yMax):
        xCoord = point[0]
        yCoord = point[1]

        if(xCoord >= xMin and xCoord <= xMax and yCoord >= yMin and yCoord <= yMax):
            return True
        else:
            return False
    
    def getEuclideanDistance(self, point1, point2):
        return np.linalg.norm(np.array(point2) - np.array(point1))
    
    def getDistanceBetweenCoordinates(self, latitude1, longitude1, latitude2, longitude2):
        #Earth radius
        R = 6371
        latitude1Radians = math.radians(latitude1)
        longitude1Radians = math.radians(longitude1)
        latitude2Radians = math.radians(latitude2)
        longitude2Radians = math.radians(longitude2)
        
        dst = 2*R*math.asin(np.sqrt((1 - np.cos(latitude2Radians - latitude1Radians) + np.cos(latitude1Radians)*np.cos(latitude2Radians)*(1 - np.cos(longitude2Radians - longitude1Radians)))/2))

        return dst*10**3
    
    def getBearing(self, latitude1, longitude1, latitude2, longitude2):
        lat1 = math.radians(latitude1)
        lat2 = math.radians(latitude2)

        diffLong = math.radians(longitude2 - longitude1)

        x = math.sin(diffLong) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)* math.cos(lat2)*math.cos(diffLong))

        initialBearing = math.atan2(x, y)


        initialBearing = math.degrees(initialBearing)
        compassBearing = (initialBearing + 360) % 360

        return compassBearing


    def getLineCoefficients(self, point1, point2):
        x1 = point1[0]
        y1 = point1[1]
        x2 = point2[0]
        y2 = point2[1]

        a = y2 - y1
        b = x1 - x2
        c = x2*y1 - y2*x1

        return [a, b, c]
    

    def getIntersection(self, coeffs1, coeffs2):
        a1 = coeffs1[0]
        b1 = coeffs1[1]
        c1 = coeffs1[2]
        a2 = coeffs2[0]
        b2 = coeffs2[1]
        c2 = coeffs2[2]

        determinant = a1*b2 - b1*a2
        
        if(determinant != 0):
            xIntersection = (b1*c2 - b2*c1)/determinant
            yIntersection = (a2*c1 - a1*c2)/determinant
            return [xIntersection, yIntersection]
        
        else:
            return None


    

    def getDistanceBetweenSegments(self, segment1, segment2):

        x1 = segment1[0][0]
        y1 = segment1[0][1]
        x2 = segment1[1][0]
        y2 = segment1[1][1]
        x3 = segment2[0][0]
        y3 = segment2[0][1]
        x4 = segment2[1][0]
        y4 = segment2[1][1]

        distances = [
        self.getEuclideanDistance((x1, y1), (x3, y3)),
        self.getEuclideanDistance((x1, y1), (x4, y4)),
        self.getEuclideanDistance((x2, y2), (x3, y3)),
        self.getEuclideanDistance((x2, y2), (x4, y4))
        ]

        # Find the minimum distance
        minDistance = np.min(distances)

        return minDistance



class RandomColorGenerator:

    def getRandomColor(self):
        redValue = random.random()
        greenValue = random.random()
        blueValue = random.random()

        return np.array([redValue, greenValue, blueValue])

    def rgb2Hex(self, color):
        red = int(color[0]*255)
        blue = int(color[1]*255)
        green = int(color[2]*255)
        
        redString = "0x{:02x}".format(red)[2:]
        blueString = "0x{:02x}".format(blue)[2:]
        greenString = "0x{:02x}".format(green)[2:]

        hexString = "#"+redString+blueString+greenString

        return hexString

    def getHexColor(self):
        return self.rgb2Hex(self.getRandomColor())

    def getRandomColors(self, nColors, separation = 0.1):

        colors = []
        maxIter = 10*nColors
        iters = 0
        while(len(colors) < nColors and iters < maxIter):
            newColor = self.getRandomColor()
            addColor = True
            for i in range(0,len(colors)):
                color = colors[i]
                dst = np.sqrt((newColor[0] - color[0])**2 + (newColor[1] - color[1])**2 + (newColor[2] - color[2])**2)
                if(dst < separation):
                    addColor = False

            if(addColor):
                colors.append(newColor)

            iters = iters + 1

        if(iters >= maxIter):
            print("Iterations exceeded error")
            return -1
        else:

            hexColors = []
            for i in range(0,len(colors)):
                hexValue = self.rgb2Hex(colors[i])
                hexColors.append(hexValue)
            return hexColors

