import time
import numpy as np
import math
import shutil
import os
import requests
import json
from PIL import Image
from io import BytesIO



class MapillaryStreetViewCollector:

    def __init__(self, tokenKey):
        self.tokenKey = tokenKey
        self.size = 640
        self.searchRadius = 50
        self.limit = 1
    
    def setSize(self, size):
        self.size = size
    
    def setImagesStreet(self, nImagesStreet):
        self.imagesStreet = nImagesStreet
    
    def setImagesPoint(self, nImagesPoint):
        self.imagesPoint = nImagesPoint
    
    def collectImages(self, outputPath, points):
        pointDictionaries = []
        for i in range(0,len(points)):
            point = points[i]
            pointDictionaries.append({"latitude": point[0], "longitude": point[1], "radius":self.searchRadius, "limit": 1})
        
        for i in range(0,len(pointDictionaries)):
            dictionary = pointDictionaries[i]

            pointPath = os.path.join(outputPath, "image_point_"+str(i))

            if(not os.path.exists(pointPath)):
                os.makedirs(pointPath)
            imageId = self.getImageId(dictionary)
            if(not imageId is None):
                self.downloadImageWithId(imageId, pointPath, i)


    
    

    def getImageId(self, paramsDict):
        
        latitude = paramsDict['latitude']
        longitude = paramsDict['longitude']
        radius = paramsDict['radius']
        limit = paramsDict['limit']

        endPoint = 'https://graph.mapillary.com/images'
        bbox = f"{longitude - radius/111320.0},{latitude - radius/111320.0},{longitude + radius/111320.0},{latitude + radius/111320.0}"
        headers = {
             'Authorization': f'OAuth {self.tokenKey}'
        }
        paramsRequest = {
             'access_token':self.tokenKey, 
             'bbox':bbox,
             'limit':limit
        }

        response = requests.get(endPoint, headers = headers, params = paramsRequest)
        imageId = None
        if(response.status_code == 200):
             data = response.json()
             if('data' in data and len(data['data']) > 0):
                  imageId = data['data'][0]['id']
            
        return imageId
                  

    
    def downloadImageWithId(self, imageId, folderPath, pictureIndex):
        

        metadataEndpoint = "https://graph.mapillary.com"
        headers = {
            'Authorization': f'OAuth {self.tokenKey}'
        }

        paramsRequest = {
             'access_token':self.tokenKey,
             'fields': 'thumb_2048_url, id, captured_at, geometry, sequence'
        }

        urlImage = f"{metadataEndpoint}/{imageId}"
        responseImage = requests.get(urlImage, headers=headers, params = paramsRequest)
        if responseImage.status_code == 200:
            dataImage = responseImage.json()
            imageUrl = dataImage['thumb_2048_url']
            print(imageUrl)
            metadata = {
                "id": dataImage['id'],
                "captured_at": ['captured_at'],
                "geometry": ['geometry'],
                "sequence": ['sequence']
            }
            responseDownload = requests.get(imageUrl)
            if responseDownload.status_code == 200:
                imagePath = os.path.join(folderPath, f"gsv_{pictureIndex}.jpg")
                metadataPath = os.path.join(folderPath, f"gsv_{pictureIndex}.json")

                image = Image.open(BytesIO(responseDownload.content))
                image = image.resize((self.size, self.size), Image.LANCZOS)
                image.save(imagePath, format='JPEG')

                with open(metadataPath, 'w') as meta_file:
                    json.dump(metadata, meta_file, indent=4)
        else:
            return None
    
        
    



        
            






            