from PIL import Image
from tqdm import tqdm
import numpy as np
from IPython import display
import csv
import sys, os
from enum import Enum
from .StreetSampleTools import StreetProperty



class StreetLabeler:

    def __init__(self, streetSampler):

        '''
        Receives a street sampler with already computed
        sampling points. 
        '''
        self.streetSampler = streetSampler

    
    def getAllImages(self, outputPathGVI, outputPathSVF, googleAPIKey):
        from .StreetViewTools import GoogleStreetViewCollector
        from .StreetViewTools import CollectionGeometry

        streets = self.streetSampler.streets
        streetViewCollector = GoogleStreetViewCollector(googleAPIKey)
        #Choose an angle in-between
        streetViewCollector.setPitch(15)
        streetViewCollector.size = "640x640"
        nStreets = len(streets)

        for i in tqdm(range(0,nStreets)):
            street = streets[i]
            streetName = street.streetId
            samplingPoints = street.getGoogleFormattedSamplingPoints()
            bearings = street.getBearings()
            pathGVI = os.path.join(outputPathGVI, streetName)
            for j in range(0,len(samplingPoints)):
                point = samplingPoints[j]
                pathSVF = os.path.join(outputPathSVF, streetName,"Point_"+str(j))
                bearing = bearings[j]
                if(not os.path.exists(pathSVF) or not os.path.exists(pathGVI)):
                    streetViewCollector.collectPictures(CollectionGeometry.COMBINED_VIEWS, pathSVF, point, bearing, pathGVI, j)
    

    def getImagesForGVI(self, parentPath, googleAPIKey):
        from .StreetViewTools import GoogleStreetViewCollector
        from .StreetViewTools import CollectionGeometry
        #First we will obtain images of both sides of the street 
        #using the google API for each street
        streets = self.streetSampler.streets
        streetViewCollector = GoogleStreetViewCollector(googleAPIKey)
        streetViewCollector.setPitch(0)
        streetViewCollector.size = '640x640'
        for i in range(0,len(streets)):
            street = streets[i]
            streetName = street.streetId
            samplingPoints = street.getGoogleFormattedSamplingPoints()
            outputPath = os.path.join(parentPath, streetName)
            if(not os.path.exists(outputPath)):
                streetViewCollector.collectPictures(CollectionGeometry.STREET, outputPath, samplingPoints)

    def tagStandCounts(self, parentDir, modelPath):
        from .SellerStandDetector.SellerStandSegmentation import SellerStandSegmentator

        segmentator = SellerStandSegmentator(modelPath)
        streets = self.streetSampler.streets
        nStreets = len(streets)

        for i in tqdm(range(0,nStreets)):
            street = streets[i]
            streetName = street.streetId
            nStreetPoints = len(street.samplingPoints)
            images = []
            pathLeft = os.path.join(parentDir, streetName, "Image_street_left")
            pathRight = os.path.join(parentDir, streetName, "Image_street_rigth")
            #Collect images for the street in both sides (left and right)
            for j in range(0,nStreetPoints):
                pathPointLeft = os.path.join(pathLeft, "gsv_"+str(j)+".jpg")
                pathPointRight = os.path.join(pathRight, "gsv_"+str(j)+".jpg")
                if(os.path.exists(pathPointLeft)):
                    imageLeft = np.array(Image.open(pathPointLeft))
                    images.append(imageLeft)
                if(os.path.exists(pathPointRight)):
                    imageRight = np.array(Image.open(pathPointRight))
                    images.append(imageRight)
            
            standCounts = 0
            for j in range(0,len(images)):
                image = images[j]
                masks, segmentedImages = segmentator.segmentSellerStands(image)
                nStands = len(masks)
                standCounts = standCounts + nStands
            
            street.setAttributeValue(StreetProperty.INFORMAL_RETAIL_PROPERTY.value, standCounts)


    
    def tagBuildingCounts(self, parentDir, modelName):

        from .Building_Height_Calculation.BuildingSegmentation import BuildingSegmentator 
        streets = self.streetSampler.streets
        buildingSegmentator = BuildingSegmentator(modelName)

        for i in tqdm(range(0,len(streets))):
            street = streets[i]
            streetName = street.streetId
            nPoints = len(street.samplingPoints)
            images = []
            pathLeft = os.path.join(parentDir, streetName, "Image_street_left")
            pathRight = os.path.join(parentDir, streetName, "Image_street_right")
            for j in range(0,nPoints):
                pathPointLeft = os.path.join(pathLeft, "gsv_"+str(j)+".jpg")
                pathPointRight = os.path.join(pathRight, "gsv_"+str(j)+".jpg")
                if(os.path.exists(pathPointLeft)):
                    imageLeft = np.array(Image.open(pathPointLeft))
                    images.append(imageLeft)
                if(os.path.exists(pathPointRight)):
                    imageRight = np.array(Image.open(pathPointRight))
                    images.append(imageRight)
            
            buildingCounts = 0

            for j in range(0,len(images)):
                image = images[j]
                masks, segmentedImages = buildingSegmentator.segmentBuildingsInImage(image)
                nBuildings = len(masks)
                buildingCounts = buildingCounts + nBuildings
            
            street.setAttributeValue(StreetProperty.BUILDING_COUNTS_PROPERTY, buildingCounts)

    def tagGVI(self, parentDir):
        from .GVICalculator import GVIMethod
        from .GVICalculator import GVICalculator
        #Once the Data for all streets has been exported we can begin to 
        #Obtain the average GVIs, assigning them as parameters
        
        streets = self.streetSampler.streets
        #I just have the simple version for GVI Calculation right now
        gviCalculator = GVICalculator(GVIMethod.SIMPLE)
        for i in tqdm(range(0,len(streets))):
            street = streets[i]
            streetName = street.streetId
            nPoints = len(street.samplingPoints)
            images = []
            pathLeft = os.path.join(parentDir, streetName, "Image_street_left")
            pathRight = os.path.join(parentDir, streetName, "Image_street_right")
            for j in range(0,nPoints):
                pathPointLeft = os.path.join(pathLeft, "gsv_"+str(j)+".jpg")
                pathPointRight = os.path.join(pathRight, "gsv_"+str(j)+".jpg")
                if(os.path.exists(pathPointLeft)):
                    imageLeft = np.array(Image.open(pathPointLeft))
                    images.append(imageLeft)
                if(os.path.exists(pathPointRight)):
                    imageRight = np.array(Image.open(pathPointRight))
                    images.append(imageRight)
            

            #Obtain the mean GVI of all images 
            meanGVI = gviCalculator.getAverageGVI(images)
            street.setAttributeValue(StreetProperty.GVI_PROPERTY.value, meanGVI)


    def exportPanoramicsForSVF(self, parentDir, nShots, avoidRepeats = True):
        '''
        nShots = How many images were obtained per point. 
        '''
        from .SVFComputeTools import ImageStitcher
        streets = self.streetSampler.streets
        #svfCalculator = SVFCalculator()
        nStreets = len(streets)
        imageStitcher = ImageStitcher()
        #segmentator = SkySegmentation()
        
        for i in tqdm(range(0,nStreets)):
            street = streets[i]
            streetName = street.streetId
            nPoints = len(street.samplingPoints)
            parentPath = os.path.join(parentDir, streetName)
            for j in range(0,nPoints):
                pointPath = os.path.join(parentPath, "Point_"+str(j),"image_point")
                panoramicPath = os.path.join(pointPath, "panoramic_"+str(j)+".jpg")
                if(avoidRepeats == True and os.path.exists(panoramicPath)):
                    continue
                
                shots = []
                print("Point "+str(j))
                for s in range(0,nShots):
                    shotPath = os.path.join(pointPath, "gsv_"+str(s)+".jpg")
                    if(os.path.exists(shotPath)):
                        shot = np.array(Image.open(shotPath))
                        shots.append(shot)
                
                if(len(shots) > 0):
                    if(avoidRepeats == True and not os.path.exists(panoramicPath)):
                        imageStitcher.stitchImages(shots, panoramicPath)
                    elif(avoidRepeats == False):
                        imageStitcher.stitchImages(shots, panoramicPath)

            display.clear_output(wait = True)

    def tagSVF(self, parentDir,fishImageWidth, fishImageHeight, skySegmentationModelPath):

        '''
        nShots = How many images were obtained per point. 
        '''
        from .SVFComputeTools import SkySegmentation
        from .SVFComputeTools import SVFCalculator
        
        streets = self.streetSampler.streets
        svfCalculator = SVFCalculator()
        nStreets = len(streets)
        segmentator = SkySegmentation(skySegmentationModelPath)
        
        for i in tqdm(range(0,nStreets)):
            street = streets[i]
            streetName = street.streetId
            nPoints = len(street.samplingPoints)
            parentPath = os.path.join(parentDir, streetName)
            panoramicImages = []
            
            for j in range(0,nPoints):
                pointPath = os.path.join(parentPath,"Point_"+str(j),"image_point","panoramic_"+str(j)+".jpg")
                if(os.path.exists(pointPath)):
                    panoramicImage = np.array(Image.open(pointPath))
                    mask, segmentedImage = segmentator.segmentImage(panoramicImage)
                    panoramicImages.append(segmentedImage)
                

            meanSVF = svfCalculator.getMeanSVF(panoramicImages, fishImageWidth, fishImageHeight)
            street.setAttributeValue(StreetProperty.SVF_PROPERTY.value, meanSVF)
            display.clear_output(wait = True)
    
    def getImagesForSVF(self, parentDir, googleAPIKey):
        from .StreetViewTools import GoogleStreetViewCollector
        from .StreetViewTools import CollectionGeometry
        #Get the streets
        streets = self.streetSampler.streets
        streetViewCollector = GoogleStreetViewCollector(googleAPIKey)
        for i in range(0,len(streets)):
            street = streets[i]
            streetName = street.streetId
            samplingPoints = street.getGoogleFormattedSamplingPoints()
            outputPath = os.path.join(parentDir, streetName)

            for j in range(0,len(samplingPoints)):
                samplingPoint = samplingPoints[j]
                pointPath = os.path.join(outputPath, "Point_"+str(j))
                if(not os.path.exists(pointPath)):
                    streetViewCollector.collectPictures(CollectionGeometry.POINT, pointPath, samplingPoint)
    
        

    def tagWithCSVFile(self, path, columnIndex, isFloat = True):
        attributeName = ""
        attributeValues = []
        increment = 0
        with open(path, newline = '\n') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',' )
            for row in reader:
                if(increment == 0):
                    attributeName = row[columnIndex]
                    increment += 1
                else:
                    attributeValue = row[columnIndex]
                    if(attributeValue == "nan"):
                        attributeValue = -1
                    attributeValues.append(attributeValue)



        #Get the mean for nan values

        meanVal = 0
        countsNonNan = 0
        for i in range(0,len(attributeValues)):
            if(attributeValues[i] != -1):
                meanVal = meanVal + float(attributeValues[i])
                countsNonNan = countsNonNan + 1

        meanVal = meanVal/countsNonNan

        for i in range(0,len(attributeValues)):
            if(attributeValues[i] == -1):
                attributeValues[i] = meanVal

        streets = self.streetSampler.streets
        nStreets = len(streets)
        for i in range(0,nStreets):
            street = streets[i]
            if(isFloat):
                street.setAttributeValue(attributeName, float(attributeValues[i]))
            else:
                street.setAttributeValue(attributeName, attributeValues[i])

    def tagAudits(self, parentDir,nClasses):
        streets = self.streetSampler.streets
        for i in range(0,len(streets)):
            street = streets[i]
            streetName = street.streetId
            detectionPath = os.path.join(parentDir, streetName, "detections.csv")
            headers = []
            #First read the tag names
            counter = 0
            data = []
            with open(detectionPath, newline = "\n") as csvfile:
                reader = csv.reader(csvfile, delimiter = ",")
                for row in reader:
                    if(counter == 0):
                        headers = row
                        counter = counter + 1
                    else:
                        data.append([int(float(x)) for x in row])
            

            data = np.array(data)
            sumDetections = -1
            if(np.size(data,0) > 1):
                sumDetections = np.sum(data,0)
            elif(np.size(data,0) == 1):
                sumDetections = data
            else:
                sumDetections = np.zeros(nClasses)
            
            for j in range(0,len(headers)):
                street.setAttributeValue(headers[j], sumDetections[j])
            
            
                
            


    def tagCounts(self, parentDir, modelPath):
        from .ImageCounterTools import YOLODetection
        streets = self.streetSampler.streets
        #I just have the simple version for GVI Calculation right now
        personCounter = YOLODetection(modelPath)
        print("Gathering images")
        for i in tqdm(range(0,len(streets))):
            street = streets[i]
            streetName = street.streetId
            nPoints = len(street.samplingPoints)
            images = []
            pathLeft = os.path.join(parentDir, streetName, "Image_street_left")
            pathRight = os.path.join(parentDir, streetName, "Image_street_right")
            for j in range(0,nPoints):
                pathPointLeft = os.path.join(pathLeft, "gsv_"+str(j)+".jpg")
                pathPointRight = os.path.join(pathRight,"gsv_"+str(j)+".jpg" )
                if(os.path.exists(pathPointLeft)):
                    imageLeft = np.array(Image.open(pathPointLeft))
                    images.append(imageLeft)
                if(os.path.exists(pathPointRight)):
                    imageRight = np.array(Image.open(pathPointRight))
                    images.append(imageRight)
            

            #Obtain the mean GVI of all images

            counts = 0
            for i in range(0,len(images)):
                image = images[i]
                imageCount = personCounter.countPeopleLight(image)
                counts = counts + imageCount
            
            street.setAttributeValue(StreetProperty.SVI_COUNTS.value, counts)
    

    def tagBuildingHeights(self, parentDir, modelPath):
        from .Building_Height_Calculation.BuildingHeightCalculation import AutomaticHeightCalculation
        heightCalculator = AutomaticHeightCalculation(modelPath)
        streets = self.streetSampler.streets
        nStreets = len(streets)
        #Like always we need to extract the path to each of the images
        for i in tqdm(range(0,nStreets)):
            street = streets[i]
            streetName = street.streetId
            nPoints = len(street.samplingPoints)
            images = []
            pathLeft = os.path.join(parentDir, streetName, "Image_street_left")
            pathRight = os.path.join(parentDir, streetName, "Image_street_right")
            for j in range(0,nPoints):
                pathPointLeft = os.path.join(pathLeft, "gsv_"+str(j)+".jpg")
                pathPointRight = os.path.join(pathRight, "gsv_"+str(j)+".jpg")
                #Open the images and add them to the image array
                if(os.path.exists(pathPointLeft)):
                    imageLeft = np.array(Image.open(pathPointLeft))
                    images.append(imageLeft)
                
                if(os.path.exists(pathPointRight)):
                    imageRight = np.array(Image.open(pathPointRight))
                    images.append(imageRight)
        

            nImages = len(images)
            averageBuildingHeight = 0
            #We will tag the building counts as a plus since this variable is necessary to compute 
            #the average height anyway
            buildingCounter = 0
            for i in range(0,nImages):
                image = images[i]
                segmentedimages, heights = heightCalculator.computeHeightsWithMasks(image)
                nHeights = len(heights)
                for j in range(0,nHeights):
                    height = heights[j]
                    averageBuildingHeight = averageBuildingHeight + height
                    buildingCounter = buildingCounter + 1
                
            if(buildingCounter > 0):
                averageBuildingHeight = averageBuildingHeight/buildingCounter
            else:
                averageBuildingHeight = float('nan')
            
            street.setAttributeValue(StreetProperty.BUILDING_HEIGHT_PROPERTY.value, averageBuildingHeight)
            street.setAttributeValue(StreetProperty.BUILDING_COUNTS_PROPERTY.value, buildingCounter)



                    

