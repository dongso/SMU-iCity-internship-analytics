"""
AUTHOR	: TAN WEI JIE AMOS
EMAIL	: amos.tan.2014@sis.smu.edu.sg
DATE    : 
"""

###########################################IMPRORTS#########################################
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from math import pi
from sklearn.cluster import DBSCAN
###########################################IMPRORTS#########################################

#Start timer:
time_now = time.time()

### Globals ###
file_dir = 'data'
file_name = ''.join([file_dir,'/','SensorReading_2015-10_S001.csv'])

# print file name
print('File name: ', file_name)

#get dataframe containing readings from sensor reading, exclude 
df = pd.read_csv(file_name, delimiter=',', usecols=[x for x in range(0,8)],parse_dates=[1])
column_names = list(df.columns.values)
# print('Before preprocessing: ', df.head(), df.tail())

#Remove rows where all sensors report 'no'
df = df.ix[(df['door_contact_as'] == 'Yes') | (df['living_room_as'] == 'Yes') 
	| (df['bedroom_as'] == 'Yes') | (df['bed_as'] == 'Yes') 
	| (df['bathroom_as'] == 'Yes') | (df['kitchen_as'] == 'Yes')]

df = df.reset_index(drop=True)

# add new column with bedroom_only flag
# TODO: handle for other cases where more sensors are valid
bedroom_only = ((df['door_contact_as'] == 'No') &
                (df['living_room_as'] == 'No') & 
                (df['bedroom_as'] == 'Yes') & 
                (df['bathroom_as'] == 'No') & 
                (df['kitchen_as'] == 'No'))

# Assign Series to dataframe.
df['bedroom_only'] = bedroom_only



# print('After preprocessing: ', df.head(), df.tail())
#reset index
# df = df.reset_index(drop=True)

#get difference between timestamps 
df['TimeDelta'] = df['date'].diff().fillna(0)
df['in_mins'] = np.array(df['TimeDelta'] / np.timedelta64(1, 'm'))

#'sleep' time > 1 min
df = df.ix[(df['in_mins'] > 1)]
df = df.reset_index(drop=True)

print(' Statistics for df["in_mins"] \n', df['in_mins'].describe()) 

#plot
x = df['in_mins']
binwidth = 30
bins = range(int(min(x)), int(max(x) + binwidth), binwidth)
plt.hist(x, bins)
plt.xlabel('duration')
plt.ylabel('freq')
# plt.show()

#preprocessing, change timestamp value in minutes

#to return value in mins / total mins in one day
def to_mins(x):
    x = pd.Timestamp(x)
    year = x.year
    month =  x.month
    day = x.day
    return (x.value - pd.Timestamp(str(year)+'-'+str(month)+'-'+str(day)).value) / (60 * (10**9))

def convert_to_radian(x):

	return ((x / (24*60)) * 2 * pi)

tmin = np.vectorize(to_mins)
trad = np.vectorize(convert_to_radian)

#DBSCAN
input_ = tmin(df['date'])
input_rad = trad(input_)

#convert time to rad points
X = input_rad[None,:] - input_rad[:,None]
#assign 'shortest distance to each point'
X[((X > pi) & (X <= (2*pi)))] = X[((X > pi) & (X <= (2*pi)))] -(2*pi)
X[((X > (-2*pi)) & (X <= (-1*pi)))] = X[((X > (-2*pi)) & (X <= (-1*pi)))] + (2*pi) 
X = abs(X)

eps = 72.750858
eps_rad = (eps / (24*60)) * 2 * pi 
min_samples = 1

# Set DBSCAN parameters
db = DBSCAN(eps_rad, min_samples, metric='precomputed')

# fit estimator
db.fit(X)

#get labels
labels = db.labels_
print(labels)
# total there are n clusters + noise in labels. 
# - 1 if -1 exist in labels because -1 is used to denote noise
no_clusters = len(set(labels)) - (1 if -1 in labels else 0)
components = db.components_
#csi = core sample indices
csi = db.core_sample_indices_

# Polar plot

plt.polar(2*pi, 1)
# plt.show()
print('No. Of Clusters: ', no_clusters)

print("Elasped Time: ", round(time.time() - time_now, 3), "seconds")