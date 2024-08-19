from ultralytics import YOLO
import numpy as np

class BuildingSegmentator:


    def __init__(self, modelDir):
        self.model = YOLO(modelDir)
    

    def segmentBuildingsInImage(self, image):
        '''
        The image provided needs to have a size of 640x640x3
        The method returns two arrays one with the segmentation masks
        and another with the segmented building images. 
        '''

        results = self.model(image, verbose=False)
        segmentedImages = []
        masks = []
        n = np.size(image, 0)
        m = np.size(image, 1)
        if(not results[0].masks is None):
            for mask in results[0].masks.data:
                mask = np.array(mask)
                #Make a copy of the image
                segmentedImage = image.copy()
                #Apply the mask to the image
                for i in range(0,n):
                    for j in range(0,m):
                        segmentedImage[i,j,:] = segmentedImage[i,j,:]*mask[i,j]
            
            
                segmentedImages.append(segmentedImage)
                masks.append(mask)
        
        return masks, segmentedImages
