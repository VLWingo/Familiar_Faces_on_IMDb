#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created: Jan 27 2022

@author: Victoria Wingo

Purpose: Create database of films/shows seen to compare cast
"""

from bs4 import BeautifulSoup
import requests
import pandas as pd
from ordered_set import OrderedSet
import ast


def util_func(element):
    try:
        return element['title']
    except KeyError:
        pass


def load_imdb():
    '''Reads IMDb_Pages.csv into a dataframe
    
    Args:
        None
        
    Returns:
        imdb_df: dataframe, read from IMDb_Pages.csv'''
    
    location = r"/home/tori/Documents/IMDb_Project/IMDb_Pages.csv"
    imdb_df = pd.read_csv(
        location,
        index_col = 0,
        names = [
            'Page',
            'Actors',
            'Roles'],
        converters={'Actors':ast.literal_eval, 'Roles':ast.literal_eval})
    return imdb_df


def load_actors():
    '''Reads Actors_db.csv into a dataframe
    
    Args:
        None
    
    Returns:
        actors_df: dataframe, read from Actors_db.csv'''
        
    location = r"/home/tori/Documents/IMDb_Project/Actors_db.csv"
    
    actors_df = pd.read_csv(
        location,
        index_col = 0,
        names = [
            'Appearances'],
        converters={'Appearances': ast.literal_eval})
    return actors_df


def check_pages(imdb_df, actors_df):
    '''Checks each title of imdb_df to see if it has already been 
    scraped for the list of actors, then scrapes them, updates Actors_db, 
    and saves changes to the csvs
    
    Args:
        imdb_df: dataframe, read from IMDb_Pages.csv
        
    Returns:
        imdb_df: dataframe, updated'''  

    for title in imdb_df.index:
        if not imdb_df['Actors'].loc[title]:
            imdb_df = scrape_imdb(title)
            imdb_df = scrape_roles(title)
            actors_df = update_actors(actors_df, title)
        if not imdb_df['Roles'].loc[title]:
            imdb_df = scrape_roles(title)
            actors_df = update_actors(actors_df, title)
        if imdb_df['Actors'].loc[title][0] not in actors_df.index:
            actors_df = update_actors(actors_df, title)
    return imdb_df


def scrape_imdb(title):
    '''Scrapes IMDb pages from IMDb_Pages.csv for actors and saves changes
    
    Args:
        title: string, index for imdb_df
        
    Returns:
        imdb_df: dataframe, updated'''

    location = r"/home/tori/Documents/IMDb_Project/IMDb_Pages.csv"
    page = requests.get(imdb_df['Page'].loc[title])
    soup = BeautifulSoup(page.content, 'html.parser')
    
    temp_cast = [util_func(element) for index, element 
               in enumerate(soup.select('.cast_list img'))]
    cast = [x for x in temp_cast if x]
    imdb_df['Actors'].loc[title] = cast 
    print("Length of cast for ", title, " is: ", len(cast))
    
    imdb_df.to_csv(location, header = False)   
    
    return imdb_df    


def scrape_roles(title):
    '''Scrapes IMDb pages from IMDb_Pages.csv for roles and saves changes
    
    Args:
        title: string, index for imdb_df
    
    Returns:
        imdb_df: dataframe, updated'''
    
    location = r"/home/tori/Documents/IMDb_Project/IMDb_Pages.csv"
    page = requests.get(imdb_df['Page'].loc[title])
    soup = BeautifulSoup(page.content, 'html.parser')

    toggles = [element.get_text() for index, element in enumerate(soup.select('.toggle-episodes'))]
    character = [element.get_text() for index, element in enumerate(soup.select('.character a'))]
    if len(character) == len(set(character)):
        exclusion = OrderedSet(character).symmetric_difference(set(toggles))
        roles = list(exclusion)
    else:
        roles = [x for x in character if x not in toggles]
    imdb_df['Roles'].loc[title] = roles
    print("Length of roles for ", title, " is: ", len(roles))
    imdb_df.to_csv(location, header = False)     
    return imdb_df


def update_actors(actors_df, title):
    '''Updates the Actors and their Roles in Actors_db.csv and actors_df
    
    Args:
        actors_df: dataframe, read from Actors_db.csv
        title: string, index for imdb_df
    
    Returns:
        actors_df: dataframe, updated'''
    
    location = r"/home/tori/Documents/IMDb_Project/Actors_db.csv"
    for i, actor in enumerate(imdb_df['Actors'].loc[title]):
        role = imdb_df['Roles'].loc[title][i]
        if actors_df.empty:
            print("Dataframe is empty! Initializing with first actor.")
            actor_dict = {actor: [{title: role}]}
            actors_df = pd.DataFrame.from_dict(actor_dict, orient='index', columns=['Appearances'])
        else:
            if actor not in actors_df.index:
                actors_df.loc[actor] = [{title: role}]
            else:
                if title in actors_df['Appearances'].loc[actor].keys():
                    if role != actors_df['Appearances'].loc[actor][title]:
                        list_ = [actors_df['Appearances'].loc[actor][title]]
                        list_.append(role)
                        actors_df['Appearances'].loc[actor][title] = list_
                    else:
                        print("Scraping error occured in ", title, " at ", actor, " for ", role)
                else:
                    actors_df['Appearances'].loc[actor][title] = role
                    
    actors_df.to_csv(location, header = False)
    return actors_df
    
imdb_df = load_imdb()
actors_df = load_actors()
print(check_pages(imdb_df, actors_df))
input_ = input("Who would you like to look up? (Enter x to exit) ")
if input_ == 'x':
    pass
else:
    try:
        print(actors_df['Appearances'].loc[input_])
    except KeyError:
        print("That actor is not in the database.")