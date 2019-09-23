from collections import defaultdict
from joblib import load
import pandas as pd
import numpy as np

numeric_cols = ['difficulty_average','num_photos']

cat_cols = ['pattern_type','yarn_weight']

attribute_cols = [
                  'attribute_adult', #
                  'attribute_female',#
                  'attribute_worked_flat',#
                  'attribute_worked_in_the_round',#
                  'attribute_chart',#
                  'attribute_bottom_up',#
                  'attribute_one_piece',#
                  'attribute_unisex',#
                  'attribute_seamed',#
                  'attribute_lace',#
                  'attribute_teen',#
                  'attribute_ribbed_ribbing',#
                  'attribute_textured',#
                  'attribute_cables',#
                  'attribute_stripes_colorwork',#
                  'attribute_top_down',#
                  'attribute_child',#
                  'attribute_long',#
                  'attribute_stranded',#
                  'attribute_baby',#
                  'attribute_positive_ease',#
                  'attribute_has_schematic',#
                  'attribute_male',#
                  'attribute_eyelets',#
                  'attribute_toddler', #
                  'attribute_fitted',#
                  'attribute_short_rows',
                  'buttoned_mod']

needles_cols = ['needles_us_6',
                'needles_us_7',
                'needles_us_4',
                'needles_us_8',
                'needles_us_5',
                'needles_us_3',
                'needles_us_2h',
                'needles_us_10',
                'needles_us_9',
                'needles_us_1h',
                'needles_us_2',
                'needles_us_1',
                'needles_us_11',
                'needles_us_10h',
                'needles_us_13',
                'needles_us_15',
                'needles_us_0']

def ModelIt(fromUser  = 'Default', user_input = []):
 # fill out default values
  return user_input



def ModelIt2(fromUser  = 'Default', user_input = []):
 # fill out default values
 data = dict()
 data['pattern_type'] = 'pullover'
 data['yarn_weight'] = 'Worsted'
 for n in numeric_cols:
  data[n] = 0
 for a in attribute_cols:
  data[a] = 0
 for n in needles_cols:
  data[n] = 0

 for k, v in user_input.items():
  if k.startswith('attribute'):
   data[k] = 1
  if (k in cat_cols) and (v != ''):
   data[k] = str(v)
  if (k in numeric_cols) and (v != ''):
   data[k] = float(v)
  needles_used = user_input.get('needle_sizes').split(', ')
  needles_used = [('neeldes_us_'+ x) for x in needles_used]
  for n in needles_used:
  	data[n] = 1

 if fromUser != 'Default':
  clf = load('/Users/jason/Desktop/stage2_reduced_v0.joblib')
  X_new = pd.DataFrame(data, index=[0])
  price_pred = float(clf.predict(X_new))
  return f'${np.round(price_pred, 2)}'
 else:
  return 'check your input'














