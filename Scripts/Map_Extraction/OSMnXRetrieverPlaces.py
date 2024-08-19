from enum import Enum
import osmnx as ox
import logging
import os

class PlaceType(Enum):
    PARKS = "parks"
    AMENITIES = "amenities"
    BUS_STOPS = "bus_stops"
    SCHOOLS = "schools"
    JOB_CENTRES = "job_centres"
    INSTITUTIONS = "institutions"
    HOMES = "homes"
    CENSUS_BLOCK = "census_block"
    SUBWAY = "subway"
    
    
    

class OSMnXRetrieverPlaces:


    def __init__(self):
        self.crs = "EPSG:4326"

    def getTags(self, placeType):
        tags = -1
        if(placeType == PlaceType.PARKS):
            tags = {"leisure":"park"}

        elif(placeType == PlaceType.SCHOOLS):
            tags = {"amenity":["school", "university", "college"]}

        elif(placeType == PlaceType.AMENITIES):
            tags = {"amenity":True}
        
        elif(placeType == PlaceType.BUS_STOPS):
            tags = {"highway":"bus_stop"}

        elif(placeType == PlaceType.JOB_CENTRES):
            tags = {"amenity":"jobcentre", "office": True}
            
        elif(placeType == PlaceType.INSTITUTIONS):
            tags = {"landuse":"institutional", "office":["government", "ngo", "association"],"amenity":"social_facility"}
            
        elif(placeType == PlaceType.HOMES):
            tags = {"building":["house", "apartments", "detached", "terrace", "semidetached_house", "hut", "ger", "houseboat", "static_caravan"]}
            
        elif(placeType == PlaceType.SUBWAY):
            tags = {"railway":"station"}

        elif(placeType == PlaceType.CENSUS_BLOCK):
            tags = {"boundary":"census"}

        return tags
        


    def getFeaturesFromPoint(self, latitude, longitude, radius, placeType):
        logging.captureWarnings(True)
        tags = self.getTags(placeType)
        try:
            gdf = ox.features_from_point((latitude, longitude), tags, dist = radius)
            gdf['geometry'] = gdf['geometry'].to_crs(self.crs).centroid
            return gdf
        except:
            print("No features found")
            return None

    def getFeaturesFromPlace(self, country, state, city, placeType):
        tags = self.getTags(placeType)
        place = {"city": city, "state": state, "country":country}
        try:
            gdf = ox.features_from_place(place, tags)
            gdf['geometry'] = gdf['geometry'].to_crs(self.crs).centroid
            return gdf
        except:
            print("No features found")
            return None

    def cleanDataFrame(self, dataFrame):

        keys = dataFrame.keys()
        element = -1
        for i in range(0,len(keys)):
            key = keys[i]
            subKeys = dataFrame[key].keys()
            for j in range(0,len(subKeys)):
                subKey = subKeys[j]
                if(type(dataFrame[key][subKey]) is list):
                    dataFrame.loc[subKey, key] = str(dataFrame.loc[subKey, key])
        return dataFrame

    def exportGeoJSON(self, gdf, path):

        cleanedDataFrame = self.cleanDataFrame(gdf)
        cleanedDataFrame.to_file(path, driver = 'GeoJSON')

        print('Exported Geojson')


    def exportAllFromPoint(self, parentPath, latitude, longitude, radius):
        placeTypes = [e for e in PlaceType]
        for i in range(0,len(placeTypes)):
            placeType = placeTypes[i]
            gdf = self.getFeaturesFromPoint(latitude, longitude, radius, placeType)
            if(not gdf is None):
                gdf = gdf[['geometry']]

                if(not os.path.exists(parentPath)):
                    os.mkdir(parentPath)
                
                self.exportGeoJSON(gdf, parentPath + "/"+placeType.value+".geojson")
        

    
        

    
            
            
            
    




    