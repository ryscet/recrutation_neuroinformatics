# -*- coding: utf-8 -*-
"""
Reads the rat_path.csv file created by motion_detector.py and calculates rat behavior results.
Computes and plots the ditribution of path lengths and durations in each room, and total time spent in each room.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math

# Use r-like style for plots
plt.style.use('ggplot')

# Define the room borders
left_border = 276
right_border = 463

def plot_results():
    """Parses and plots rat path results.
       Plots total time and total distance per room in the top row.
       Plots boxplots for visit durations and path lengths in bottom row.
    """
    # Parse rat_path.csv and group it by room occupied by the rat
    grouped = prepare_data().groupby('room_id')
    # Prepare a dict for storing the results per each room
    results = {'path_lengths' :{}, 'n_frames': {}, 'visit_durations' : {}}
    
    # iterate over rooms and calcualte results
    for name, room in grouped:
       # Store results in a dict
       results['path_lengths'][name], results['n_frames'][name],  results['visit_durations'][name] = calc_results(room, name) 
    
    # Create figure 
    fig, axes = plt.subplots(nrows = 2, ncols = 2)
    fig.suptitle('Rat movement results', fontweight = 'bold', fontsize =  12)
    
    # get room names for plot legend
    room_names = sorted(list(results['path_lengths'].keys()))
    
    # Plot total time per room
    sns.barplot(x = list(results['n_frames'].keys()), y =list(results['n_frames'].values()),
                ax = axes[0, 0], order = room_names)
                
    # Plot total distance per room    
    sns.barplot(x = list(results['path_lengths'].keys()), y = [sum(item) for item in list(results['path_lengths'].values())],
                ax = axes[0, 1], order = room_names)

    # Convert path lengths dict to dataframe
    p_len = pd.DataFrame(dict([(key, pd.Series(value)) for key,value in results['path_lengths'].items() ]))
    # Plot path lenghts distributions 
    sns.boxplot(x = 'variable', y = 'value', data = pd.melt(p_len), ax = axes[1, 1], order = room_names,
                **dict(showmeans = True,meanline = True))        
    
    # Convert visit durations dict to dataframe
    v_dur = pd.DataFrame(dict([(key, pd.Series(value)) for key,value in results['visit_durations'].items() ]))
    # Plot visit times distributions 
    sns.boxplot(x = 'variable', y = 'value', data = pd.melt(v_dur), ax = axes[1, 0], order = room_names,
                **dict(showmeans = True,meanline = True))       
    
    
    axes[0, 0].set_ylabel('total time (frames)')
    axes[0, 1].set_ylabel('total distance (pixels)')
    axes[1, 1].set_ylabel('path lengths (pixels)')
    axes[1, 0].set_ylabel('visit durations (frames)')
    axes[1, 0].set_xlabel('')
    axes[1, 1].set_xlabel('')
    




def prepare_data():
    """Reads the csv with path the rat has traveled in the video. 
       Annotates each position with the room number and the distance traveled from previous position. 

       Return
       ------
       rat_path: DataFrame
                 columns are: room_id, x_cords, y_cords, distance
    """
    
    # Read the csv output of the motion_detector script
    rat_path = pd.read_csv('/Users/user/Desktop/OpenCV_python/rat_path.csv')

    # Annotate each position with room id, based on room borders
    rat_path['room_id'] = 'room_2'
    rat_path.loc[rat_path['x_cords'] <= left_border, 'room_id'] = 'room_1'
    rat_path.loc[rat_path['x_cords'] >= right_border, 'room_id'] = 'room_3'
    
    # Calculate the ditance between each and next position using pythagorean formula
    rat_path['x_delta'] = (rat_path['x_cords'].shift() - rat_path['x_cords']).fillna(0)
    rat_path['y_delta'] = (rat_path['y_cords'].shift() - rat_path['y_cords']).fillna(0)
    
    rat_path['distance'] = np.vectorize(dist)(rat_path['x_delta'], rat_path['y_delta'])
    
    return rat_path.drop(['x_delta', 'y_delta'], axis = 1)
    


def calc_results(room, room_id):
    """Compute the path results per room. 
       Slice the room dataframe into pieces representing signle visits to the room.
       Aggregate distance traveled and time spent during each visit.  

       Parameters
       ----------
       room: DataFrame
           DataFrame resulting from filtering the `rat_path` for a single room. 

       room_id:str
           name of the room, ex.'room_1'
             
       Returns
       -------
       path_lengths: numpy.array
           collection of distances covered during each visit to the room.
       
       total_room_time: int
           number of frames spent in a room during the whole recording.
       
       visit_durations: numpy.array
           collection of durations of visits to the room.


    """
    
    # Store the index in a new column. 
    room.loc[:,'frame'] = room.index        
    # Calculate the difference between consecutive frame numbers 
    # Note, filtering rat_path by room_id, will result in frames beeing consecutive during one room visit, and having large differences when rat was changing rooms.
    room.loc[:,'f_delta'] = (room['frame']-room['frame'].shift()).fillna(1)
    # Reseting index is only for convienience, so the values are continous again   
    room.reset_index(inplace = True)
    
    # Indexes where f_delta was greater then 1 indicate rat was in a different room one frame before, and this frame was removed during filtering by room_id.
    # Insert 0 at index 0, to account for entering the room where the rat started.
    entering = np.insert(room[room['f_delta'] > 1].index.values,0,0)
    # Indexes 1 position before entering a new room, are when rat left the old room
    leaving = np.append(entering[1::] - 1, len(room))
    
    # Store the room entering and leaving frame indices in a dataframe.
    crossings = pd.DataFrame({'entering': entering, 'leaving' : leaving})
    
    # Define entering to the room as the starting point to calculate the path length for each visit.
    room.loc[room['f_delta'] > 1, 'distance'] = 0

    # For storing the distance traveled in each visit to the room    
    path_lengths = []
    # For storing the time spent in each visit to the room    
    visit_durations = []
    
    # Slice the room dataframe by entering and leaving indices
    for idx, row in crossings.iterrows():        
        # Get a single visit slice
        # + 1 because the upper range is not included
        single_path = room.iloc[row['entering']:row['leaving'] + 1]
   
        # Correct for special cases when rat only passed by room 2 and was captured there for a single frame
        if((len(single_path) == 1) and (room_id == 'room_2')):
            # In such case state the rat covered the distance equal to the width of room 2
            path_lengths.append(right_border - left_border)
        else:
            # Otherwise save the path length covered during the visit
            path_lengths.append(single_path['distance'].sum())    
        # Store the time of a visit in frames
        visit_durations.append(len(single_path))
    
    # Get total time spent in this room
    total_room_time = len(room)
    
    return np.array(path_lengths), total_room_time , np.array(visit_durations)
    

def dist(x, y):
    """Calculate distance between points (0,0) and (`x`, `y`)
        
        Parameters
        ----------
        x,y: int, int
            x-distance and y-distance between rat_path frames
    """
    return math.hypot(x, y)
    
if __name__ == '__main__':  
    plot_results()
