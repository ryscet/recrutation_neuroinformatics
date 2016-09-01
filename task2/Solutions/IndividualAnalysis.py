"""
Computes the times of the visits per mouse per phase to each room.
"""

import sys
import os.path
sys.path.append(os.path.dirname(__file__))
sys.path.append("..")

import pandas as pd
from load_data import mice
from ParseData import get_mice_phase
import numpy as np


def get_all_times():
    """ Computes the total times spent by each mouse in each room in each phase.
        Saves the resulting dataframe to a csv file.
        
        Returns
        -------
        room_time_db: DataFrame
            columns: 'room_id', 'room_time', 'phase', 'mouse_id'
    """
    # Define the phases to iterate over
    phases = ['PHASE 1 dark', 'PHASE 1 light', 'PHASE 2 dark', 'PHASE 2 light', 'PHASE 3 dark', 'PHASE 3 light']
    # Define the mice names to iterate over
    mice_list = list(mice)
    # Prepare a dataframe to store the results
    room_time_db = pd.DataFrame(columns = ['room_id', 'room_time', 'phase', 'mouse_id'])
    # Iterate over all mice in all phases
    for mouse in mice_list:
        print(mouse)
        for phase in phases:
            print(phase)
            # Load the data and drop unneccessary columns - event_number is used for PairAnalysis
            _mice_phase = get_mice_phase(mouse, phase).drop('event_number', axis =1)
            # Calculate the time spent in each room by this mouse in this phase
            r_time = calc_room_time(_mice_phase)
            # Add the phase and mouse id info to the results
            r_time['phase'] = phase
            r_time['mouse_id'] = mouse
            # Aggregate the results
            room_time_db = room_time_db.append(r_time, ignore_index = True, verify_integrity = True)
            
    # Save the results so they don't need to be computed each time for the anlysis    
    path = os.path.dirname(os.path.realpath(__file__)) + '/Solutions'

    room_time_db.to_csv(path +'/parsed_data/indiv_times.csv', index = False)
    
    return room_time_db
    

def calc_room_time(mice_phase):
    """ Calculate timedeltas between room entry and leaving. 
        Sum them to get the total time for each room per mouse per phase.
        
        Parameters
        ----------
        mice_phase: DataFrame
            Contains the dataframe returned by `ParseData.get_mice_phase()`
            For a description see `ParseData.get_mice_phase()`
            
        Returns
        -------
        durations: DataFrame
            Contains total time spent per room by `mice_phase`
            columns: room_id, 'room_time'
                
    """
    # Dict where keys will be room number and values will be sums of visit durations to this room.
    durations = {}
    # iterate over visits grouped by room number
    for room_idx, mice_data in mice_phase.groupby('room'):
        # Get the visits start and end timestamp (datetime format)
        start = mice_data.loc[mice_data['status'] == 'start'] 
        end = mice_data.loc[mice_data['status'] == 'end'] 
        # Calculate the sum of all visits durations and store the results in the durations dictionary
        durations[room_idx] = [np.array(end.index.values - start.index.values, dtype='timedelta64[ms]').sum().astype(int)]                
  
    # Convert to a pandas dataframe so they can be aggregated easilly. Make the room number the index of the dataframe.
    durations = pd.DataFrame.from_dict(durations, orient = 'index')
    # Rename the column
    durations.columns = ['room_time']
    # Copy the index over to a new column
    durations['room_id'] = durations.index
    
    return durations

if __name__ == '__main__':
    get_all_times()
    
