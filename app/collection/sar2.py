import os
from datetime import date, timedelta

import ee
import geemap as gee
import matplotlib.pyplot as plt
from geemap.cartoee import (add_gridlines, add_north_arrow, add_scale_bar_lite,
                            get_map, get_image_collection_gif, pad_view)
from PIL import Image
import numpy as np


def sar(name='custom', coordinates=(0, 0)):

  # set date range
  # s1_start_date, s1_end_date = set_s1_date_range()
  s2_start_date, s2_end_date = set_s2_date_range()
  print(s2_start_date, s2_end_date)


  # set region from pair of coordinates
  region = set_region(coordinates)
  region_reactangle = create_region_rectangle(coordinates)
  print(region_reactangle)

  # create download folder
  download_folder = create_download_folder(name)


  # get base image data (Sentinel-2)
  base_image_data = get_base_image(region, s2_start_date, s2_end_date)
  download_images(base_image_data, region_reactangle, download_folder)

  pass





def set_s1_date_range(start_date=None, end_date=None):
  # default start/end date
  today = date.today()
  last_week = today - timedelta(days=5)
  last_quarter = today - timedelta(days=90)
  # set start/end date
  start_date = last_week if end_date is None else end_date
  end_date = today if start_date is None else start_date
  end_date2 = last_quarter
  # format to zero hours, minutes, seconds
  start_date = start_date.strftime('%Y-%m-%dT00:00:00')
  end_date = end_date.strftime('%Y-%m-%dT00:00:00')
  end_date2 = end_date2.strftime('%Y-%m-%dT00:00:00')
  return start_date, end_date, end_date2

def set_s2_date_range():
  # range: 90 days ago till today
  end_date = date.today()
  start_date = end_date - timedelta(days=90)
  # format to zero hours
  end_date = end_date.strftime('%Y-%m-%d')
  start_date = start_date.strftime('%Y-%m-%d')  
  return start_date, end_date


def set_region(coordinates):
  (lat, lon) = coordinates
  point = ee.Geometry.Point([float(lon), float(lat)])
  buffer = point.buffer(3000) # define a circle around the point
  region = buffer.bounds() # bound around that circle
  return region

def create_region_rectangle(coordinates):
    (lat, lon) = coordinates
    r = 0.4
    return [lon+r, lat-r, lon-r, lat+r]

def create_download_folder(name):
  outFolder = os.path.join(os.getcwd(), 'Downloads', name)
  if not os.path.exists(outFolder):
    os.makedirs(outFolder)
  return outFolder

def download_images(image_data, region, download_folder):
  print('Download Sentinel-2 Base Image')
  visParams = image_data['visParams']
  for data in image_data['images']:
    image_name = data['name']
    outPath = os.path.join(download_folder, image_name)
    print(outPath)
    image = data['image']
    plt.figure(figsize=(10, 10), dpi=100)
    ax = get_map(image, region=region, vis_params=visParams)
    plt.savefig(fname=outPath, transparent=True)
    plt.clf()
    plt.close()


def get_base_image(region, start_date, end_date):
  s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterDate(start_date, end_date) \
    .filterBounds(region) \
    .map(lambda image: image.clip(region)) \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
    .sort('CLOUDY_PIXEL_PERCENTAGE', False) \
    .select(['B4', 'B3', 'B2'])


  image = s2.first()


  visParams = {
    'bands': ['B4', 'B3', 'B2'],
    # 'min': 0,
    # 'max': 1,
    'dimensions': [1000, 1000],
    'region': region,
    'format': 'png',
    'gamma': 4.0
  }

  imageData = {
    'visParams': visParams,
    'images': [
      {
        'image': image,
        'name': 's2.png'
      }
    ]
  }

  return imageData


  
    