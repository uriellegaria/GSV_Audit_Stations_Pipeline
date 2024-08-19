import sys

from Utilities.Utilities import RandomColorGenerator
from Map_Extraction.MultiJSONVisualizer import MultiGeoJSONVisualizer
import math
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
from Utilities.Utilities import GeometryCalculations
from StreetView_Tools.StreetViewTools import GoogleStreetViewCollector
from Utilities.Utilities import ColorsWalkabilityVars
from Utilities.Utilities import CSVExporter


class WalkabilityReport:

    def __init__(self, mapDataLocation, geojsonStreetsPath, geojsonsPlacesPaths):
        '''
        geojsonStreetsPath is a path to the geojson of the walkable streets
        geojsonsPlacesPaths is a list of paths to the geojsons of the different types of
        places considered in the multilayer network. 
        '''
        self.mapDataLocation = mapDataLocation
        self.geojsonStreetsPath = os.path.join(self.mapDataLocation, geojsonStreetsPath)
        self.geojsonsPlacesPaths = geojsonsPlacesPaths

        nPlaceLayers = len(self.geojsonsPlacesPaths)
        
        self.layerNames= []
        self.layerNames.append(geojsonStreetsPath.split(".geojson")[0])

        for i in range(0,nPlaceLayers):
            self.layerNames.append(self.geojsonsPlacesPaths[i].split(".geojson")[0])

        for i in range(0,nPlaceLayers):
            self.geojsonsPlacesPaths[i] = os.path.join(self.mapDataLocation, self.geojsonsPlacesPaths[i])
        
        #Add map data location to path
        sys.path.append(self.mapDataLocation)
        self.openMap()

        self.maxSamplingPoints = 100

        collector = GoogleStreetViewCollector(None)
        self.nShots = collector.imagesPoint
        self.auditAttributes = ['sidewalk', 'road', 'planter', 'landscape', 'trip_hazard', 'bad_building', 'good_building', 'utility_pole', 'buffer', 'street_light', 'seating', 'walk_signal', 'crosswalk', 'curb_ramp', 'graffiti', 'bike_mark', 'lightpole', 'boarded_house', 'wall', 'driveway']
        
    def openMap(self):
        #First we need to open our maps. The Map visualizer can help with this although i 
        #wonder if a new specialized class would be best. 
        
        #For now i think it will suffice, it is quite a nice data structure i created 
        #i must say.

        nPlaces = len(self.geojsonsPlacesPaths)
        colorGenerator = RandomColorGenerator()
        #For visualization purposes
        layerColors = colorGenerator.getRandomColors(nPlaces + 1)
        layerColors[0] = "#dba753"
        #Let's create a multilayer visualizer 
        multiLayerData = MultiGeoJSONVisualizer()

        #Add the paths layer
        multiLayerData.addLayer(self.layerNames[0], self.geojsonStreetsPath, layerColors[0], pointLayer = False)

        #Add the places layers
        for i in range(0,len(self.geojsonsPlacesPaths)):
            placesPath = self.geojsonsPlacesPaths[i]
            multiLayerData.addLayer(self.layerNames[i+1], placesPath, layerColors[i+1], pointLayer = True)

        self.multiLayerData = multiLayerData


    def drawMap(self, layerNames, nodeSize, edgeSize, width, height):
        self.multiLayerData.setNodeSizeForAll(nodeSize)
        self.multiLayerData.setEdgeSizeForAll(edgeSize)

        self.multiLayerData.drawMultiLayer(layerNames, width, height)

    def extractNodePositions(self, graph):
        nodeKeys = list(graph.nodes.keys())
        positions = []
        for i in range(0,len(nodeKeys)):
            nodeKey = nodeKeys[i]
            position = graph.nodes[nodeKey]['pos']
            positions.append(position)

        return positions


    def getMeanDistance(self, points1, points2):
        dst = 0
        nIters = 0
        distanceCalculator = GeometryCalculations()
        for i in range(0,len(points1)):
            point1 = points1[i]
            for j in range(0,len(points2)):
                point2 = points2[j]
                nIters = nIters + 1
                distance = distanceCalculator.getDistanceBetweenCoordinates(point1[1], point1[0], point2[1], point2[0])
                dst = dst + distance

        dst = dst/nIters
        return dst

    def getCountsPlaces(self, resultsPath, plotDistances = True):
        layers = self.multiLayerData.layers.copy()
        layers.pop(0)
        nLayers = len(layers)
        counts = np.zeros(nLayers)
        layerNames = self.multiLayerData.getLayerNames()
        layerNames.pop(0)

        for i in range(0,nLayers):
            layer = layers[i]
            layerGraph = layer.visualizationGraph
            nNodes = len(self.extractNodePositions(layerGraph))
            counts[i] = nNodes

        counts = counts*(100/sum(counts))
        if(plotDistances):
            plt.figure(figsize = (5,5))
            plt.bar(list(range(0,len(counts))), counts, tick_label = layerNames)
            plt.setp(plt.gca().get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
            plt.title("Place type distribution")
            plt.ylabel("%")
            plt.savefig(os.path.join(resultsPath,'place_counts.pdf'), dpi = 600, bbox_inches = 'tight')
        return counts


    def prepareSampling(self, drawSampling = True, pointColor = "#ff1764", nodeSize = "2", edgeSize = "2", edgeColor = "#ff700a", width = 7, height = 7):
        from StreetView_Tools.StreetSampleTools import StreetSampler
        self.sampler = StreetSampler(self.maxSamplingPoints)
        self.sampler.openStreets(self.geojsonStreetsPath)
        self.sampler.sampleStreetsNoIntersections()
        if(drawSampling):
            self.sampler.drawSamplingScheme(width, height,nodeSize = nodeSize, edgeSize = edgeSize, edgeColor = edgeColor, pointColor = pointColor)


    def prepareImages(self, outputParentPath, apiKey):
        from StreetView_Tools.StreetLabelling import StreetLabeler
        self.outputFolderGVI = os.path.join(outputParentPath,"GVI_Images")
        self.outputFolderSVF = os.path.join(outputParentPath,"SVF_Images")
        self.streetLabeller = StreetLabeler(self.sampler)
        self.streetLabeller.getAllImages(self.outputFolderGVI, self.outputFolderSVF, apiKey)

        self.streetLabeller.exportPanoramicsForSVF(self.outputFolderSVF, self.nShots)
        print("Exported panoramics")


    def exportGVIAndSVFResults(self, gviPath, svfPath, resultsPath, skySegModelPath, avoidRepetition = True):
        from StreetView_Tools.StreetLabelling import StreetLabeler
        self.streetLabeller = StreetLabeler(self.sampler)
        gviFilePath = os.path.join(resultsPath,"GVI.csv")
        svfFilePath = os.path.join(resultsPath, "SVF.csv")
        csvExporter = CSVExporter()
        if(avoidRepetition and not os.path.exists(gviFilePath)):
            self.streetLabeller.tagGVI(gviPath)
            header = ["GVI"]
            gviValues = []
            for i in range(0,len(self.sampler.streets)):
                street = self.sampler.streets[i]
                gviValue = street.attributes['GVI']
                gviValues.append([gviValue])

            csvExporter.exportCSV(header, gviValues, gviFilePath)
            print("Exported GVI Data")
        if(avoidRepetition and not os.path.exists(svfFilePath)):
            self.streetLabeller.tagSVF(svfPath, 1000, 1000, skySegModelPath)
            header = ["SVF"]
            svfValues = []
            for i in range(0,len(self.sampler.streets)):
                street = self.sampler.streets[i]
                svfValue = street.attributes['SVF']
                svfValues.append([svfValue])

            csvExporter.exportCSV(header, svfValues, svfFilePath)
            print("Exported SVF Data")

        if(not avoidRepetition):
            self.streetLabeller.tagGVI(gviPath)
            header = ["GVI"]
            gviValues = []
            for i in range(0,len(self.sampler.streets)):
                street = self.sampler.streets[i]
                gviValue = street.attributes['GVI']
                gviValues.append([gviValue])

            csvExporter.exportCSV(header, gviValues, gviFilePath)
            print("Exported GVI Data")

            self.streetLabeller.tagSVF(svfPath, 1000, 1000, skySegModelPath)
            header = ["SVF"]
            svfValues = []
            
            for i in range(0,len(self.sampler.streets)):
                street = self.sampler.streets[i]
                svfValue = street.attributes['SVF']
                svfValues.append([svfValue])

            csvExporter.exportCSV(header, svfValues, svfFilePath)
            print("Exported SVF Data")
    

    def exportBuildingHeightData(self, imagesPath, resultsPath, modelPath, avoidRepetition = True):
        from StreetView_Tools.StreetLabelling import StreetLabeler
        self.streetLabeller = StreetLabeler(self.sampler)
        pathBuildingHeightsCSV = os.path.join(resultsPath, "Building_Heights.csv")
        pathBuildingCountsCSV = os.path.join(resultsPath, "Building_Counts.csv")
        csvExporter = CSVExporter()

        if(avoidRepetition and not os.path.exists(pathBuildingHeightsCSV)):
            self.streetLabeller.tagBuildingHeights(imagesPath, modelPath)
            headerHeights = ["Building_Heights"]
            headerBuildingCounts = ["Building_Counts"]
            heightValues = []
            buildingCountValues = []
            streets = self.sampler.streets
            nStreets = len(streets)
            for i in range(0,nStreets):
                street = streets[i]
                heightValue = street.attributes['Building_Height']
                buildingCounts = street.attributes['Building_Counts']
                heightValues.append([heightValue])
                buildingCountValues.append([buildingCounts])
            
            csvExporter.exportCSV(headerBuildingCounts, buildingCountValues, pathBuildingCountsCSV)
            csvExporter.exportCSV(headerHeights, heightValues, pathBuildingHeightsCSV)


        elif(not avoidRepetition):
            self.streetLabeller.tagBuildingHeights()
            headerHeights = ["Building_Heights"]
            headerBuildingCounts = ["Building_Counts"]
            heightValues = []
            buildingCountValues = []
            streets = self.sampler.streets
            nStreets = len(streets)
            for i in range(0,nStreets):
                street = streets[i]
                heightValue = street.attributes['Building_Height']
                buildingCounts = street.attributes['Building_Counts']
                heightValues.append([heightValue])
                buildingCountValues.append([buildingCounts])
            
            csvExporter.exportCSV(headerBuildingCounts, buildingCounts, pathBuildingCountsCSV)
            csvExporter.exportCSV(headerHeights, heightValues, pathBuildingHeightsCSV)
        
    def exportSellerStandData(self, imagesPath, resultsPath, modelPath, avoidRepetition = True):
        from StreetView_Tools.StreetLabelling import StreetLabeler

        self.streetLabeller = StreetLabeler(self.sampler)
        csvFilePath = os.path.join(resultsPath, "SellerStands.csv")
        csvExporter = CSVExporter()
        if(avoidRepetition and not os.path.exists(csvFilePath)):
            self.streetLabeller.tagStandCounts(imagesPath, modelPath)
            header = ["N_Sellers"]
            #Counts for each street
            countValues = []
            streets = self.sampler.streets
            for i in range(0,len(streets)):
                street = streets[i]
                streetNSellers = street.attributes["Seller_Counts"]
                countValues.append([streetNSellers])
            
            csvExporter.exportCSV(header, countValues, csvFilePath)
            print("Exported seller counts")
        
        elif(not avoidRepetition):
            self.streetLabeller.tagStandCounts(imagesPath, modelPath)
            header = ["N_Sellers"]
            #Counts for each street
            countValues = []
            streets = self.sampler.streets
            for i in range(0,len(streets)):
                street = streets[i]
                streetNSellers = street.attributes["Seller_Counts"]
                countValues.append([streetNSellers])
            
            csvExporter.exportCSV(header, countValues, csvFilePath)
            print("Exported seller counts")
            







    def exportCountData(self, countPath, resultsPath, modelPath, avoidRepetition = True):
        from StreetView_Tools.StreetLabelling import StreetLabeler
        self.streetLabeller = StreetLabeler(self.sampler)
        countsFilePath = os.path.join(resultsPath, "Counts.csv")
        csvExporter = CSVExporter()
        if(avoidRepetition and not os.path.exists(countsFilePath)):
            self.streetLabeller.tagCounts(countPath, modelPath)

            header = ["Count"]
            countValues = []
            for i in range(0,len(self.sampler.streets)):
                street = self.sampler.streets[i]
                counts = street.attributes['Counts']
                countValues.append([counts])

            csvExporter.exportCSV(header, countValues, countsFilePath)
            print("Exported Count Data")

        elif(not avoidRepetition):
            self.streetLabeller.tagCounts(countPath, modelPath)

            header = ["Count"]
            countValues = []
            for i in range(0,len(self.sampler.streets)):
                street = self.sampler.streets[i]
                counts = street.attributes['Counts']
                countValues.append([counts])

            csvExporter.exportCSV(header, countValues, countsFilePath)
            print("Exported Count Data")
    

    def exportAuditSummaryCSV(self, resultsPath):
        detectionParent = os.path.join(resultsPath, "CSV_Audit")
        self.streetLabeller.tagAudits(detectionParent, 21)
        streets = self.streetLabeller.streetSampler.streets
        nStreets = len(streets)
        attributes = self.auditAttributes
        headers = ["Street Name"]
        headers.extend(attributes)
        rows = []
        csvExporter = CSVExporter()
        for i in range(0,nStreets):
            street = streets[i]
            streetName = street.streetId
            row = [streetName]
            for j in range(0,len(attributes)):
                value = street.attributes[attributes[j]]
                row.append(value)
            rows.append(row)
        
        csvExporter.exportCSV(headers, rows, os.path.join(resultsPath, "audits_summary.csv"))

    def exportAuditData(self,imagesPath, resultsPath, containerId):
        outputDir = os.path.join(resultsPath, "CSV_Audit")
        from StreetView_Tools.Audits.AuditMAPSContainerControl import AuditMAPSContainerController
        auditor = AuditMAPSContainerController()
        if(not os.path.exists(outputDir)):
            auditor.exportStreetMetricsCSVs(imagesPath, self.sampler, outputDir, containerId)
    
    def compileResults(self, resultsPath, dpi = 600):
        from StreetView_Tools.AttributeStreetVisualizer import StreetAttributesVisualizer
        from StreetView_Tools.AttributeStreetVisualizer import VariableType
        from StreetView_Tools.StreetLabelling import StreetLabeler
        outputDir = os.path.join(resultsPath, "Result_Figures")
        if(not os.path.exists(outputDir)):
            os.mkdir(outputDir)
        self.streetLabeller = StreetLabeler(self.sampler)

        #Variable standard colors
        
        #GVI
        gviPath = os.path.join(resultsPath, "GVI.csv")
        self.streetLabeller.tagWithCSVFile(gviPath, 0)
        streetVisualizer = StreetAttributesVisualizer(self.sampler)
        minColor = np.array(ColorsWalkabilityVars.GVI_MIN_COLOR.value)
        maxColor = np.array(ColorsWalkabilityVars.GVI_MAX_COLOR.value)
        streetVisualizer.colorByAttribute("GVI", VariableType.CONTINUOUS, 7, 7, 2, minColor, maxColor)
        plt.savefig(os.path.join(outputDir,'gvi_map.pdf'), dpi = 600, bbox_inches = 'tight')

        #SVF
        svfPath = os.path.join(resultsPath, "SVF.csv")
        self.streetLabeller.tagWithCSVFile(svfPath, 0)
        minColor = np.array(ColorsWalkabilityVars.SVF_MIN_COLOR.value)
        maxColor = np.array(ColorsWalkabilityVars.SVF_MAX_COLOR.value)
        streetVisualizer.colorByAttribute("SVF", VariableType.CONTINUOUS, 7, 7, 2, minColor, maxColor)
        plt.savefig(os.path.join(outputDir,'svf_map.pdf'), dpi = 600, bbox_inches = 'tight')

        #Seller Stands
        sellersPath = os.path.join(resultsPath, "SellerStands.csv")
        self.streetLabeller.tagWithCSVFile(sellersPath,0)
        minColor = np.array(ColorsWalkabilityVars.INFORMAL_RETAIL_MIN_COLOR.value)
        maxColor = np.array(ColorsWalkabilityVars.INFORMAL_RETAIL_MAX_COLOR.value)
        streetVisualizer.colorByAttribute("N_Sellers", VariableType.CONTINUOUS, 7,7,2, minColor, maxColor)
        plt.savefig(os.path.join(outputDir, 'seller_stand_map.pdf'), dpi = 600, bbox_inches = 'tight')

        #Building counts
        buildingCountsPath = os.path.join(resultsPath, "Building_Counts.csv")
        self.streetLabeller.tagWithCSVFile(buildingCountsPath, 0)
        minColor = np.array(ColorsWalkabilityVars.BUILDING_HEIGHTS_MIN_COLOR.value)
        maxColor = np.array(ColorsWalkabilityVars.BUILDING_HEIGHTS_MAX_COLOR.value)
        streetVisualizer.colorByAttribute("Building_Counts", VariableType.CONTINUOUS, 7,7,2, minColor, maxColor)
        plt.savefig(os.path.join(outputDir, "building_counts_map.pdf"))

        #Building Heights
        buildingHeightPath = os.path.join(resultsPath, "Building_Heights.csv")
        self.streetLabeller.tagWithCSVFile(buildingHeightPath, 0)
        minColor = np.array(ColorsWalkabilityVars.BUILDING_HEIGHTS_MIN_COLOR.value)
        maxColor = np.array(ColorsWalkabilityVars.BUILDING_HEIGHTS_MAX_COLOR.value)
        streetVisualizer.colorByAttribute("Building_Heights",VariableType.CONTINUOUS, 7,7,2, minColor, maxColor)
        plt.savefig(os.path.join(outputDir, "building_heights_map.pdf"), dpi = 600, bbox_inches = 'tight')
        

        #Counts
        countsPath = os.path.join(resultsPath, "Counts.csv")
        self.streetLabeller.tagWithCSVFile(countsPath, 0)
        fontSize = 8
        minColor = np.array(ColorsWalkabilityVars.COUNTS_MIN_COLOR.value)
        maxColor = np.array(ColorsWalkabilityVars.COUNTS_MAX_COLOR.value)
        streetVisualizer.colorByAttribute("Count", VariableType.DISCRETE, 7, 7, 2, minColor, maxColor, fontSize)
        plt.savefig(os.path.join(outputDir,'counts_map.pdf'), dpi = 600, bbox_inches = 'tight')

        #Audits autoMAPS
        detectionParent = os.path.join(resultsPath, "CSV_Audit")
        self.streetLabeller.tagAudits(detectionParent, 21)
        attributes = self.auditAttributes
        minColor = np.array(ColorsWalkabilityVars.COUNTS_MIN_COLOR.value)
        maxColor = np.array(ColorsWalkabilityVars.COUNTS_MAX_COLOR.value)

        for i in range(0,len(attributes)):
            print(attributes[i])
            streetVisualizer.colorByAttribute(attributes[i], VariableType.CONTINUOUS, 7, 7, 2, minColor, maxColor)
            plt.savefig(os.path.join(outputDir,attributes[i]+".pdf"), dpi = 600, bbox_inches = 'tight')
            
    
    def getPlacesDistanceMatrix(self, resultsPath, plotDistances = True):
        layers = self.multiLayerData.layers.copy()
        layers.pop(0)
        nLayers = len(layers)
        placesDistanceMatrix = np.zeros((nLayers, nLayers))
        layerNames = self.multiLayerData.getLayerNames()
        layerNames.pop(0)

        #We are assuming the first layer is always the one with the streets. 
        for i in range(0,nLayers - 1):
            layer = layers[i]
            layerGraph = layer.visualizationGraph
            nodePositions = self.extractNodePositions(layerGraph)
        
            for j in range(i,nLayers):
                layer2 = layers[j]
                layer2Graph = layer2.visualizationGraph
                nodePositions2 = self.extractNodePositions(layer2Graph)
                distance = self.getMeanDistance(nodePositions, nodePositions2)
                placesDistanceMatrix[i,j] = distance
                #The matrix is simetrical, so we need to fill the reflected side too
                placesDistanceMatrix[j,i] = distance

        self.placesDistanceMatrix = placesDistanceMatrix

        if(plotDistances):
            fig, ax = plt.subplots(figsize = (7,7))
            im = ax.imshow(self.placesDistanceMatrix)
            ax.set_xticks(np.arange(len(layerNames)), labels = layerNames)
            ax.set_yticks(np.arange(len(layerNames)), labels = layerNames)
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
            for i in range(np.size(placesDistanceMatrix, 0)):
                for j in range(np.size(placesDistanceMatrix,1)):
                    text = ax.text(j, i, str(np.round(self.placesDistanceMatrix[i, j],1)), ha="center", va="center", color="w")

            ax.set_title("Mean distance (m)")
            plt.savefig(os.path.join(resultsPath,'distance_matrix.pdf'), dpi = 600, bbox_inches = 'tight')
            
        return layerNames, self.placesDistanceMatrix


    def writeReport(self, title, author, date, chunks, resultsPath):
        '''
        Right now i want to write the chunks manually since i want to write observations about the particular results.
        However, this could be made automatic in the future. I have to say that it is very much automatic in the sense that
        it can construct the document latex and handle its structure in a seamless systematic way. 
        '''
        from ReportTools import ReportCreator

        self.report = ReportCreator(title, author, date)
        nChunks = len(chunks)
        for i in range(0,nChunks):
            chunk = chunks[i]
            self.report.addResultFromChunk(chunk)
        self.report.export(resultsPath, "report")