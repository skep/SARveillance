import os

import ee
import matplotlib.pyplot as plt
from geemap import png_to_gif
from geemap.cartoee import add_gridlines, get_map
from lib import utils


class SAR_URBAN:

  def __init__(self, mode='S1', name='custom', coordinates=[0, 0], date_from=None, date_to=None, out_dir=None):
    self.mode = mode
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
    print('')
    print('AOI: ',self.name)
    print('')

    # region formats
    self.region = utils.create_point_buffer_region(self.coordinates)
    self.region_eswn = utils.create_point_eswm_region(self.coordinates)

    # find a cloudless basemap based on
    # Sentinel-2 images
    if self.mode == 's2':
      self.find_basemap_image()

    # download base image
    # self.download_base_image()

    # find sentinel-1 images
    self.find_s1_images()

    # download sentinel-1 images
    self.download_s1_images()

    # generate gif
    self.generate_gif()


  def find_basemap_image(self):
    '''
    return a (mostly) cloundless & recent Sentinel-2 ee.Image
    '''
    cloudy_pixel_threshold = 5
    search_days = [30, 60, 90, 120, 150, 180]

    print('##### SENTINEL-2 #####')

    # loop over date ranges to find the most recent image
    # TODO: move the range in steps of <days> to only search
    # in a fresh date range
    for days in search_days:

      # get the date range
      date_from, date_to = utils.recent_date_range(days)
      print(f'+ Search between {date_from} and {date_to}')

      # from collection COPERNICUS/S2_SR
      # filter by date range
      # filter by region bounds
      # filter by fully region coverage
      # clip region from images
      # filter by cloudy pixel percentage lower than <threshold>
      # sort by cloudy pixel percentage
      # select/filter needed bands
      collection = ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterDate(date_from, date_to) \
        .filterBounds(self.region) \
        .filter(ee.Filter.contains('.geo', self.region)) \
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
      print(f'+ Found {image_count} images between {date_from} and {date_to}')

    # select first image from collection
    base_image = collection.first()

    date = base_image.get("system:time_start")
    date = ee.Date(date).format('YYYY-MM-dd').getInfo()
    print(f'-> Use Sentinel-2 image from {date}')
    print('')

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

    # date of image
    date = self.base_image.get("system:time_start")
    date = ee.Date(date).format('YYYY-MM-dd').getInfo()
    sod = self.base_image.get("SENSING_ORBIT_DIRECTION").getInfo()
    print(sod)

    # file name + file path
    image_name = 'base_image.png'
    out_path = outPath = os.path.join(poi_out_dir, image_name)

    # download image
    fig = plt.figure(figsize=(10, 10), dpi=100)
    ax = get_map(self.base_image, region=self.region_eswn, vis_params=vis_params)

    add_gridlines(ax, interval=(0.2, 0.2), linestyle=":")
    ax.set_title(label=date, fontsize=10, loc='left')
    ax.set_title(label=self.name, fontsize=15, loc='center')
    ax.set_title(label=sod, fontsize=10, loc='right')

    progressbar_base = utils.create_progressbar_reactangle(self.region_eswn, color='white', percentage=100)
    progressbar_image = utils.create_progressbar_reactangle(self.region_eswn, color='#037ffc', percentage=50)
    # Add progress bar to axes
    ax.add_patch(progressbar_base)
    ax.add_patch(progressbar_image)



    fig.tight_layout()

    plt.savefig(fname=out_path, transparent=False)
    plt.clf()
    plt.close()
    

  def find_s1_images(self):
    '''
    find all sentinel-1 images for the given region and date range
    '''

    print('##### SENTINEL-1 #####')

    # if one of the date is undefined, search within the past week
    if self.date_from == None or self.date_to == None:
      self.date_from, self.date_to = utils.recent_date_range(days=14, format='%Y-%m-%d')
    else:
      self.date_from, self.date_to = utils.fix_date_range(self.date_from, self.date_to)

    print(f'+ Search between {self.date_from} and {self.date_to}')


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
    # print(minmax)

    # final image count check
    image_count = int(collection.size().getInfo())
    if image_count == 0:
      print('Could not find sentinel-1 images')
      return
    else:
      print(f'-> Found {image_count} images')
      print('')


    # create new bands, based an computations of value in VV & VH bands
    def _urban_mode(image):
      if self.mode == 'S1':
        r = image.expression("7 * VH > 0.5", { 'VH': image.select('VH')}).rename('R')
        g = image.expression("2 * VV", { 'VV': image.select('VV')}).rename('G')
        b = image.expression("8 * VH", { 'VH': image.select('VH')}).rename('B')
      elif self.mode == 'S2':
        r = image.expression("5.5 * VH > 0.5", { 'VH': image.select('VH')}).rename('R')
        # g = image.expression("1 * VV", { 'VV': image.select('VV')}).rename('G')
        g = image.select('VV').rename('G')
        b = image.expression("8 * VH", { 'VH': image.select('VH')}).rename('B')
      return image.addBands([r,g,b])
    collection = collection.map(_urban_mode)

    # remove now unused vv & vh bands
    collection = collection.select(['R', 'G', 'B'])

    self.s1_collection = collection


  def download_s1_images(self):
    '''
    downloads all found sentinel-1 images
    '''

    vis_params_s2 = {
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

    vis_params_s1 = {
      'bands': ['R', 'G', 'B'],
      'region': self.region,
      'format': 'png',
      'opacity': 1,
      # 'min': 0,
      # 'max': 1,
      'gamma': 0.9
    }
    vis_params_s1_s2 = {
      'bands': ['R', 'G', 'B'],
      'region': self.region,
      'format': 'png',
      'opacity': 0.8,
      'min': 0.25,
      'max': 1
    }    

    dates = self.s1_collection.aggregate_array("system:time_start")
    dates = dates.map(lambda d: ee.Date(d).format('YYYY-MM-DD')).getInfo()
    images = self.s1_collection.toList(self.s1_collection.size())

    size = self.s1_collection.size().getInfo()

    print('##### GENERATE IMAGES #####')

    for i, date in enumerate(dates):

      print(f'+ {date}...')

      image_name = f'{str(i).zfill(3)}_{date}.png'
      image = ee.Image(images.get(i))
      out_path = outPath = os.path.join(poi_out_dir, image_name)

       # apply a mask for all darker, low intensity signals
      if self.mode == 'S2':
        mask_threshold = 0.25
        mask = image.reduce(ee.Reducer.mean()).gt(mask_threshold)
        image = image.updateMask(mask)

      # image props
      sod = image.get("orbitProperties_pass").getInfo()
      platform = image.get("platform_number").getInfo()     

      if self.mode == 'S2':
        fig, ax1 = plt.subplots(1, 1, figsize=[10,10], dpi=100)
        plt.axis('off')
        fig, ax2 = plt.subplots(1, 1, figsize=[10,10], dpi=100)
        plt.axis('off')
        ax1 = get_map(self.base_image, region=self.region_eswn, vis_params=vis_params_s2)
        ax2 = get_map(image, region=self.region_eswn, vis_params=vis_params_s1_s2)
        # add gridlines to Sentinel-1 image
        add_gridlines(ax2, interval=(0.2, 0.2), linestyle=":")
        # set title, name and metadata
        ax2.set_title(label=date, fontsize=10, loc='left')
        ax2.set_title(label=self.name, fontsize=15, loc='center')
        ax2.set_title(label=f'S-1{platform} / {sod}', fontsize=10, loc='right')
        # progressbar
        percentage = ((i + 1) / size) * 100
        # print(percentage, '%')
        progressbar_base = utils.create_progressbar_reactangle(self.region_eswn, color='white', percentage=100)
        progressbar_image = utils.create_progressbar_reactangle(self.region_eswn, color='#037ffc', percentage=percentage)
        # Add progress bar to axes
        ax2.add_patch(progressbar_base)
        ax2.add_patch(progressbar_image)
        # tight layout
        fig.tight_layout()
        # save image
        plt.savefig(fname=out_path, transparent=True)
        plt.clf()
        plt.close(fig)        

      elif self.mode == 'S1':

        fig = plt.figure(figsize=[10,10], dpi=100)
        plt.axis('off')
        ax = get_map(image, region=self.region_eswn, vis_params=vis_params_s1)
        # add gridlines to Sentinel-1 image
        add_gridlines(ax, interval=(0.2, 0.2), linestyle=":")
        # set title, name and metadata
        ax.set_title(label=date, fontsize=10, loc='left')
        ax.set_title(label=self.name, fontsize=15, loc='center')
        ax.set_title(label=f'S-1{platform} / {sod}', fontsize=10, loc='right')
        # progressbar
        percentage = ((i + 1) / size) * 100
        progressbar_base = utils.create_progressbar_reactangle(self.region_eswn, color='white', percentage=100)
        progressbar_image = utils.create_progressbar_reactangle(self.region_eswn, color='#037ffc', percentage=percentage)
        # Add progress bar to axes
        ax.add_patch(progressbar_base)
        ax.add_patch(progressbar_image)
        # tight layout
        fig.tight_layout()
        # save image
        plt.savefig(fname=out_path, transparent=True)
        plt.clf()
        plt.close(fig)



  def generate_gif(self):
    fps = 1
    loop = 0
    in_dir = os.path.join(self.out_dir, self.name)
    out_dir = os.path.join(self.out_dir, self.name, 'gif')
    if not os.path.exists(out_dir):
      os.makedirs(out_dir)
    out_file = f'{self.name}.gif'
    out_gif = os.path.join(out_dir, out_file)
    png_to_gif(in_dir, out_gif, fps, loop)









