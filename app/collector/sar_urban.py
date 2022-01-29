import os

import ee
import matplotlib.pyplot as plt
from geemap.cartoee import (add_gridlines, add_north_arrow, add_scale_bar_lite,
                            get_map, get_image_collection_gif, pad_view)
from lib import utils


class SAR_URBAN:

  def __init__(self, name='custom', coordinates=[0, 0], date_from=None, date_to=None, out_dir=None):
    self.name = name
    self.coordinates = coordinates
    self.date_from = date_from
    self.date_to = date_to
    self.out_dir = out_dir

    # internal vars
    self.region = None
    self.region_eswn = None
    self.base_image = None
    self.s1_collection = None


  def run(self):
    '''
    creates sar urban images
    '''
    
    # region formats
    self.region = utils.create_point_buffer_region(self.coordinates)
    self.region_eswn = utils.create_point_eswm_region(self.coordinates)

    # find a cloudless basemap based on
    # Sentinel-2 images
    self.find_basemap_image()

    # download base image
    # self.download_base_image()

    # find sentinel-1 images
    self.find_s1_images()

    # download sentinel-1 images
    self.download_s1_images()



  def find_basemap_image(self):
    '''
    return a (mostly) cloundless & recent Sentinel-2 ee.Image
    '''
    cloudy_pixel_threshold = 10
    search_days = [30, 60, 90, 120, 150, 180]

    # loop over date ranges to find the most recent image
    # TODO: move the range in steps of <days> to only search
    # in a fresh date range
    for days in search_days:

      # get the date range
      date_from, date_to = utils.recent_date_range(days)
      print(f'Search base image in range: {date_from} - {date_to}')

      # from collection COPERNICUS/S2_SR
      # filter by date range
      # filter by region bounds
      # clip region from images
      # filter by cloudy pixel percentage lower than <threshold>
      # sort by cloudy pixel percentage
      # select/filter needed bands
      collection = ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterDate(date_from, date_to) \
        .filterBounds(self.region) \
        .map(lambda image: image.clip(self.region)) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloudy_pixel_threshold)) \
        .sort('CLOUDY_PIXEL_PERCENTAGE', False) \
        .select(['B4', 'B3', 'B2'])

      # count images in collection
      # if 0, increase the range
      image_count = int(collection.size().getInfo())
      if image_count == 0:
        continue
      else:
        break

    # final image count check
    image_count = int(collection.size().getInfo())
    if image_count == 0:
      print('Could not find a cloudless base image')
      # TODO: use alternative base image or background
      return
    else:
      print(f'Found {image_count} images within date range')

    # select first image from collection
    base_image = collection.first()

    # populate class vars
    self.base_image = base_image


  def download_base_image(self):
    '''
    downloads the base image
    '''

    # poi download folder, create if not exist
    if self.out_dir is None:
      self.out_dir = os.path.join(os.getcwd(), 'downloads')
    poi_out_dir = os.path.join(self.out_dir, self.name)
    if not os.path.exists(poi_out_dir):
      os.makedirs(poi_out_dir)

    # visualization params
    # TODO: ideal gamma value
    vis_params = {
      'bands': ['B4', 'B3', 'B2'],
      'region': self.region,
      'format': 'png',
      'gamma': 3.0,
      'crs': "EPSG:4326",
    }

    # file name + file path
    image_name = 'base_image.png'
    out_path = outPath = os.path.join(poi_out_dir, image_name)

    # download image
    fig = plt.figure(figsize=(10, 10), dpi=100)
    ax = get_map(self.base_image, region=self.region_eswn, vis_params=vis_params)

    add_gridlines(ax, interval=(0.2, 0.2), linestyle=":")
    ax.set_title(label=self.name, fontsize=15, loc='center')

    fig.tight_layout()

    plt.savefig(fname=out_path, transparent=False)
    plt.clf()
    plt.close()
    

  def find_s1_images(self):
    '''
    find all sentinel-1 images for the given region and date range
    '''

    # if one of the date is undefined, search within the past week
    if self.date_from == None or self.date_to == None:
      self.date_from, self.date_to = utils.recent_date_range(days=14, format='%Y-%m-%dT00:00:00')

    print(f'Search Sentinel-1 image in range: {self.date_from} - {self.date_to}')

    # from collection COPERNICUS/S1_GRD_FLOAT
    # filter by date range
    # filter by region bounds
    # filter by transmitterReceiverPolarisation for VV & VH
    # filter by instrument mode = IW
    # filter by bands
    # clip region from images
    collection = ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT') \
      .filterDate(self.date_from, self.date_to) \
      .filterBounds(self.region) \
      .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
      .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
      .filter(ee.Filter.eq('instrumentMode', 'IW')) \
      .select(['VV', 'VH']) \
      .map(lambda image: image.clip(self.region))

    minmax = collection.first().reduceRegion(ee.Reducer.minMax(), self.region).getInfo()
    print(minmax)

    # final image count check
    image_count = int(collection.size().getInfo())
    if image_count == 0:
      print('Could not find sentinel-1 images')
      return
    else:
      print(f'Found {image_count} images within date range')


    # create new bands, based an computations of value in VV & VH bands
    def _urban_mode(image):
      r = image.expression("(VH > 0.1) ? 5.5 * VH : 0", { 'VH': image.select('VH')}).rename('R')
      g = image.expression("(VV > 0.3) ? VV : 0", { 'VV': image.select('VV')}).rename('G')
      b = image.expression("(VH > 0.2) ? 8 * VH : 0", { 'VH': image.select('VH')}).rename('B')
      return image.addBands([r,g,b])
    collection = collection.map(_urban_mode)

    # minmax = collection.first().reduceRegion(ee.Reducer.minMax(), self.region).getInfo()
    # print(minmax)

    # remove now unused vv & vh bands
    collection = collection.select(['R', 'G', 'B'])


    self.s1_collection = collection


  def download_s1_images(self):
    '''
    downloads all found sentinel-1 images
    '''

    vis_params2 = {
      'bands': ['B4', 'B3', 'B2'],
      'region': self.region,
      'format': 'png',
      'gamma': 3.0,
    }

    # poi download folder, create if not exist
    if self.out_dir is None:
      self.out_dir = os.path.join(os.getcwd(), 'downloads')
    poi_out_dir = os.path.join(self.out_dir, self.name)
    if not os.path.exists(poi_out_dir):
      os.makedirs(poi_out_dir)

    # visualization params
    # TODO: ideal gamma value

    vis_params = {
      # 'bands': ['R', 'G', 'B'],
      'bands': ['sum'],
      'region': self.region,
      'format': 'png',
      # 'crs': "EPSG:4326",
      # 'min': 0,
      # 'max': 1,
      #'palette': ['#ed6900', '#ff00f6'],
      'palette': ['#6d0072','#910091','#b500b2','#da00d3','#ff00f6'],
      'opacity': 0.8
    }

    dates = self.s1_collection.aggregate_array("system:time_start")
    dates = dates.map(lambda d: ee.Date(d).format('YYY-MM-DD')).getInfo()
    images = self.s1_collection.toList(self.s1_collection.size())

    for i, date in enumerate(dates):
      image_name = f'{str(i).zfill(3)}_{date}.png'
      image = ee.Image(images.get(i))
      out_path = outPath = os.path.join(poi_out_dir, image_name)

       # merge bands
      sum = image.reduce(ee.Reducer.sum())
      mask = sum.reduce(ee.Reducer.sum()).gt(0.01)

      sum = sum.updateMask(mask)
      # print(sum.bandNames().getInfo())
      print(date)


      fig, ax1 = plt.subplots(1, 1, figsize=[10,10], dpi=100)
      plt.axis('off')
      fig, ax2 = plt.subplots(1, 1, figsize=[10,10], dpi=100)
      plt.axis('off')
      ax1 = get_map(self.base_image, region=self.region_eswn, vis_params=vis_params2)
      ax2 = get_map(sum, region=self.region_eswn, vis_params=vis_params)

      add_gridlines(ax2, interval=(0.2, 0.2), linestyle=":")
      ax1.set_title(label=self.name, fontsize=15, loc='left')
      ax2.set_title(label=date, fontsize=15, loc='right')

      fig.tight_layout()

      plt.savefig(fname=out_path, transparent=True)
      plt.clf()
      plt.close()











