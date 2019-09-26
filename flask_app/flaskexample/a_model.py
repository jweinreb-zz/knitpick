from collections import defaultdict
from joblib import load
import pickle
import pandas as pd
import numpy as np
from sklearn.neighbors import KDTree
import os

import base64
from io import BytesIO
from flask import Flask
from matplotlib.figure import Figure
import seaborn as sns

#df = pd.read_csv("/Users/jason/github/knitpick/flask_app/knitpick.csv")
#df.loc[:, 'buttoned_mod'] = df[['attribute_buttoned', 'attribute_buttonholes']].max(axis=1)

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

design_cols = [
                  'attribute_worked_flat',#
                  'attribute_worked_in_the_round',#
                  'attribute_chart',#
                  'attribute_bottom_up',#
                  'attribute_one_piece',#
                  'attribute_seamed',#
                  'attribute_lace',#
                  'attribute_ribbed_ribbing',#
                  'attribute_textured',#
                  'attribute_cables',#
                  'attribute_stripes_colorwork',#
                  'attribute_top_down',#
                  'attribute_stranded',#
                  'attribute_has_schematic',#
                  'attribute_eyelets',#
                  'attribute_short_rows',
                  'buttoned_mod']

fit_cols = [      'attribute_adult', #
                  'attribute_female',#
                  'attribute_unisex',#
                  'attribute_teen',#
                  'attribute_child',#
                  'attribute_baby',#
                  'attribute_positive_ease',#
                  'attribute_male',#
                  'attribute_toddler', #
                  'attribute_fitted']

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

pattern_types = ['ankle',
 'cardigan',
 'coat',
 'cowl',
 'dress',
 'fingerless',
 'gloves',
 'hat',
 'knee-highs',
 'mid-calf',
 'mittens',
 'other-socks',
 'other-sweater',
 'other-top',
 'pullover',
 'scarf',
 'shawl-wrap',
 'shrug',
 'skirt',
 'sleeveless-top',
 'strapless-top',
 'tee',
 'thigh-high',
 'toeless',
 'tube',
 'vest']

yarn_weights = ['Any gauge',
 'Aran',
 'Aran / Worsted',
 'Bulky',
 'Cobweb',
 'DK',
 'DK / Sport',
 'Fingering',
 'Jumbo',
 'Lace',
 'Light Fingering',
 'No weight specified',
 'None',
 'Sport',
 'Super Bulky',
 'Thread',
 'Worsted']

def ModelIt3(fromUser  = 'Default', user_input = []):
 # fill out default values
 
 user_input['num_photos'] = int(user_input['num_photos'])
 user_input['difficulty_average'] = int(user_input['difficulty_average'])

 for k, v in user_input.items():
  if v == 'on':
    user_input[k] = True
 
 for k in attribute_cols + needles_cols:
  if not user_input.get(k):
    user_input[k] = False

 if fromUser != 'Default':
  clf = load(os.getenv('PRICE_PICKLE_PATH'))
  X_new = pd.DataFrame(user_input, index=[0])
  price_pred = float(clf.predict(X_new))
  #return f'${np.round(price_pred, 2)}'
  user_input['price'] = price_pred
  clf2 = load(os.getenv("PROJECTS_PICKLE_PATH"))
  X_new = pd.DataFrame(user_input, index=[0])
  proj_pred = float(clf2.predict(X_new))
  return dict(price=f'${np.round(price_pred, 2)}', projects=int(np.round(proj_pred, 0)))
 else:
  return 'check your input'

def ModelIt5(fromUser  = 'Default', user_input = []):
  base = "patterns/search#craft=knitting&"
  cat = f"pc={user_input['pattern_type']}&"
  yarnw = f"weight={user_input['yarn_weight'].replace(' ', '-').lower()}&"
  
  start = base + cat + yarnw
  design = "pa="
  for d in design_cols + ['attribute_long']:
    if (user_input.get(d) == "on"):
      if d == 'attribute_worked_in_the_round':
        design += "in-the-round" + "%2B"
      elif d == 'attribute_has_schematic':
        design += "schematic" + "%2B"
      elif d == 'buttoned_mod':
        design += "buttonholes" + "%2B"
      elif d == 'attribute_long':
        design += 'long-sleeve' + '%2B'
      else:
        design += d.split('attribute_')[1].replace('_', '-') + "%2B"
  if design != "pa=":
    design = design[:-3] + "&"
    start += design

  fit = "fit="
  for f in fit_cols:
    if user_input.get(f) == "on":
        fit += f.split('attribute_')[1].replace('_', '-') + "%2B"
  if fit != "fit=":
    fit = fit[:-3]  + "&"
    start += fit

  return start[:-1]

def ModelIt4(fromUser  = 'Default', user_input = []):
 # fill out default values
 
 user_input['num_photos'] = int(user_input['num_photos'])
 user_input['difficulty_average'] = int(user_input['difficulty_average'])

 for k, v in user_input.items():
  if v == 'on':
    user_input[k] = True
 
 for k in attribute_cols + needles_cols:
  if not user_input.get(k):
    user_input[k] = False

 if fromUser != 'Default':
  # return user_input
  clf = load('/Users/jason/Desktop/stage2_reduced_v0.joblib')
  X_new = pd.DataFrame(user_input, index=[0])
  X_new_cat = X_new[cat_cols]
  X_new = X_new[numeric_cols + attribute_cols + needles_cols]
  newcols = ['yarn_weight_' + y for y in sorted(yarn_weights)] + ['pattern_type_' + p for p in sorted(pattern_types)]

  with open('/Users/jason/github/knitpick/flask_app/kdtree.p', 'rb') as f:
    tree = pickle.load(f)
  #dist, ind = tree.query(X_new, k=5)
  df_to_query = pd.concat([X_new, pd.get_dummies(X_new_cat).reindex(columns=newcols, fill_value=0)], axis=1)
  dist, ind = tree.query(df_to_query, k=1000)

  with open('/Users/jason/github/knitpick/flask_app/pattern_data.p', "rb") as f:
    metadata = pickle.load(f)
    metadata = metadata.loc[(metadata[list(user_input)] == pd.Series(user_input)).all(axis=1)]
    #return subdf.permalink
    the_links = []
    #for i, row in subdf.iterrows():
      #the_links.append(dict(name=row['name'], permalink=row.permalink))
    #return the_links
    #for i, row in metadata.head().iterrows():
    #  the_links.append(dict(name=row['name'], permalink=row.permalink))
    return metadata
  #return {'names': subdf.name, 'permalinks': subdf.permalink}
  #return metadata.iloc[2]
 else:
  return 'check your input'

def ModelIt6(fromUser  = 'Default', user_input = []):
 # fill out default values
 
 user_input['num_photos'] = int(user_input['num_photos'])
 user_input['difficulty_average'] = int(user_input['difficulty_average'])

 for k, v in user_input.items():
  if v == 'on':
    user_input[k] = True
 
 for k in attribute_cols + needles_cols:
  if not user_input.get(k):
    user_input[k] = False

 if fromUser != 'Default':
  clf = load(os.getenv('PRICE_PICKLE_PATH'))
  X_new = pd.DataFrame(user_input, index=[0])
  X_encoded = clf.named_steps['columntransformer'].fit_transform(X_new)
  price_estimates = [clfest.predict(X_encoded)[0] for clfest in clf.named_steps['randomforestregressor'].estimators_]
  fig = Figure()
  ax = fig.subplots()
  fig.set_size_inches(12, 8)
  sns.distplot(price_estimates, ax=ax, hist=True)
  ax.set_xlabel('Price ($)')
  ax.set_ylabel('Density')
  ax.set_title('Distribution of price estimates for your pattern')
  ax.axvline(np.mean(price_estimates), linestyle='--', color='red')
  # Save it to a temporary buffer.
  # Save it to a temporary buffer.
  buf = BytesIO()
  fig.savefig(buf, format="png")
  # Embed the result in the html output.
  data = base64.b64encode(buf.getbuffer()).decode("ascii")
  return f'data:image/png;base64,{data}'
 else:
  return "check your input"

