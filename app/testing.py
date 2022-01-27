from collection.sar import Sar
from collection.sar2 import sar
from collector.cartoee import Collector
import geemap as gee


gee.ee_initialize()

pois = [
  ('Lesnovka',52.73937,32.02741),
  ('Klintsy',52.74443,32.25086),
  ('Unecha',52.81702,32.00613),
  ('Klimovo Air Base',52.34435,32.17038),
  ('Yelnya',54.60466,33.17042),
  ('Kursk',51.76865,36.43167),
  ('Pogonovo training ground',51.49683,39.17392),
  ('Valuyki',50.22927,38.11056),
  ('Soloti',50.27119,38.01979),
  ('Opuk',45.03103,35.95830),
  ('Bakhchysarai',44.76231,33.86253),
  ('Novoozerne',45.40086,33.14890),
  ('Dzhankoi',45.69481,34.42467),
  ('Novorossiysk',44.72015,37.83119),
  ('Raevskaya',44.81758,37.60302),
  ('SUPPORT',49.30922,31.25083),
]

(name, lat, lon) = pois[13]


# sar = Sar(name=name, coordinates=(lat,lon))
# sar.run()
sar(name=name, coordinates=(lat,lon))
