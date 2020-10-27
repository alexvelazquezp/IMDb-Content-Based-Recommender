'''
Created on 26 oct. 2020

@author: Alex
'''
import pandas as pd

class IMDb:
    
    def __init__(self):
        global movies
        
        #Lee y devuelve el archivo con todas las películas de IMDb
        movies = pd.read_csv('IMDb movies.csv', low_memory=False)
        movies = movies[['imdb_title_id','original_title','year','genre','country','avg_vote','votes','metascore']]
        movies = movies[movies['year']!='TV Movie 2019']  #Existe un valor que no es un año. Lo borramos
        movies = movies.astype({'year':int})

        #Creamos una columan por cada género y ponemos un 1 si pertenece a él
        movies['genre'] = movies['genre'].str.split(', ')
        for index, row in movies.iterrows():
            for genre in row['genre']:
                movies.at[index, genre] = 1
        #Para poner todos los NaN como valor cero excepto la columna 'metascore'
        temp_metascore = movies['metascore']
        movies = movies.fillna(0)
        movies['metascore'] = temp_metascore
    
    #Devuelve el histórico de puntuaciones de un usuario
    def get_profile(self, n):
        user = pd.read_csv('user_profile_' + str(n) + '.csv')
        user.rename(columns={'title':'original_title'}, inplace=True)
        
        return user
    
    #Devuelve las 7 películas más populares de 2019 a hoy, 5 entre 2010 y 2019, 3 entre 2005 y 2010, y 5 entre 1990 y 2005
    def get_top20(self, user):
        top2020 = movies[movies['year']>=2019].sort_values('votes', ascending=False).head(7)
        top2010 = movies[(movies['year']>=2010) & (movies['year']<2019)].sort_values('votes', ascending=False).head(5)
        top2000 = movies[(movies['year']>=2005) & (movies['year']<2010)].sort_values('votes', ascending=False).head(3)
        top1990 = movies[(movies['year']>=1990) & (movies['year']<2005)].sort_values('votes', ascending=False).head(5)
        top20 = top2020.append(top2010.append(top2000.append(top1990)))
        top20.sort_values('year', ascending=False, inplace=True)
        top20 = top20[['imdb_title_id','original_title','year','genre','avg_vote']]
        top20 = top20[~top20['original_title'].isin(user['original_title'].tolist())]

        return top20
    
    #En función de los genéros del usuario y las valoraciones, devuelve las 20 películas que más le encajan
    def recommend(self, user):
        user_genres = self.__get_user_genres(user)
        unwatched = movies[~movies['original_title'].isin(user['original_title'].tolist())]
        unwatched_matrix = unwatched.drop(columns=['original_title','year','genre','country','avg_vote','votes','metascore'],
                                          axis=1)
        unwatched_matrix.set_index('imdb_title_id', inplace=True)
        scores = (unwatched_matrix * user_genres).sum(axis=1)
        scores = scores.to_frame()
        scores.reset_index(inplace=True)
        scores.rename({0:'score'}, axis=1, inplace=True)

        top20 = pd.merge(how='inner', left=unwatched, right=scores, left_on='imdb_title_id', right_on='imdb_title_id')
        top20 = top20[['imdb_title_id','original_title','year','genre','avg_vote','votes','score']]
        top20 = top20[(top20['votes']>20000) & (top20['avg_vote']>=7.0)]
        top20.sort_values(['score','avg_vote','year'], ascending=[False,False,False], inplace=True)
        top20.drop(columns=['votes','score'], axis=1, inplace=True)

        return top20.head(20)
    
    #Calcula porcentajes de cada género para cada usuario
    def __get_user_genres(self, user):
        user_genres = pd.merge(how='inner', 
                               left=user[['original_title']], right=movies, 
                               left_on='original_title', right_on='original_title')
        user_genres.drop(columns=['original_title','imdb_title_id','year','genre','country','avg_vote','votes','metascore'],
                         axis=1, inplace=True)
        genres = user_genres.transpose().dot(user['rating'])
        genres = genres / sum(genres)

        return genres