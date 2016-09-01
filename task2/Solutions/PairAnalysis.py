import sys
import os.path

sys.path.append(os.path.dirname(__file__))
sys.path.append("..")

import pandas as pd
from load_data import mice
from ParseData import get_mice_phase
import numpy as np
from itertools import combinations

def get_all_combinations():
    """Iterate over all mice pair combinations in each phase and calculate time spent in the same room.
        Results include how much time a pair of mice spent together in each room, how many times they met and average duration on each meeting.
     
        Returns
        -------
        meetings_db: DataFrame
            columns: mice_combination, room_id, phase, total_meeting_duration, number_of_meetings, average_meeting_duration
                
    """
    # Define phases to iterate over
    phases = ['PHASE 1 dark', 'PHASE 1 light', 'PHASE 2 dark', 'PHASE 2 light', 'PHASE 3 dark', 'PHASE 3 light']
    # Prepare dataframe to store the results
    meetings_db = pd.DataFrame(columns = ['mice_combination', 'room_id', 'phase', 'total_meeting_duration', 'number_of_meetings', 'average_meeting_duration'])

    # Iterate over all unique combinations of mice names
    for name_a, name_b in combinations(list(mice),2):
        print(name_a)
        for phase in phases:
            # Calculate results for the current mice pair in the current phase
            single_entry = combine_mice_pair(name_a, name_b, phase)
            # Annotate the results with mice names and phase info
            single_entry['mice_combination'] = name_a + '_' + name_b
            single_entry['phase'] = phase
            # Aggregate the results
            meetings_db = meetings_db.append(single_entry, ignore_index = True)            
    # Save results to file
    path = os.path.dirname(os.path.realpath(__file__)) + '/Solutions'
    meetings_db.to_csv(path +'/parsed_data/pair_times.csv', index = False)
    return meetings_db
    
    
def combine_mice_pair(name_a, name_b, phase):
    """ Calculate intersecting visits of a mice pair for a given phase. 
        Merge two dataframes of room visit slices on a datetime index.
        From the occupied room number subtract the room occupied by another mouse.
        Get the time slices where room difference is zero and calculate their duration.
        
        Parameters
        ----------
            name_a, name_b, phase: str,str,str
                Mice names that will make a pair, and the experiemntal phase.
        
        Returns
        -------
            database_entry: DataFrame
                columns: room_id, total_meeting_duration, number_of_meetings, average_meeting_duration
                Dataframe returned by `preapre_db_entry()`, containing visit parameters for a mice pair in a single phase.
                
                
    """    

    # Load dataframes with visits to the room indexed with timestamp
    mice_a = get_mice_phase(name_a, phase).drop(['timestamp', 'phase', 'mouse_id'], axis=1)
    mice_b = get_mice_phase(name_b, phase).drop(['timestamp', 'phase', 'mouse_id'], axis=1)

    # Joining the two dataframes on index will order the rows by timestamps. If mice_a entered a room 1, and before she left
    # mice_b also entered it, a row from mouse b dataframe will be inserted between entering and leaving rows of mouse a dataframe. 
    combined = mice_a.join(mice_b, how = 'outer', lsuffix = '_a', rsuffix = '_b')
    
    # Time slices are not consecutive, i.e. leaving room_1 is not followed by entering room_2. Instead there is a short period where mouse is not marked to be in any room
    # if not corrected (comment  linebelow) then we'll assume, mouse was already in the room to which she was heading.
    combined = fix_twilight(combined)

    # Empty rows occur when after mouse_a entered some room, mouse b was entering ad/or leaving other rooms. mice_a.join method 
    # combines two datframes on idex leaving empty columns on rows existing originally in only one dataframe.
    # Filling nans with the last valid value will fill empty rows between entering and leaving the room with the room_id.
    combined.loc[:, ['room_a', 'room_b', 'event_number_a', 'event_number_b']] = combined.loc[:, ['room_a', 'room_b', 'event_number_a', 'event_number_b']].fillna( method = 'bfill')        
    combined.loc[:, ['status_a', 'status_b']] = combined.loc[:, ['status_a', 'status_b']].fillna( value = 'inside')      
    
    # From the occupied room number subtract the room occupied by another mouse.
    combined['overlap'] = combined['room_a'] - combined['room_b']
    
    # Ucomment to plot an example 
    #fig, axes = plt.subplots(2, sharex = True)
    #axes[0].plot(combined.index, combined['room_a'], 'r', alpha = 0.5, label = 'mouse a')
    #axes[0].plot(combined.index, combined['room_b'], 'b', alpha = 0.5, label = 'mouse b') 
    #axes[1].plot(combined.index, combined['room_a'] - combined['room_b'], 'g', alpha = 0.5, label = 'room intersection')
    #axes[0].set_ylabel('room id')
    #axes[1].set_ylabel('room a - room b')
    #plt.legend()
    
    # Get dict of list with all meetings durations 
    meeting_durations = get_pair_time(combined)
    # Compute the sum, number and average duration of meetings. Save in a dataframe
    database_entry = preapre_db_entry(meeting_durations)
    
    return database_entry


def preapre_db_entry(all_durations):
    """From the dict containing list of all meetings durations, compute their sum, number and average and strore in a dataframe.
        
        Parameters
        ----------
        all_durations: dict
            Keys are room id.
            Values are lists containing duration of each overlapping visit for a mice pair in a single phase.
        
        Returns
        -------
        parsed_durations: DataFrame
            columns: room_id, total_meeting_duration, number_of_meetings, average_meeting_duration
            DataFrame with computed reults about meetings of mice pair in the same room.
    """
    # Prepare the dataframe for storing the results
    parsed_durations = pd.DataFrame(columns = ['room_id', 'total_meeting_duration', 'number_of_meetings', 'average_meeting_duration'])
   # Iterate over dict containing list with all meetings durations
    for key, value in all_durations.items():
        # Convert the list to numpy array 
        durations =np.array(value)
        # Store results for the room as a row in a dataframe
        parsed_durations.loc[key, :] =  [int(key), durations.sum(),  len(durations), durations.mean()]  
    return parsed_durations
    
    
  


def get_pair_time(combined):
    """Calculate the duration of all unique meetings in a room.
       Use the event number to identify unique meetings even if they happened consecutively in the same room.
       
       Parameters
       ----------
       combined: DataFrame
           columns: room_a, room_b, event_number_a, event_number_b, status_a, status_b, overlap
               suffixes '_a' and '_b' mark whether the information is about first or second mouse from the pair.
               room columns - mark currently occupied room.
               status - can be either start, end or inside and marks whether the mouse is entering, leaving or inside the room.
               event number - marks which visit to the room the mouse is currently at.
               overlap - identifies rows where mice are in the same room.
               index of this dataframe are timestamps, which can be used to calculate durations of slices where the mice are in the same room.
       
       Returns
       -------
       all_durations: dict
           keys are room numbers. 
           values are overlapping lists of room visits 
    """
    # Filter the rows where mice were in the same room
    same_room = combined.loc[combined['overlap'] == 0]
    # Create event identifier to mark unique events for both mice. For example, if mice was in room 1 with event number = 2, 
    # and mouse b was there in the same time but twice, with event numbers 5 and 6, then the event uniion will be 7 and 8.
    same_room['event_union'] = same_room['event_number_a'] + same_room['event_number_b']
    
    all_durations = {}
    for e_nr, meeting in same_room.groupby('event_union'):
        # Subtract the first row timestamp from the last to get the duration. Store as the duration in milliseconds.
        duration = np.array([meeting.tail(1).index.get_values()[0] - meeting.head(1).index.get_values()[0]], dtype='timedelta64[ms]').astype(int)[0]
        # room id will always be twhe same for room_a and room_b for overlapping visits
        room_id = meeting.iloc[0, meeting.columns.get_loc('room_a')] 
        # Keep appending results to a list stored in a dict. Check if the list exists, if not create it.
        if room_id not in all_durations.keys():
            all_durations[room_id] = [duration]
            
        all_durations[room_id].append(duration)
        
    return all_durations





    



def fix_twilight(combined):     
    """Between leaving a room and entering a new room, there is a short period of time when the mouse is nowhere.
        This funtion marks this special cases assigning -10 to room id.
        This prevents false positives for identyfying mice meetings.
        If not used mice will be assumed to be in the room to which she is heading instead of beeing nowhere.
        
        Parameters
        ----------
        combined: DataFrame
            columns: room_a, room_b, event_number_a, event_number_b, status_a, status_b, overlap
                       suffixes '_a' and '_b' mark whether the information is about first or second mouse from the pair.
                       room columns - mark currently occupied room.
                       status - can be either start, end or inside and marks whether the mouse is entering, leaving or inside the room.
                       event number - marks which visit to the room the mouse is currently at.
                       overlap - identifies rows where mice are in the same room.
    """
    # Collect indices where entering the room was not preceeded by leaving the previous one
    twilight_a = find_gaps(combined, 'status_a')
    twilight_b =  find_gaps(combined, 'status_b')

    # mark these indices with a special value, so they are not erroneously counted as visits in the same room
    combined.iloc[twilight_a - 1, combined.columns.get_loc('room_a') ] = -10
    combined.iloc[twilight_b - 1, combined.columns.get_loc('room_b') ] = -10

    return combined
    
def find_gaps(status_df, col_name):
    """ Finds rows where entering the room (status == 'start') is not immediately preceeded by leaving the previous room.
        These happen when one of the mice was enetering or leaving a room, when another was inbetween rooms (i.e. nowhere) in this time.
        
        Parameters
        ----------
        status_df: Series
            a 'status' column from the 'combined' dataframe, marking entering and leaving the room.
        col_name:str
            can be either 'status_a' or 'status_b'. Indicates which mouse from the pair is beeing corrected.
            
        Returns
        -------
        np.array
            indices where mouse was inbetween rooms, i.e. in the nowhere or twilight zone.
            The indices are the integer indices of entering the room, that where preceeded by Nan values.
    """
    # Convert Series to Dataframe, because we'll ad a second column 
    status_df = pd.DataFrame(status_df[col_name])
    # Move the status column one row up, so that at the same index there is current and previous status of the mouse.
    status_df['shifted'] = status_df[col_name].shift(1)

    # Find rows where entering the room was preceeded by not beeing in any room (marked as Nan) istead of leaving the previous room.
    c = pd.isnull(status_df['shifted']) & (status_df[col_name] == 'start')
    
    # Return the integer indices of such cases
    return np.where(c)[0][0:-1]
    
if __name__ == '__main__':
    get_all_combinations()

