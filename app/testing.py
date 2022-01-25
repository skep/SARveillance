from collection.sar import Sar
from collector.cartoee import Collector
import geemap as gee


gee.ee_initialize()

name = 'Yelnya'
sar = Sar(name=name, coordinates=(45.69481,34.42467))
sar.run()
