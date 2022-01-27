import json
import sys
import os
from datetime import date, datetime, timedelta

import ee
import geemap as gee
import matplotlib.pyplot as plt
import requests
from geemap.cartoee import (add_gridlines, add_north_arrow, add_scale_bar_lite,
                            get_map, get_image_collection_gif, pad_view)
import pprint
import cartopy.crs as ccrs
from PIL import Image
import cv2


class Sar():
    '''
    returns a list of image objects, containing the image url & metadata

    Args:
      coordinates (tuple): lat,lon coordinates
      geojson (TODO): geojson
      name (str): place name
      start_date (date): start date of timeseries
      end_date (date): end date of timeseries
      max_frame (int): max allowed frame to process

    Returns:
      collection (TODO): collection
      region (TODO): region bounds

    '''

    # constants
    IMAGE_COLLECTION_1 = 'COPERNICUS/S1_GRD'
    IMAGE_COLLECTION_2 = 'COPERNICUS/S1_GRD_FLOAT'

    # def __init__(self, **kwargs):

    def __init__(self, name='Custom', geojson=None, coordinates=(0, 0), start_date=None, end_date=None, max_frames=20):

        self.name = name

        # default start/end date
        today = date.today()
        last_week = today - timedelta(days=2)
        # set start/end date
        self.start_date = last_week if end_date is None else end_date
        self.end_date = today if start_date is None else start_date
        # format to zero hours, minutes, seconds
        self.start_date = self.start_date.strftime('%Y-%m-%dT00:00:00')
        self.end_date = self.end_date.strftime('%Y-%m-%dT00:00:00')

        # coordinates
        self.coordinates = coordinates

        # init internal vars
        self.collection = None
        self.region = None

    def run(self):
        print(self.name)

        print('-> Set Region')
        self.setRegion()

        s2 = self.s2()
        # self.download_images(s2)
        s1 = self.s1()
        # self.download_images(s1)
        # merge test
        # self.merge_images(s1, s2)
        self.fix(s1)

        # out_img = os.path.join('D:/workspace/python/SARveillance/downloads', 'final.png')
        # fig = plt.figure(figsize=(10, 10))
        # fig.patch.set_alpha(0.3)

        # ax = get_map(s2['image'], vis_params=s2['visParams'])
        # add_gridlines(ax, interval=(0.02, 0.02), linestyle=":")

        # bx = get_map(s1['image'], vis_params=s1['visParams'])
        # bx.patch.set_alpha(0.3)
        # add_gridlines(bx, interval=(0.02, 0.02), linestyle=":")

        # # ax.set_title(label='Test', fontsize=15)
        # fig.add_subplot(ax)
        # fig.add_subplot(bx)

        # plt.savefig(fname=out_img, dpi=100, transparent=True)
        # plt.clf()
        # plt.close()

        # self.s1_urban_s2()
        return

        print('-> Load Collection')
        collection = self.loadCollection()

        print('-> Filter Collection By Date Range')
        collection = self.filterDates(collection)

        print('-> Filter Collection Basics')
        collection = self.filterBasics(collection)

        print('-> Filter Bands')
        collection = self.filterBands(collection, ['VV', 'VH'])

        print('-> Filter Bounds/Region')
        collection = self.filterBounds(collection)

        print('-> Clip Collection Images')
        # collection = self.clipRegion(collection)

        print('-> Filter Bands')
        # collection = self.filterBands(collection, ['VH', 'VV'])

        print('-> Urban Mode')
        collection = self.urban_mode(collection)

        print('-> Set Visualization Parameter')
        visParams = {
            'bands': ['VH55', 'VV', 'VH8'],
        }

        print('Create Visualization')
        self.createVisualization(collection, visParams)

    ###########################################################
    ###########################################################
    ###########################################################
    ###########################################################
    ###########################################################

    def fix(self, s1):
        ip = s1['images'][0]['outPath']
        image = cv2.imread(ip, 0)
        image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 17, -6)
        cv2.imwrite(
            'C:/Users/solschner/workspace-dev/python/Sarveillance2/downloads/fix.png', image)

    def merge_images(self, s1, s2):
        basePath = s2['images'][0]['outPath']
        baseImage = Image.open(basePath)
        # baseImage = baseImage.convert("RGBA")
        print(basePath)
        imageSize = baseImage.size
        outFolder = os.path.join(os.getcwd(), 'Downloads')
        for i, image in enumerate(s1['images']):
            s1Path = image['outPath']
            s1Image = Image.open(s1Path)
            s1Image = s1Image.convert("RGBA")
            # new_image = Image.new(
            #     'RGBA', (imageSize[0], imageSize[1]), (0, 0, 0, 1))
            # new_image.paste(baseImage, (0, 0))
            # new_image.paste(s1Image, (0, 0))
            imageName = f's1_{str(i).zfill(3)}_merged.png'
            outPath = os.path.join(outFolder, imageName)
            # new_image.save(outPath, format="png")
            x = Image.alpha_composite(
                Image.new("RGBA", baseImage.size), baseImage.convert('RGBA'))
            x.paste(s1Image, (0, 0), s1Image)
            x.save(outPath, format="png")

    def download_images(self, imageData):
        # prepare region as [s,w,n,e]
        (lat, lon) = self.coordinates
        r = 0.4
        region = [lon+r, lat-r, lon-r, lat+r]
        # vis params
        visParams = imageData['visParams']
        # loop
        for data in imageData['images']:
            image = data['image']
            outPath = data['outPath']
            plt.figure(figsize=(8, 8), dpi=80)
            ax = get_map(image, region=region, vis_params=visParams)
            # plt.savefig("filename.png", transparent=True)
            plt.savefig(fname=outPath, transparent=True)
            plt.clf()
            plt.close()

    def download_images_OLD(self, data):
        pass
        # filename = os.path.join(out_dir, 's2.tif')
        # gee.ee_export_image(image, filename=outPath, scale=8,
        #                     region=self.region, file_per_band=False)
#

    def s2(self):

        def maskS2clouds(image):
            qa = image.select('QA60')
            # Bits 10 and 11 are clouds and cirrus, respectively.
            cloudBitMask = 1 << 10
            cirrusBitMask = 1 << 11
            # Both flags should be set to zero, indicating clear conditions.
            mask = qa.bitwiseAnd(cloudBitMask).eq(0) \
                .And(qa.bitwiseAnd(cirrusBitMask).eq(0))

            return image.updateMask(mask).divide(10000)

        def clip(image):
            return image.clip(aoi)

        # load S2 data
        aoi = self.region
        s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(aoi) \
            .filterDate("2017-03-28", "2022-01-1") \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5)) \
            .sort('CLOUDY_PIXEL_PERCENTAGE', False) \
            .map(maskS2clouds) \
            .select(['B4', 'B3', 'B2']) \
            .map(clip)

        # set vis params
        visParams = {
            'bands': ['B4', 'B3', 'B2'],
            'min': 0,
            'max': 1,
            'dimensions': [750, 750],
            'region': self.region,
            'format': 'png',
            'gamma': 2.0
        }

        # init image data
        imageData = {
            'visParams': visParams,
            'images': []
        }

        # we only want the s2 image with the less cloud coverage
        # we already have it sorted by cloud cover, so we take the first
        image = s2.first()
        imageName = 's2.png'
        outFolder = os.path.join(os.getcwd(), 'Downloads')
        outPath = os.path.join(outFolder, imageName)
        # add image to imageData
        imageData['images'].append({
            'image': image,
            'outPath': outPath
        })

        # and return
        return imageData

    def s1(self):

        def clip(image):
            return image.clip(aoi)

        # load S1 data
        aoi = self.region
        s1 = ee.ImageCollection('COPERNICUS/S1_GRD_FLOAT') \
            .filterBounds(aoi) \
            .filterDate(self.start_date, self.end_date) \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
            .filter(ee.Filter.eq('instrumentMode', 'IW')) \
            .select(['VV', 'VH']) \
            .map(clip)

        def _urban_mode(image):
            vh55 = image.expression(
                "5.5 * VH > 0.5", {'VH': image.select('VH')}).rename('VH55')
            vh55 = image.select('VH').multiply(5.5).rename('VH55')
            # vh8 = image.expression(
            # "1.0 * VH", {'VH': image.select('VH')}).rename('VH8')
            vh8 = image.select('VH').multiply(8).rename('VH8')
            return image.addBands([vh55, vh8])

        s1 = s1.map(_urban_mode)
        s1 = s1.select(['VH55', 'VV', 'VH8'])
        s1 = s1.map(clip)

        # image = s1.first()
        visParams = {
            'bands': ['VH55', 'VV', 'VH8'],
            # 'dimensions': [750, 750],
            # 'crs': 'EPSG:32637'
            'crs': "EPSG:4326",
            'region': self.region,
            # 'crs': "EPSG:32637",
            'opacity': 0.8,
            # 'min': 0,
            # 'max': 1,
            'format': 'png',
            # 'gamma': 2.0
        }

        # image count in collection
        count = int(s1.size().getInfo())
        print(f'Count: {count}')

        # prepare loop
        dates = s1.aggregate_array("system:time_start")
        dates = dates.map(lambda d: ee.Date(d).format('YYY-MM-DD')).getInfo()
        images = s1.toList(count)
        # loop
        imageData = {
            'visParams': visParams,
            'images': []
        }
        for i, date in enumerate(dates):
            image = ee.Image(images.get(i))
            imageName = f's1_{str(i).zfill(3)}.png'
            outFolder = os.path.join(os.getcwd(), 'Downloads')
            outPath = os.path.join(outFolder, imageName)
            imageData['images'].append({
                'image': image,
                'outPath': outPath
            })

        # return all data
        return imageData

        # Size plot
        # fig = plt.figure(figsize=(10, 10))
        # ax = get_map(image, vis_params=visParams)
        # # pad_view(ax)
        # add_gridlines(ax, interval=(0.02, 0.02), linestyle=":")
        # ax.set_title(label='Test', fontsize=15)
        # plt.savefig(fname=out_img, dpi=100)
        # plt.clf()
        # plt.close()

        # return {
        #     'image': image,
        #     'visParams': visParams,
        #     'outPath': outPath
        # }

    ###########################################################
    ###########################################################
    ###########################################################
    ###########################################################
    ###########################################################

    def setRegion(self):
        (lat, lon) = self.coordinates
        base_point = ee.Geometry.Point([float(lon), float(lat)])
        base_buffer = base_point.buffer(3000)
        self.region = base_buffer.bounds()

    def loadCollection(self):
        '''
        TODO
        '''
        return ee.ImageCollection(self.IMAGE_COLLECTION_2)

    def filterDates(self, collection):
        '''
        filters an image collection by a range of dates in yyyy-mm-dd format
        returns image collection
        '''
        return collection.filterDate(self.start_date, self.end_date)

    def filterBasics(self, collection):
        '''
        filter basic stuff, instrument mode
        '''
        return collection \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
            .filter(ee.Filter.eq('instrumentMode', 'IW'))
        # .filter(ee.Filter.eq('resolution_meters', 10))

    def filterBands(self, collection, bands=['VV', 'VH']):
        '''
        filter bands
        '''
        def _filterBands(image):
            return image.select(bands)
        return collection.map(_filterBands)

    def filterBounds(self, collection):
        '''
        filter bounds
        '''
        return collection.filterBounds(self.region)

    def clipRegion(self, collection):
        '''
        clip region from images
        '''
        return collection.map(lambda image: image.clip(self.region))

    def urban_mode(self, collection):
        '''
        Create a reducer that will compute the specified percentiles,
        e.g. given [0, 50, 100] will produce outputs named 'p0', 'p50', and 'p100'
        with the min, median, and max respectively.
        '''
        def _urban_mode(image):
            vh55 = image.expression(
                "5.5 * VH > 0.5", {'VH': image.select('VH')}).rename('VH55')
            vh8 = image.expression(
                "8.0 * VH", {'VH': image.select('VH')}).rename('VH8')
            return image.addBands([vh55, vh8])
        return collection.map(_urban_mode)

    def createVisualization(self, collection, visParams):
        '''
        Create the final visualization
        '''
        gif = gee.create_timelapse(
            collection=collection,
            start_date=self.start_date,
            end_date=self.end_date,
            region=self.region,
            bands=visParams['bands'],
            vis_params=visParams,
            dimensions=950,
            frames_per_second=2,
            crs="EPSG:32637",
            frequency='day',
        )
        print(gif)
