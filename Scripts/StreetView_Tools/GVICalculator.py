import numpy as np 

class GVIMethod:
    SIMPLE = 0
    MACHINE_LEARNING = 1

class GVICalculator:

    def __init__(self, method):
        self.method = method
        #Simple method params
        self.thresholdGVI = 0.83

    def setThresholdGVI(self, thresholdValue):
        self.thresholdGVI = thresholdValue

    def getMask(self, image):
        if(self.method == GVIMethod.SIMPLE):
            n = np.size(image, 0)
            m = np.size(image, 1)

            greenMarks = np.zeros((n,m))
            for i in range(0,n):
                for j in range(0,m):
                    rValue = image[i,j,0]
                    gValue = image[i,j,1]
                    bValue = image[i,j,2]
                    ratio1 = float('inf')
                    ratio2 = float('inf')

                    if(gValue != 0):
                        ratio1 = rValue/gValue
                        ratio2 = bValue/gValue
                    
                        if(ratio1 < self.thresholdGVI and ratio2 < self.thresholdGVI):
                            greenMarks[i,j]  = 1

            return greenMarks

    def getGVI(self, image):
        mask = self.getMask(image)
        n = np.size(image, 0)
        m = np.size(image, 1)

        gvi = sum(sum(mask))/(n*m)
        return gvi

    def getAverageGVI(self, images):
        values = []
        for i in range(0,len(images)):
            image = images[i]
            value = self.getGVI(image)
            values.append(value)

        avgGVI = np.mean(values)
        return avgGVI