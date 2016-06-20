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

# To return value in mins / total mins in one day
def to_mins(x):
    x = pd.Timestamp(x)
    year = x.year
    month =  x.month
    day = x.day
    return (x.value - pd.Timestamp(str(year)+'-'+str(month)+'-'+str(day)).value) / (60 * (10**9))

# Helper method to convert values to radian
def convert_to_radian(x):

    return ((x / (24*60)) * 2 * pi)

# Get all the sleep intervals based on bedroom only data
def get_df_sleep_intervals(df):
    
    df_sleep = pd.DataFrame(columns=('sleep_start', 'sleep_end', 'sleep_duration'))
    
    sleep_start = None
    sleep_end = None
    
    for index, row in df.iterrows():
        if (row['bedroom_only'] and sleep_start is None):
            sleep_start = row['date']
        elif ((not row['bedroom_only']) and (not sleep_start is None)):
            sleep_end = row['date']
            sleep_duration = sleep_end - sleep_start
        
            payload = {}
            payload['sleep_start'] = sleep_start
            payload['sleep_end'] = sleep_end
            payload['sleep_duration'] = sleep_duration
            df_sleep = df_sleep.append(payload, ignore_index=True)
        
            sleep_start = None
            sleep_end = None
            
    # already reached end of file, sleep was spilled over from last day to next month
    if not sleep_start is None:        
        sleep_end = df['date'].iloc[-1]
        sleep_duration = sleep_end - sleep_start
        
        payload = {}
        payload['sleep_start'] = sleep_start
        payload['sleep_end'] = sleep_end
        payload['sleep_duration'] = sleep_duration
        df_sleep = df_sleep.append(payload, ignore_index=True)
        
        sleep_start = None
        sleep_end = None
          
    # TODO: handle first and last entry in a more appropriate manner 
    # df_sleep.drop(df_sleep.head(1).index, inplace=True)
        
    # print(df_sleep.head())  
    # print(df_sleep.tail())  
    return df_sleep

# Returns a distance matrix (a numpy array)
def get_x_from_df(series):
    print(series.head())
    
    # Vectorizing to_mins and to_radian functions
    tmin = np.vectorize(to_mins)
    trad = np.vectorize(convert_to_radian)

    # Converting series of timestamp -> minutes / total minuites in a day -> radian
    input_rad = trad(tmin(series))

    # Convert time to rad points   
    X = input_rad[None,:] - input_rad[:,None]

    # Assign 'shortest distance to each point
    X[((X > pi) & (X <= (2*pi)))] = X[((X > pi) & (X <= (2*pi)))] -(2*pi)
    X[((X > (-2*pi)) & (X <= (-1*pi)))] = X[((X > (-2*pi)) & (X <= (-1*pi)))] + (2*pi) 
    X = abs(X)

    return X

# Returns output from sklearn DBSCAN method
def dbscan(eps, min_pts, X, metric='precomputed'):
    db = DBSCAN(eps, min_pts, metric)
    db.fit(X)
    return db.labels_, db.components_, db.core_sample_indices_

# TODO:
# 1. Research on methods to identify EPS.
# 2. Implement that method
def calculate_eps():
    pass

############################################################################################

# Start timer:
time_now = time.time()

### Globals ###
file_dir = 'data'
file_name = ''.join([file_dir,'/','SensorReading_2015-10_S001.csv'])

# print file name
print('File name: ', file_name)

# Get dataframe containing readings from sensor reading, exclude 
df = pd.read_csv(file_name, delimiter=',', usecols=[x for x in range(0,8)],parse_dates=[1])
column_names = list(df.columns.values)
# print('Before preprocessing: ', df.head(), df.tail())

#Remove rows where all sensors report 'no'
df = df.ix[(df['door_contact_as'] == 'Yes') | (df['living_room_as'] == 'Yes') 
	| (df['bedroom_as'] == 'Yes') | (df['bed_as'] == 'Yes') 
	| (df['bathroom_as'] == 'Yes') | (df['kitchen_as'] == 'Yes')]

# Add new column with bedroom_only flag
# TODO: handle for other cases where more sensors are valid
bedroom_only = ((df['door_contact_as'] == 'No') &
                (df['living_room_as'] == 'No') & 
                (df['bedroom_as'] == 'Yes') & 
                (df['bathroom_as'] == 'No') & 
                (df['kitchen_as'] == 'No'))

# Assign Series to dataframe.
df['bedroom_only'] = bedroom_only
# df = df.reset_index(drop=True)
df_sleep = get_df_sleep_intervals(df)
# print(df_sleep.columns.values)
# print(df_sleep.head())

# X is a distance matrix.
# Set 'X1' as sleep_start timings
X1 = get_x_from_df(df_sleep['sleep_start'])

# Set 'X2' as sleep_end timings
X2 = get_x_from_df(df_sleep['sleep_end'])

# TODO
# 1. Implement method to calculate EPS
# 2. Get output for both X1 and X2
# 3. Construct cluster plot. Polar plot

# Arbitrary eps and min_pts value:
eps = convert_to_radian(15)
min_pts = 10

X1_label, X1_components, X1_csi = dbscan(eps, min_pts, X1)
X2_label, X2_components, X2_csi = dbscan(eps, min_pts, X2)

# Sanity check here:
print('Sanity check.......')
print('Checking.........................')
print('start sleep time cluster: ')
# - 1 if -1 exist in labels because -1 is used to denote noise
X1_no_clusters = len(set(X1_label)) - (1 if -1 in X1_label else 0)
print('Number of clusters for start sleep time: ', X1_no_clusters )
print('end sleep time cluster: ')
X2_no_clusters = len(set(X2_label)) - (1 if -1 in X2_label else 0)
print('Number of clusters for end sleep time: ', X2_no_clusters )


print("Elasped Time: ", round(time.time() - time_now, 3), "seconds")