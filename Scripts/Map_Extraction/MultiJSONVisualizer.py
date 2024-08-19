from .GeoJSONHandler import GeoJSONOpener
import matplotlib.pyplot as plt
import matplotlib.patches as patches


class GeoJSONLayer:


    def __init__(self, path, layerId, color, pointLayer = True):
        self.handler = GeoJSONOpener(path)
        self.layerId = layerId
        self.color = color
        self.pointLayer = pointLayer

        self.visualizationGraph = self.handler.getVisualizationGraph()

    def setEdgeSize(self, edgeSize):
        self.handler.setEdgeSize(edgeSize)

    def setNodeSize(self, nodeSize):
        self.handler.setNodeSize(nodeSize)

    def drawLayer(self, ax):
        if(self.pointLayer):
            self.handler.drawMap(ax, self.visualizationGraph, nodeColor = self.color, edgeColor = self.color, drawNodes = True, drawEdges = False)
        else:
            self.handler.drawMap(ax, self.visualizationGraph, nodeColor = self.color, edgeColor = self.color, drawNodes = False, drawEdges = True)

    def __eq__(self, other):
        return self.layerId == other.layerId

    def getMainColor(self):
        return self.color

class MultiGeoJSONVisualizer:


    def __init__(self):
        self.layers = []
        
    def addLayer(self, layerId, path, color, pointLayer = True):

        layer = GeoJSONLayer(path, layerId, color, pointLayer)
        if(not layer in self.layers):
            self.layers.append(layer)

    def getLayer(self, layerId):
        for i in range(0,len(self.layers)):
            layer = self.layers[i]
            if(layer.layerId == layerId):
                return layer


    def setNodeSizeForAll(self, nodeSize):
        nLayers = len(self.layers)
        for i in range(0,nLayers):
            self.layers[i].setNodeSize(nodeSize)

    def setEdgeSizeForAll(self, edgeSize):
        nLayers = len(self.layers)
        for i in range(0,nLayers):
            self.layers[i].setEdgeSize(edgeSize)


    def setNodeSizeLayer(self, layerId, nodeSize):
        self.getLayer(layerId).setNodeSize(nodeSize)

    def setEdgeSizeLayer(self, layerId, edgeSize):
        self.getLayer(layerId).setEdgeSize(edgeSize)

    def getLayerNames(self):
        layerNames = []
        for i in range(0,len(self.layers)):
            layerName = self.layers[i].layerId
            layerNames.append(layerName)

        return layerNames
        
        

    
    def drawMultiLayer(self, layerNames, width = 5, height = 5):
        fig, ax = plt.subplots(figsize = (width, height))
        layerPatches = []
        for i in range(0,len(layerNames)):
            layerId = layerNames[i]
            layer = self.getLayer(layerId)
            layer.drawLayer(ax)
            layerPatch = patches.Patch(color=layer.getMainColor(), label=layer.layerId)
            layerPatches.append(layerPatch)
            #ax.add_patch(layerPatch)

        ax.legend(handles = layerPatches, loc = 'upper right')
        
            
        
            