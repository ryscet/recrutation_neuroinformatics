"""
Prepares the dataframes that are aggregated for individual and pair analysis.

"""

import sys
sys.path.append("..") # Adds higher directory to python modules path.
import pandas as pd
from load_data import data, phases
from datetime import datetime



def get_mice_phase(mouse, phase):
    """Create a dataframe with the room visits info for a single mouse in a single phase.
       The dataframes returned by this function will be aggregated into two databases, indiv_times.csv and pair_times.csv.
       
    
        Parameters
        ----------
        mouse:str
            mouse identifier from the load_data.mice variable.
            
        phase:str
            one of: PHASE 1 dark, PHASE 1 light, PHASE 2 dark, ... PHASE 3 light.
        
        Returns
        -------
        mice_phase_df: DataFrame
            A dataframe with the room visits info for a single mouse in a single phase.
            
            columns: timestamp, status, room, phase, mouse_id, event_number
            
                status - can be either 'start' or 'end', marking entering or leaving the room.
                timestamp - is the datetime for 'start' and for 'end'
                event_number - is the unnique number per each visit to the room 
    """

    data.unmask_data()
    data.mask_data(*phases.gettime(phase))
    # Because of masking only visits starting in the given phase are returned.
    start_times = data.getstarttimes(mouse)
    end_times = data.getendtimes(mouse)
    room_numbers = data.getaddresses(mouse)

    mice_phase_df = pd.DataFrame(columns = ['timestamp', 'status', 'room', 'phase', 'mouse_id', 'event_number'])
    idx = 0
 
    for st, en, room in zip(start_times, end_times, room_numbers):

        # Convert timestamps to datetime format 
        _st = datetime.fromtimestamp(st)
        _en = datetime.fromtimestamp(en)
        
        # add a new row to the dataframe, one for mouse entering and one for leaving the room
        mice_phase_df.loc[idx, ['timestamp', 'status', 'room', 'event_number']] = [_st, 'start',room, idx/2]
        mice_phase_df.loc[idx+1, ['timestamp', 'status', 'room', 'event_number']] = [_en,'end',room, idx/2]
       # Move the index by two, beacuse at each iteration we add two rows
        idx = idx + 2
    # Use the entry and leaving times as index. This will allow to easily calculate mice visit intersections and durations.
    mice_phase_df.set_index(keys = 'timestamp', drop = False, inplace = True)
    
    return mice_phase_df
    
