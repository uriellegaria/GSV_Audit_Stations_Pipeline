from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import cv2
import os 
import imutils
import torch
import sys
import StreetView_Tools.DeepLabV3Plus.network
from torchvision import transforms
from tqdm import tqdm


class ImageStitcher:

    '''
    A simple class that can be used to stitch some images 
    to create a panoramic image. 
    '''

    def stitchImages(self, images, outputPath):
        cvImages = []
        for i in range(0,len(images)):
            openCVImage = cv2.cvtColor(images[i], cv2.COLOR_RGB2BGR)
            cvImages.append(openCVImage)

        stitcher = cv2.Stitcher_create()
        try:
            status, result = stitcher.stitch(cvImages)
            cv2.imwrite(outputPath, result)
        except:
            print("Could not stitch "+outputPath)
            print(len(images))

class SkySegmentation:
    def __init__(self, modelPath):
        modelName = "deeplabv3plus_resnet101"
        numClasses = 19
        outputStride = 8
        self.modelPath = modelPath
        model = StreetView_Tools.DeepLabV3Plus.network.modeling.__dict__[modelName](num_classes=numClasses, output_stride=outputStride)
        model.load_state_dict(torch.load(self.modelPath, map_location=torch.device('cpu'))['model_state'])
        self.model = model
        

    def segmentImage(self, imgArray):

        transform = transforms.ToTensor()
        inputImage = transform(imgArray)
        inputImage = inputImage.unsqueeze(0)
        self.model.eval()
        outputs = self.model(inputImage)
        preds = outputs.max(1)[1].detach().cpu().numpy()
        skyIndex = 10
        n = np.size(preds,1)
        m = np.size(preds,2)

        mask = np.zeros((n,m))
        for i in range(0,n):
            for j in range(0,m):
                if(preds[0,i,j] == skyIndex):
                    mask[i,j] = 1
        

        resizedMask = cv2.resize(mask, (np.size(imgArray,1), np.size(imgArray,0)),interpolation = cv2.INTER_NEAREST)
        maskedImg = imgArray.copy()
        for i in range(0,np.size(imgArray,0)):
            for j in range(0,np.size(imgArray,1)):
                maskedImg[i,j,:] = imgArray[i,j,:]*resizedMask[i,j]

        
        return resizedMask, maskedImg

class SVFCalculator:
    def obtainSVF(self, img, fishImageWidth, fishImageHeight, showFishImage = False):
        '''
        Receives a segmented image and gives the VCF metric
        
        '''
        fishImgConverter = Panoramic2FishEye(fishImageWidth, fishImageHeight)
        fishImgConverter.setPanoramic(img)
        radiusFraction = 1
        fishImage = fishImgConverter.convert2FishEye(radiusFraction)
        if(showFishImage):
            plt.figure()
            plt.imshow(fishImage)
            plt.title("Fish-eye image")

        radius = fishImgConverter.radius

        n = np.size(fishImage,0)
        m = np.size(fishImage,1)
        totalPixels = 0
        occupiedPixels = 0
        midX = int(m/2)
        midY = int(n/2)
        for i in range(0,n):
            for j in range(0,m):
                dst = np.sqrt((j - midX)**2 + (i - midY)**2)
                if(dst < radius):
                    totalPixels = totalPixels + 1
                    if(not all(v == 0 for v in fishImage[i,j,:])):
                        occupiedPixels = occupiedPixels + 1

        return occupiedPixels/totalPixels

    def getMeanSVF(self, images, fishImageWidth, fishImageHeight):
        meanSVF = 0
        for i in tqdm(range(0,len(images))):
            image = images[i]
            svf = self.obtainSVF(image, fishImageWidth, fishImageHeight, showFishImage = False)
            meanSVF = meanSVF + svf/len(images)
        if(len(images)==0):
            meanSVF = float('nan')

        return meanSVF

class Panoramic2FishEye:
    '''
    Obtains a Fish eye image from a panoramic image
    '''

    def __init__(self, imgWidth, imgHeight):
        '''
        imgWidth and imgHeight are the width and height
        of the Fish-eye images that will be generated. 
        '''
        self.imgWidth = imgWidth
        self.imgHeight = imgHeight

    def setPanoramicWithPath(self, imgPath):
        
        self.img = np.asarray(Image.open(imgPath))/255.0


    def setPanoramic(self, img):
        self.img = img

    def getPanoramicImage(self):
        return self.img

    def convert2FishEye(self, radiusFraction):

        radius = radiusFraction*np.min([self.imgWidth, self.imgHeight])
        self.radius = radius
        midPointX = int(self.imgWidth/2)
        midPointY = int(self.imgHeight/2)

        fishImage = np.zeros((self.imgHeight, self.imgWidth,3))
        

        panoramicWidth = np.size(self.img,1)
        panoramicHeight = np.size(self.img,0)

        for i in range(0,self.imgHeight):
            for j in range(0,self.imgWidth):
                xa = j
                ya = i

                if(xa < midPointX):
                    index1 = int((np.sqrt((xa - midPointX)**2 + (ya - midPointY)**2)/radius)*panoramicHeight)
                    index2 = int((np.pi/2 + np.arctan((ya - midPointY)/(xa - midPointX)))*(panoramicWidth/(2*np.pi)))
                    fishImage[i,j,:] = self.img[index1, index2,:]

                elif(xa > midPointX):
                    index1 = int((np.sqrt((xa - midPointX)**2 + (ya - midPointY)**2)/radius)*panoramicHeight)
                    index2 = int((3*np.pi/2 + np.arctan((ya - midPointY)/(xa - midPointX)))*(panoramicWidth/(2*np.pi)))
                    fishImage[i,j,:] = self.img[index1, index2,:]

        return fishImage