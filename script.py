"""
The MIT License (MIT)
Copyright (c) 2016 Marco Bonvini

Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
and associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the 
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or 
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT 
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH 
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from matplotlib import pyplot as plt
from datetime import datetime
import pytz
import os
import pandas as pd
import numpy as np

# Get the name of the directory containing the files
dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw_data')

# Create a list of file names (using their absolute paths)
file_names = map(lambda x: os.path.join(dir_path, x), os.listdir(dir_path))

# Load each file as a pandas DataFrame and put them in a list.
# Use the first column as the index, and convert it from string to a datetime object
dfs = map(lambda x: pd.read_csv(x, index_col=0, parse_dates=True), file_names)

# We could start working with all the data into separate DataFrames but that would make our 
# work less convenient and less flexible writing a bunch of for loops for iterating 
# over the DataFrames.
# Let's put them into a Panel, i.e. a 3D DataFrame

# Retrieve the names of the houses from the file names
# './raw_data/house1.csv' becomes 'house1' with the following steps:
# 1) './raw_data/house1.csv' is split into ['./raw_data/', 'house1.csv']
# 2) get last element ['./raw_data/', 'house1.csv'] that is 'house1.csv'
# 3) split the file name 'house1.csv' and get a list like ['house1', '']
# 4) get first element of ['house1', ''] that is `house1`
#
# The names will become the way we'll reference the different houses in the Panel,
# making it more convenient than using integer indexes.
house_names = map(lambda x: os.path.split(x)[-1].split('.csv')[0], file_names)

# Create a Panel that aggregates all the data
# - first dimension are the house names,
# - second dimension (major axis) is the time index, and
# - third dimension are the variables P, Vrms, and Irms
pnl = pd.Panel(map(lambda x: x.values, dfs), items = house_names, major_axis=dfs[0].index.tolist(), minor_axis=dfs[0].columns.tolist())

# Let's start with something simple, see the mean, max and min values for all the variables
# across the different houses
print pnl.mean()
print pnl.max()

# Let's try to plot the Power consumption across all the house
pnl.ix[:,:,'Power'].plot()
plt.legend(loc='upper center', ncol=5)
plt.ylabel('Power [W]')
plt.xlabel('Time')
plt.show()

# Compute the energy in kWh
# The energy is teh sum of the energy computed in each time period that in our case
# is 2 minutes long and represented by the variable `dt`. The energy, computed in Joules,
# is then converted into kWh.
# We do not use any fancy methods to compute the integral, just a simple cumulative sum.
dt = 60*2
J_2_kWh = 1.0/3600.0/1000.0
pnl.ix[:,:,'Energy'] = (pnl.ix[:,:,'Power']*dt).apply(np.cumsum)*J_2_kWh

# Plot the energy consumption
pnl.ix[:,:,'Energy'].plot()
plt.legend(loc='upper left', ncol=5)
plt.ylabel('Energy [kWh]')
plt.xlabel('Time')
plt.show()

# Let's try to compute the average power consumption per house for hourly intervals
agg_hourly_power = pnl.ix[:,:,'Power'].groupby(by=[pnl.ix[:,:,'Power'].index.map(lambda x : x.hour)])

# Plot it with multiple bars
agg_hourly_power.mean().plot(kind='bar')
plt.legend(loc='upper center', ncol=5)
plt.ylabel('Power [W]')
plt.xlabel('Hour of day [hh]')
plt.show()

# Compute the load duration curve.
# The load duration curve shows which percentage of a load falls into a certain
# range. This curve is useful to identify ranges where the operation should be optimized 
# in order to deliver energy savings.
size_bins = 200
loads_aggregated = map(lambda n: pnl.ix[n, :,'Power'].groupby(by=[pnl.ix[n, :, 'Power'].apply(lambda x: size_bins*(x//size_bins))]).count(), pnl.items.tolist())
load_duration = pd.concat(loads_aggregated, axis=1)
load_duration.columns = pnl.items.tolist()
load_duration.fillna(0, inplace=True)
(load_duration*100.0/load_duration.sum()).plot(kind='bar')
plt.legend(loc='upper right', ncol=5)
plt.xlabel('Power [W]')
plt.ylabel('Percentage of time [%]')
plt.show()
