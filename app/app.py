from collection.sar import Sar
from collector.sar_urban import SAR_URBAN
import geemap as gee


gee.ee_initialize()

pois = [
  ('Lesnovka',52.73937,32.02741), # 0
  ('Klintsy',52.74443,32.25086), # 1
  ('Unecha',52.81702,32.00613), # 2
  ('Klimovo Air Base',52.34435,32.17038), # 3
  ('Yelnya',54.60466,33.17042), # 4
  ('Kursk',51.76865,36.43167), # 5
  ('Pogonovo training ground',51.49683,39.17392), # 6
  ('Valuyki',50.22927,38.11056), # 7
  ('Soloti',50.27119,38.01979), # 8
  ('Opuk',45.03103,35.95830), # 9
  ('Bakhchysarai',44.76231,33.86253), # 10
  ('Novoozerne',45.40086,33.14890), # 11
  ('Dzhankoi',45.69481,34.42467), # 12
  ('Novorossiysk',44.72015,37.83119), # 13
  ('Raevskaya',44.81758,37.60302), # 14
  ('SUPPORT',49.30922,31.25083), # 15
]

(name, lat, lon) = pois[4]

date_from='2022-01-01'
date_to='2022-01-30'

sar_urban = SAR_URBAN(mode='S1', name=name, coordinates=(lat,lon), date_from=date_from, date_to=date_to)
sar_urban.run()

# for poi in pois:
#   (name, lat, lon) = poi
#   sar_urban = SAR_URBAN(mode='S1', name=name, coordinates=(lat,lon), date_from=date_from, date_to=date_to)
#   sar_urban.run()

