import ee 
from datetime import date, datetime, timedelta
from matplotlib.patches import Rectangle


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
  date_from = (date_to - timedelta(days=days)).strftime('%Y-%m-%dT00:00:00')
  date_to = date_to.strftime('%Y-%m-%dT23:59:59')
  return date_from, date_to

def fix_date_range(date_from, date_to):
  # first convert string to datetime obj
  date_from = datetime.strptime(date_from, "%Y-%m-%d")
  date_to = datetime.strptime(date_to, "%Y-%m-%d")
  # set times
  date_from = date_from.strftime('%Y-%m-%dT00:00:00')
  date_to = date_to.strftime('%Y-%m-%dT23:59:59')
  return date_from, date_to


def create_progressbar_reactangle(region_eswn, color='white', percentage=100):
    # Create a Rectangle patch
  [e,s,w,n] = region_eswn
  reactangle_width = abs(e-w) / 100 * percentage
  reactangle_height = 0.005 # depends on the r-value of create_point_eswm_region()
  return Rectangle((w,s),reactangle_width,reactangle_height,color=color,zorder=10)

