#Let's create a class that can be used to achieve a visualization of a map based on attribute 
#variables.

#3 types of variables

from enum import Enum
import matplotlib.patches as patches
import numpy as np
import matplotlib.pyplot as plt
from Utilities.Utilities import ColorMapCreator
import matplotlib as mpl

class VariableType(Enum):
    DISCRETE = 0
    CONTINUOUS = 1
    CATEGORICAL = 2

#Ok so the path to get to using this class would be Having a geojson -> Using the StreetSampleTools to open strets
#-> Adding attributes to the streets (for instance with some street view analysis)-> Visualizing the streets

class StreetAttributesVisualizer:

    def __init__(self, streetSampler):
        self.streetSampler = streetSampler


    def colorByAttribute(self, attributeName, attributeType, width, height, edgeSize, *args):
        #For continuous variables args contains two triplets: 1. the RGB for min value coor
        #and 2. The RGB for max value. 

        #For discrete variables (counts of people, obstacles, etc.), you could actually use the
        #same color scheme as continuous variables. But i will provide an option to specify the 
        #value of the variable on each street. args here provides the font size, which has to be 
        #adapted to the size of the map.

        #Finally, for categorical variables args provides a dictionary specifying the color corresponding
        #to each value. Example red = sidewalk, blue = no sidewalk. Or red = more than 5 obstacles, blue = less than
        #five obstaces
        if(attributeType == VariableType.CONTINUOUS):
            minValueColor = args[0]
            maxValueColor = args[1]

            #We first need to get the value of the attribute for all streeets

            attributeValues = []
            streets = self.streetSampler.streets
            for i in range(0,len(streets)):
                street = streets[i]
                attributeValue = street.attributes[attributeName]
                attributeValues.append(attributeValue)


            minValue = np.min(attributeValues)
            maxValue = np.max(attributeValues)

            for i in range(0,len(streets)):
                street = streets[i]
                attributeValue = attributeValues[i]
                if(maxValue - minValue > 0):
                    color = minValueColor + (maxValueColor - minValueColor)*((attributeValue-minValue)/(maxValue - minValue))
                    street.setAttributeValue("color", color)
                
                else:
                    color = minValueColor
                    street.setAttributeValue("color", color)


            #Now that we have been asigned a value we can draw the streets
            fig, ax = plt.subplots(figsize = (width, height), layout = 'constrained')
            colorMapCreator = ColorMapCreator()
            norm, colorMap = colorMapCreator.getColorMap(minValueColor, maxValueColor, minValue, maxValue)
            
            for i in range(0,len(streets)):
                street = streets[i]
                streetColor = street.attributes["color"]
                segments = street.streetSegments
                for j in range(0,len(segments)):
                    segment = segments[j]
                    xCoords = [x[0] for x in segment]
                    yCoords = [x[1] for x in segment]
                    plt.plot(xCoords, yCoords, linewidth = edgeSize, color = streetColor)


            fig.colorbar(mpl.cm.ScalarMappable(norm = norm, cmap = colorMap), ax = ax, orientation = 'vertical', label = attributeName)
            
        elif(attributeType == VariableType.DISCRETE):
            minValueColor = args[0]
            maxValueColor = args[1]
            fontSize = args[2]

            #We first need to get the value of the attribute for all streeets

            attributeValues = []
            streets = self.streetSampler.streets
            for i in range(0,len(streets)):
                street = streets[i]
                attributeValue = street.attributes[attributeName]
                attributeValues.append(attributeValue)


            minValue = np.min(attributeValues)
            maxValue = np.max(attributeValues)

            for i in range(0,len(streets)):
                street = streets[i]
                attributeValue = attributeValues[i]
                color = minValueColor + (maxValueColor - minValueColor)*((attributeValue-minValue)/(maxValue - minValue))
                street.setAttributeValue("color", color)


            #Now that we have been asigned a value we can draw the streets
            fig, ax = plt.subplots(figsize = (width, height), layout = 'constrained')
            mapCreator = ColorMapCreator()
            norm, colorMap = mapCreator.getColorMap(minValueColor, maxValueColor, minValue, maxValue)
            
            for i in range(0,len(streets)):
                street = streets[i]
                streetColor = street.attributes["color"]
                segments = street.streetSegments
                attributeValue = attributeValues[i]
                for j in range(0,len(segments)):
                    segment = segments[j]
                    xCoords = [x[0] for x in segment]
                    yCoords = [x[1] for x in segment]
                    ax.plot(xCoords, yCoords, linewidth = edgeSize, color = streetColor)

                
                points = street.getPointsList()
                xCoords = [x[0] for x in points]
                yCoords = [x[1] for x in points]

                xAverage = sum(xCoords)/len(xCoords)
                yAverage = sum(yCoords)/len(yCoords)
                ax.text(xAverage, yAverage, int(attributeValue), fontsize = fontSize)

            #Let's create a dummy mappable
            fig.colorbar(mpl.cm.ScalarMappable(norm = norm, cmap = colorMap), ax = ax, orientation = 'vertical', label = attributeName)

        elif(attributeType == VariableType.CATEGORICAL):
            colorDictionary = args[0]
            #In this case we can directly start drawing the streets with the appropriate color
            streets = self.streetSampler.streets
            plt.figure(figsize = (width, height))

            colorPatches = []
            colorDictionaryKeys = list(colorDictionary.keys())
            for i in range(0,len(colorDictionaryKeys)):
                key = colorDictionaryKeys[i]
                colorAttribute = colorDictionary[key]
                keyString = str(key)
                patch = patches.Patch(color = colorAttribute, label = keyString)
                colorPatches.append(patch)
                
            for i in range(0,len(streets)):
                street = streets[i]
                attributeValue = street.attributes[attributeName]
                streetColor = colorDictionary[attributeValue]
                segments = street.streetSegments
                for j in range(0,len(segments)):
                    segment = segments[j]
                    xCoords = [x[0] for x in segment]
                    yCoords = [x[1] for x in segment]
                    plt.plot(xCoords, yCoords, color = streetColor, linewidth = edgeSize)
                    

            


