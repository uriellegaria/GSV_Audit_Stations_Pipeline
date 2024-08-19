
from PIL import Image
from .DockerContainerManager import DockerContainerManagement
import time
import os
import json
from tqdm import tqdm
import skimage.io
import numpy as np
import csv



class AuditMAPSContainerController:


    def __init__(self, imageName = "automaps_container", containerExists = True):
        
        self.dockerManager = DockerContainerManagement(imageName = imageName)
        #If the container does not exist yet create create a new one with the image
        #I think i will actually upload this eventually to Docker Hub, so that 
        if(containerExists == False):
            self.dockerManager.runNewContainer()

        
        self.classes =  self.denseDictionary = ["BG", "sidewalk", "road", "planter", "landscape", "trip_hazard", "bad_building", "good_building", "utility_pole", "buffer", "street_light", "seating", "walk_signal", "crosswalk","curb_ramp", "graffiti", "bike_mark","lightpole", "boarded_house", "wall", "driveway"]

    def getContainerId(self, index):
        return self.dockerManager.getContainerId(index)
    

    def exportCSV(self, headers, rows, path):
        with open(path, 'w') as csvfile:
            write = csv.writer(csvfile)
            write.writerow(headers)
            write.writerows(rows)
    


    def exportStreetMetricsCSVs(self, parentDir, streetSampler, outputDir, containerId):
        '''
        Receives a street sampler, does the auditing for all sampling points, and exports a 
        CSV per street in the following folder structure

        parentDir
            StreetName
                detections.csv

        '''

        streets = streetSampler.streets
        classNames = self.classes

        for i in tqdm(range(0,len(streets))):
            streetName = streets[i].streetId
            parentFolder = os.path.join(parentDir, streetName)
            nSamplingPoints = len(streets[i].samplingPoints)
            leftFolder = os.path.join(parentFolder, "Image_street_left")
            rightFolder = os.path.join(parentFolder, "Image_street_right")

            outputName = os.path.join(outputDir, streetName)
            rows = []

            if(not os.path.exists(outputName)):
                os.makedirs(outputName)

            for j in range(0,nSamplingPoints):
                photoDir = os.path.join(leftFolder, "gsv_"+str(j)+".jpg")
                if(os.path.exists(photoDir)):
                    img = np.array(skimage.io.imread(photoDir))
                    result = self.auditImage(outputName, img, containerId)
                    row = []
                    for s in range(0,len(classNames)):
                        countClass = result[classNames[s]]
                        row.append(countClass)
                    
                    rows.append(row)
                
                photoDir = os.path.join(rightFolder, "gsv_"+str(j)+".jpg")
                if(os.path.exists(photoDir)):
                    img = np.array(skimage.io.imread(photoDir))
                    result = self.auditImage(outputName, img, containerId)
                    row = []
                    for s in range(0,len(classNames)):
                        countClass = result[classNames[s]]
                        row.append(countClass)
                    
                    rows.append(row)
            
            csvFilePath = os.path.join(outputName, "detections.csv")

            self.exportCSV(classNames, rows, csvFilePath)

    
    def auditImage(self, outputPath, image, containerId, scriptName = "/test_automaps.py"):

        '''
        Provides a dictionary with the automap detected features (e.g. {graffiti: 1, buffer:0, etc.} ))
        Execution of this function puts the image inside the container, and then a script that produces the
        result will be called inside it. Finally, the result is extracted from the container as a json file
        '''

        #Start the container (in case it is not already running)
        self.dockerManager.startContainer(containerId)
        pathLocalImage = os.path.join(outputPath, "test_image.jpg")

        img = Image.fromarray(image)
        img.save(pathLocalImage)
        time.sleep(1)

        #Put the image into the container
        self.dockerManager.putFileIntoContainer(pathLocalImage, "/", containerId)

        #Process the image with automaps by running the script. This script has a predefined names, which is test_automaps.py
        #i know not the best, i will definitely change that in the future. 

        self.dockerManager.runScript(containerId, scriptName)
        
        #Good, now finally we can get the json file from the container
        jsonOutputPath = os.path.join(outputPath, "test_image.json")

        self.dockerManager.getContainerFile(containerId, "/test_image.json",  os.path.join(outputPath,"image_file.tar"), outputPath)

        #Finally let's open the json file
        f = open(jsonOutputPath)
        data = json.load(f)
        
        return data

       
        

        

        























