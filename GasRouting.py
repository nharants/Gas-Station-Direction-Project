# Nate Harants 2/8/2025
import requests
import googlemaps
import polyline
from haversine import haversine, Unit
key = '????'


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
        print("Shit don't work slime :(\n")
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
#helper function to find index of lcosest number in list
def findcloseindex(list, num):
    closest_index = 0
    closest_diff = abs(list[0] -num)

    for i in range(1, len(list)):
        current_diff = abs(list[i]-num)
        if current_diff < closest_diff:
            closest_diff = current_diff
            closest_index = i
    return closest_index



def FindGasStations(Start, End, range, buffer):
    base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    TotalDistance = TravelDistance(Start, End)
    TotalDistNum = TotalDistance[0]
    TotalDistNum = int(TotalDistNum.replace(" mi", "").replace(",",""))

    Directionss, coords, distancecheckpoints = Directions(Start, End)
    # using the range, buffer, and totaldistance, of the journey, determine at what
    # miles there should be a stop for a gas.

    # do a places search for gas stations near each one.
    #takes into account buffer to find when you should stop for gas
    #totoldistance by range to get the number of stops
    travelrange = (range - buffer)
    stopmilepoints = []
    numofstops = int(TotalDistNum/travelrange)


    i = 1
    while i <numofstops:
        stopmilepoints.append(travelrange*i)
        i=i+1

    print(stopmilepoints)
    stopindexes=[]
    for s in stopmilepoints:
        index = findcloseindex(distancecheckpoints,s)
        stopindexes.append(index)
    print(stopindexes)
    stopcoordinates = []
    for i in stopindexes:
        stopcoord = coords[i]
        stopcoordinates.append(stopcoord)
    print(stopcoordinates)


if __name__ == '__main__':
    address1 = "9211  Springbreeze court, Fort Wayne Indiana"
    address2 = "53 Wolfs Head Drive, Coaldale Colarado"
    latlong = AddresstoLocation(address2)
    Directions(address1, address2)
    FindGasStations(address1, address2, 200, 40)



