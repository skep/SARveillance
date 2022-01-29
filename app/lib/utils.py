import ee 
from datetime import date, timedelta


def create_point_buffer_region(coordinates, meter=3000):
    '''
    returns an ee region
    '''
    [lat, lon] = coordinates
    point = ee.Geometry.Point([float(lon), float(lat)]) # creates an ee geometry from a point
    buffer = point.buffer(3000) # expand the geometry by a given distance (in meter)
    region = buffer.bounds() # the bounding box of the buffer

    return region

def create_point_eswm_region(coordinates, r=0.4):
  '''
  returns an geospatial region in format [E,S,W,N]
  '''
  # geospatial region in format [E,S,W,N] from a given point o (lat,lon)
  #          (lat+r)    
  #             N
  #
  # (lon-r) W   o   E (lon+r)
  #  
  #             S
  #          (lat-r)
  [lat, lon] = coordinates
  region_eswn = [lon+r, lat-r, lon-r, lat+r]

  return region_eswn


def recent_date_range(days=90, format='%Y-%m-%d'):
  '''
  returns 2 formatted date for a given range
  date_to is always <today>
  date_from is <today> minus <days> days
  '''
  date_to = date.today()
  date_from = (date_to - timedelta(days=days)).strftime(format)
  date_to = date_to.strftime(format)
  return date_from, date_to


