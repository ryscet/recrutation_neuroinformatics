# -*- coding: utf-8 -*-
"""
Parses the results from csv files into a single dataframe. 
Uses seaborn to find correlation between average size and age and between average intensity and age.
"""


import csv
import glob
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot  as plt


def make_img_database():
    """Parses results of imaging into a dataframe.
       
       Returns
       -------
       img_database: DataFrame
           columns: No, Size, Intensity, Animal_number, Picture_number, Age
           Dataframe where cells size and intensity are marked with animal age and number
    """
    
    img_paths = glob.glob('imgdata/*')
    img_database = pd.DataFrame(columns = ['No', 'Size', 'Intensity','Animal_number', 'Picture_number', 'Age'])

    # Iterate over all images
    for path in img_paths:
        # use the first 3 rows to extract Animal number, Picture Number and Age iformation
        reader = csv.reader(open(path))
        img_info = {}
        for idx, row in enumerate(reader):
            img_info[row[0]] = row[1]
            if(idx >= 2):
                break
        # Use the remaining rows of the csv file to extract size and intensity ino
        df = pd.read_csv(path, header = 3)

        # Annotate size and intensity rows with information from the first three rows

        df['Animal_number'] = int(img_info['Animal number'])
        df['Picture_number'] = int(img_info['Picture number'])
        df['Age'] = int(img_info['Age'])
        
        # Aggregate results from all images        
        img_database = img_database.append(df, ignore_index = True)
        
        # Save to a file
        img_database.to_csv('img_database.csv', index = False)
        
    return img_database


def plot_correlation():
    """Calculate the average of intensity and size per animal, then correlate with age.
       Note
       ----
       some animals have the same age.
       
    """
    
    fig, axes = plt.subplots(2, figsize = (20, 40))
    
    img_db = pd.read_csv('img_database.csv')

    # Uncomment to see the boxplots of size and intensity per animal - correlation is seldom visible like that. 
   # sns.boxplot(x = 'Age', y = 'Size', hue = 'Animal_number', ax = axes[0],palette="Set3", width = 2, data = img_db)
   # sns.boxplot(x = 'Age', y = 'Intensity', hue = 'Animal_number', ax = axes[1],palette="Set3", width = 2, data = img_db)
   # fig.savefig('size_int_boxes.pdf')

    # Calculate the average size and intensity per animal number
    grouped = img_db.groupby(['Age', 'Animal_number'], as_index = False)
    avg_db = grouped.aggregate(np.mean)

    # Correlate the averages with age
    size = sns.jointplot(x = 'Age', y = "Size", data=avg_db, kind="reg")
    intensity = sns.jointplot(x = 'Age', y = 'Intensity', data=avg_db, kind="reg",marginal_kws={'bins':6}, **{'x_jitter':0, 'color':'b'})
    
    size.fig.savefig('size_age.pdf')
    intensity.fig.savefig('intensity_age.pdf')

if __name__ == '__main__':
    plot_correlation()
