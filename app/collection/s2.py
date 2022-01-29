import ee

from utils.dates import get_date_range


def get_base_image(region, range):
  '''
  returns a sentinel-2 collection
  '''


    s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterDate(start_date, end_date) \
    .filterBounds(region) \
    .map(lambda image: image.clip(region)) \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
    .sort('CLOUDY_PIXEL_PERCENTAGE', False) \
    .select(['B4', 'B3', 'B2'])