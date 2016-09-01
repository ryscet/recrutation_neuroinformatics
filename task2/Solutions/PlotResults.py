"""Each function in this script reads the computed results from csv file, plots them and saves the figures to a pdf.

"""

import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os.path
#import numpy as np
#import matplotlib.pyplot as plt
from sklearn import svm, datasets


sys.path.append(os.path.abspath(__file__))

plt.style.use('ggplot')


def plot_indiv_results():
    """Read individual results and plot how much time mice spent in each room divided by phases."""
    # Load results
    indiv_db = pd.read_csv('parsed_data/indiv_times.csv')
    
    # Plot the average time mice spent in each room in each phase
    fig1= plt.figure(figsize=(20, 10))
    
    sns.barplot(x="room_id", y="room_time", hue="phase", data=indiv_db)
    fig1.suptitle('Individual mice results - averages', fontweight = 'bold')
          
    fig1.savefig('figures/Indiv_avg.pdf')
    # Make a separate plot for each mouse
    g = sns.factorplot(x="room_id", y="room_time", hue="phase", col="mouse_id", kind = "bar", col_wrap = 4, data=indiv_db,
                       saturation = .5)
    g.despine(left = True)

    plt.tight_layout()
    
    g.fig.savefig('figures/Indiv_split.pdf')
    
def plot_pair_results():
    """ Plot the results from all mice pairs divided by room number (column) and phase (bar color).
        In the first row plot the average of the sumas of all meeting durations for all mice pairs.
        In the second row plot average number of meetings.
        In the third row plot average of a single meeting.
    """
    
    pair_db = pd.read_csv('parsed_data/pair_times.csv')
    fig, axes = plt.subplots(3, figsize=(20, 40))
    
    # plot the average of the sum of all meetings durations
    sns.barplot(x="room_id", y="total_meeting_duration", hue="phase", data=pair_db, ax = axes[0])
    # plot the average number of meetings
    p2 = sns.barplot(x="room_id", y="number_of_meetings", hue="phase", data=pair_db, ax = axes [1])
    # plot the average duration of meetings
    p3 = sns.barplot(x="room_id", y="average_meeting_duration", hue="phase", data=pair_db, ax = axes[2])
    
    # Show the legend only on the top plot
    p2.legend_.remove()
    p3.legend_.remove()
    
    fig.suptitle('Mice pair results', fontweight = 'bold')
    
    fig.savefig('figures/Pair_avg.pdf')


def plot_svm():
    """Creates a classifier for phase in room 1. Uses average meeting duration and number of meetings as features. 
        Uses support vector clustering (SVC) method."""    
    
    
    pair_db = pd.read_csv('parsed_data/pair_times.csv')

    # The phase classifier will only be constructed for room 1
    room_1 = pair_db.loc[pair_db['room_id'] == 1, :]
    
    # Change the phase column from string to numeric type, so it can be used as input to scipy machine learning functions
    num_phase = {'PHASE 1 dark' : 0, 'PHASE 1 light' : 1, 'PHASE 2 dark' : 2, 'PHASE 2 light' : 3, 'PHASE 3 dark' : 4, 'PHASE 3 light' : 5}
    room_1['phase'] = room_1['phase'].replace(num_phase)

    # 3 phases will be classified, PHASE 1 dark, PHASE 1 light, PHASE 2 dark
    room_1 = room_1.loc[room_1['phase'] <= 2,['average_meeting_duration', 'number_of_meetings', 'phase']]    
    
    # Take the 'average_meeting_duration' and 'number_of_meetings' columns and change them to np.array type
    # Transform the results by natural logarithm, they will be easier and faster to classify
    X = np.log(room_1.as_matrix()[:,:2])
    
    # Take the phase information for training the classifier
    y = room_1.as_matrix()[:,2]  

    # we create an instance of SVM and fit out data. 
    C = 1.0  # SVM regularization parameter
    svc = svm.SVC(kernel='linear', C=C).fit(X, y)
    
    # Get classification accuracy
    score = np.around(svc.score(X, y, sample_weight=None) * 100)

    # create a mesh to plot in
    h = 0.1 # step size in the mesh

    x_min, x_max = X[:, 0].min() - 0.1, X[:, 0].max() + 0.1
    y_min, y_max = X[:, 1].min() - 0.1, X[:, 1].max() + 0.1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                         np.arange(y_min, y_max, h))
                         
                             
    # Define colors for plotting so they match with previous plots from plot_pair_results()
    color_dict = {0: 'r', 1: 'b', 2: 'magenta' }
    color_map = [color_dict[phase] for phase in y]


    # Plot the decision boundary. For that, we will assign a color to each
    # point in the mesh [x_min, m_max]x[y_min, y_max].
    plt.style.use('ggplot')

    fig, axes = plt.subplots()
    
    # Classify the points from the mesh marking the areas belonging to each phase
    Z = svc.predict(np.c_[xx.ravel(), yy.ravel()])

    # Reshape for plotting in 2D
    Z = Z.reshape(xx.shape)
    
    
    # Plot the classifier results
    # Adjust the colors so they are the same on all plots
    levels = [ -1 , 0 , 1 , 2]
    cs = axes.contourf(xx, yy, Z ,levels, colors = ('r', 'b', 'magenta'), extend = 'both',antialiased = True, alpha=0.2, linewidth=1)
        
    
    # Plot also the training points
    axes.scatter(X[:, 0], X[:, 1], c=color_map)
    
    # Set figure parameters
    axes.set_xlabel('average meeting duration')
    axes.set_ylabel('number of meetigs')
    axes.set_xlim(xx.min(), xx.max())
    axes.set_ylim(yy.min(), yy.max())
    axes.set_title('SVC classification accuracy: %i %%'%(score))

    
    # make the legend
    artists, labels = cs.legend_elements()
    L = plt.legend(artists[1:-1], labels[1:-1], handleheight=2, loc = 'lower left')
    L.get_texts()[0].set_text('PHASE 1 dark')
    L.get_texts()[1].set_text('PHASE 1 light')
    L.get_texts()[2].set_text('PHASE 2 dark')
    
    fig.savefig('figures/svc_phase.pdf')

if __name__ == '__main__':
    plot_indiv_results()
    plot_pair_results()
    plot_svm()