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


def ModelIt3(fromUser  = 'Default', user_input = []):
 # fill out default values
 
 user_input['num_photos'] = int(user_input['num_photos'])
 user_input['difficulty_average'] = int(user_input['difficulty_average'])

 for k, v in user_input.items():
  if v == 'on':
    user_input[k] = 1
 
 for k in attribute_cols + needles_cols:
  if not user_input.get(k):
    user_input[k] = 0

 if fromUser != 'Default':
  # return user_input
  clf = load('/Users/jason/Desktop/stage2_reduced_v0.joblib')
  X_new = pd.DataFrame(user_input, index=[0])
  price_pred = float(clf.predict(X_new))
  return f'${np.round(price_pred, 2)}'
 else:
  return 'check your input'













