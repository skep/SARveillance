from datetime import date, timedelta
import ee

class Collector():


  # constants
  foo = 999

  # defaults
  defaults = {
    'point': (0,0),
    'name': 'Custom',
    'start_date': date.today(),
    'end_date': date.today() - timedelta(days=7),
    'max_frames': 20
  }

  def __init__(self, **kwargs): 
    '''
    update defaults with kwargs values
    only process allowed attributes (defined in defaults)
    '''
    # default_attr = Sar.defaults
    # allowed_attr = list(default_attr.keys())
    # default_attr.update(kwargs)
    # self.__dict__.update((k,v) for k,v in default_attr.items() if k in allowed_attr)
    # print(type(self.start_date))
    print('Collector init')