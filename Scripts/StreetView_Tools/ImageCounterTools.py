from ultralytics import YOLO
import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

class YOLODetection:

    def __init__(self, modelPath):
        self.model = YOLO(modelPath)
        

    def countPeople(self, image):
        results = self.model(image, verbose = False)
        boxesObject = results[0].boxes
        classes = boxesObject.cls
        imageWidth = np.size(image,1)
        imageHeight = np.size(image,0)
        personsIndexes = []
        for i in range(0,len(classes)):
            if(classes[i] == 0):
                personsIndexes.append(i)

        self.count = len(personsIndexes)
        tensorBoxes = boxesObject.xywhn
        #print(boxesObject)
        bboxes = []
        for i in range(0,len(tensorBoxes)):
            if(i in personsIndexes):
                tensorBox = tensorBoxes[i]
                box = [int((tensorBox[0] - tensorBox[2]/2)*imageWidth), int((1 - tensorBox[1] - tensorBox[3]/2)*imageHeight), int(tensorBox[2]*imageWidth), int(tensorBox[3]*imageHeight)]
                bboxes.append(box)

        confidences = boxesObject.conf
        confArray = []
        for i in range(0,len(confidences)):
            confArray.append(float(confidences[i]))

        self.image = image
        self.bboxes = bboxes
        self.confidences = confArray

        #We will also extract the probabilities
        
        
        return self.count


    def countPeopleLight(self, image):
        results = self.model(image, verbose = False)
        boxesObject = results[0].boxes
        classes = boxesObject.cls
        imageWidth = np.size(image,1)
        imageHeight = np.size(image,0)
        personsIndexes = []
        for i in range(0,len(classes)):
            if(classes[i] == 0):
                personsIndexes.append(i)

        self.count = len(personsIndexes)
        #We will also extract the probabilities
        
        
        return self.count
        
    def getLabeledImage(self):
        rectangleDrawer = ImageRectangleDrawer()
        confidencesString = []
        for i in range(0,len(self.confidences)):
            confidencesString.append(str(round(self.confidences[i],2)))
        labeledImage = rectangleDrawer.drawBoxes(self.image, self.bboxes, confidencesString)
        return labeledImage


class ImageRectangleDrawer:

    def __init__(self):
        self.linePixelWidth = 5
        self.lineColor = np.array([219, 205, 48])
        self.headerHeight = 20
        self.fontSize = 12

    def drawBoxes(self, image, bboxes, texts):
        imageHeight = np.size(image, 0)
        newImage = image.copy()
        nBoxes = len(bboxes)
        for i in range(0,nBoxes):
            box = bboxes[i]
            x = box[0]
            y = box[1]
            width = box[2]
            height = box[3]
            index1 = imageHeight - y
            index2 = x

            #Bottom line 
            newImage[index1-self.linePixelWidth:index1, index2:index2 + width, :] = self.lineColor
            #Right line
            newImage[index1-height:index1, index2 + width-self.linePixelWidth:index2 + width, :] = self.lineColor
            #Top Line
            newImage[index1-height: index1 - height-self.linePixelWidth, index2: index2 + width,:] = self.lineColor
            #Left line 
            newImage[index1-height:index1, index2:index2 + self.linePixelWidth, :] = self.lineColor

            #Header
            newImage[index1-height-self.headerHeight:index1-height, index2:index2 + width, :] = self.lineColor
            
            #Text
            labelText = texts[i]
            pilImage = Image.fromarray(newImage)
            pilImageDraw = ImageDraw.Draw(pilImage)
            font = ImageFont.truetype("arial.ttf",12)
            pilImageDraw.text((index2, index1-height-self.headerHeight), labelText, fill=(0,0,0,255), font = font)
            newImage = np.array(pilImage)

        return newImage
            
            
            