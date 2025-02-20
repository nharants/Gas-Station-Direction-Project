# Nate Harants 2/8/2025
import requests
import googlemaps
import polyline
from haversine import haversine, Unit
key = 'insert key here'

#project created to learn usage of google maps API's, including directions, distancematrix, geocoding, and places.

# uses the google geodata api to convert address to Latitude and Longitude
def AddresstoLocation(address):
    geoUrl = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        "address": address,

        "key": key
    }

    response = requests.get(geoUrl, params)
    if (response.status_code == 200):
        geodata = response.json()
        latlot = geodata["results"][0]["geometry"]["location"]

        lat = latlot["lat"]
        lot = latlot["lng"]
        return lat, lot

    else:
        print("Failed :(\n")
        return 0


def TravelDistance(start, destination):
    disturl = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": start,
        "destinations": destination,
        "units": "imperial",
        "key": key
    }

    response = requests.get(disturl, params)
    if response.status_code == 200:
        data = response.json()

        if data["status"] == "OK":
            distance = data["rows"][0]["elements"][0]["distance"]["text"]
            duration = data["rows"][0]["elements"][0]["duration"]["text"]

            return distance, duration

        else:
            print(data["status"])
            return 0
    else:
        print("no response :(\n")
        return 0

#Uses the google directions api to get step by step directions, also returns a series of coordinates
#along the path of the trip which can be used to find nearby services at any point in the trip.
def Directions(start, destination):
    DirUrl = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": start,
        "destination": destination,
        "key": key
    }
    #sends an http request and unpacks the contents f the response to get the polyline
    response = requests.get(DirUrl, params)
    data = response.json()
    routes = (data["routes"])
    routess = routes[0]

    legs = routess["legs"][0]
    polylinee = routess["overview_polyline"]
    polystring = polylinee["points"]
    #decodes polyline into its constituent coordinates
    coords = polyline.decode(polystring)

    #creats a companion list that stores the totaldistance between at each coordinates
    #the indexs of this list match the indexes of the cooridnates
    distancepoints = []
    distancepoints.append(0)
    y = 1
    totaldist=0
    while y < len(coords):
        #uses the haversine formula to compute distance betwene each coord and adds it to the total, calling the google api for each coordinate
        #would be insanely inefficient and expensive, I'm not that amateurish :)
        distpoint = haversine(coords[y-1], coords[y], unit=Unit.MILES)
        totaldist+=distpoint
        distancepoints.append(totaldist)

        y= y+1


    steps = legs["steps"]
    totaldist = 0
    directionsteps = []
    for step in steps:
        currentstep = ()

        ycurrentstep = list(currentstep)
        ycurrentstep.append(step["html_instructions"])
        dist = step["distance"]

        disttext = dist["text"]
        parts = disttext.split(" ", 1)
        distnum = float(parts[0])
        unit = parts[1]
        # if in feet, convert to miles
        if unit == "ft":
            distnum = distnum / 5280
        totaldist = totaldist +distnum
        dur = (step["duration"])

        ycurrentstep.append(disttext)
        ycurrentstep.append(dur)
        ycurrentstep.append(totaldist)
        currentstep = tuple(ycurrentstep)

        directionsteps.append(currentstep)

    return directionsteps, coords, distancepoints
#helper function to find index of clcsest number in list
def findcloseindex(list, num):
    closest_index = 0
    closest_diff = abs(list[0] -num)

    for i in range(1, len(list)):
        current_diff = abs(list[i]-num)
        if current_diff < closest_diff:
            closest_diff = current_diff
            closest_index = i
    return closest_index


# takes a startpoint, end point, mileage range, and buffer zone and returns
# directions with recommended points in the trip to stop for gas, as well as
# gas stations near that point
def FindGasStations(Start, End, range, buffer):
    base_url = 'https://places.googleapis.com/v1/places:searchNearby'
    TotalDistance = TravelDistance(Start, End)
    TotalDistNum = TotalDistance[0]
    TotalDistNum = int(TotalDistNum.replace(" mi", "").replace(",",""))

    Directionss, coords, distancecheckpoints = Directions(Start, End)
    # using the range, buffer, and totaldistance, of the journey, determine at what
    # miles there should be a stop for a gas.

    # do a places search for gas stations near each one.
    #takes into account buffer to find when you should stop for gas, IE how much gas you should have left at that point.
    #totoldistance by range to get the number of stops
    travelrange = (range - buffer)
    stopmilepoints = []
    print(TotalDistNum/travelrange)
    numofstops = int(TotalDistNum/travelrange)
    print(numofstops)

    i = 1
    #determining what mile markers you should stop for gas
    while i <=numofstops:
        stopmilepoints.append(travelrange*i)
        i=i+1


    stopindexes=[]
    #finds the index of the distance checkpoint closest to the stop
    for s in stopmilepoints:
        index = findcloseindex(distancecheckpoints,s)
        stopindexes.append(index)

    stopcoordinates = []
    #uses this index to pull the closest point on the travel path to
    #the suggested path, this will be used to find nearby gas stations.
    for i in stopindexes:
        stopcoord = coords[i]
        stopcoordinates.append(stopcoord)

    #finds nearby gas stations within a 5 mile radius of each stopping point
    datas = []
    for s in stopcoordinates:
        latitude = s[0]
        longitude = s[1]
        #preparing the POST request for the places api
        headers = {
            'Content_type': 'application/json; charset=utf-8',
            'X-Goog-Api-Key':key,
            'X-Goog-FieldMask': 'places.displayName,places.id,places.types,places.formattedAddress,places.priceLevel,places.userRatingCount,places.rating'
        }
        data = {

            'includedTypes':["gas_station"],
            "maxResultCount" : 10,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                    #roughly 5 miles
                    "radius": 32000.0
                }

            }

        }

        response = requests.post(base_url, headers = headers, json = data)
        if response.status_code == 200:
            data = response.json()
            datas.append(data)
        else:
            print(f'Error: {response.status_code} - {response.text}')
    Gstations = []
    for d in datas:
        addresses = []
        for p in d["places"]:
            disp = p["displayName"]
            disptext = disp["text"]
            add = p["formattedAddress"]

            addresses.append(disptext + ", " + add)
        Gstations.append(addresses)

    return Directionss, stopcoordinates, stopmilepoints, Gstations


        
if __name__ == '__main__':
    address1 = "Fort Wayne, Indiana"
    address2 = "Colorado Springs, Colorado"
    #find directions between address1 and addrees 2 with a mileage of 200 miles and a buffer zone of 40 miles
    Steps, stopcoords, milemarks,gasstations = FindGasStations(address1, address2, 200, 40)
    #prints directions
    for s in Steps:
        print(s)
        print('\n')

    print(len(milemarks))
    print(len(gasstations))
    j=0
    #shows suggested mile markers for stopping for gas and returns gas stations within a 20 miles radius of the suggested point
    while j< len(milemarks):
        print("stop for gas at " + str(milemarks[j]) +" Miles")
        print("nearby gas stations:")
        print(gasstations[j])
        print("\n")

        j = j+1





