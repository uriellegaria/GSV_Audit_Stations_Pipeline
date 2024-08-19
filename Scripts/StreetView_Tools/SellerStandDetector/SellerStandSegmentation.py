from ultralytics import YOLO
import numpy as np


class SellerStandSegmentator:

    def __init__(self, modelPath):
        self.model = YOLO(modelPath)
    

    def segmentSellerStands(self, image):
        '''
        Returns masks and segmented seller stands detected in an image.
        The provided images should be numpy array of size 640x640x3
        '''
        results = self.model(image, verbose = False)
        segmentedImages = []
        masks = []
        n = np.size(image,0)
        m = np.size(image,1)
        if(not results[0].masks is None):
            for mask in results[0].masks.data:
                #Convert tensor to numpy array
                mask = np.array(mask)
                #Make a copy of the image to segment it
                segmentedImage = image.copy()
                #Apply the mask by multiplying
                for i in range(0,n):
                    for j in range(0,m):
                        segmentedImage[i,j,:] = image[i,j,:]*mask[i,j]
                
                segmentedImages.append(segmentedImage)
                masks.append(mask)

        
        return masks, segmentedImages



