# API Documentation
This API is RESTful because:
- It is hackable up the tree
- It uses short, meaningfull names
- It uses GET, POST and DELETE on objects

The api lives in the /api/ endpoints

## Favourites
To add or remove favourites, on `/api/favourites`  
**GET:** Returns a list with all favourites (id's)  
**POST:** Adds a favourite `arguments: film=<id>`  
**DELETE:** Removes a favourite `arguments: film=<id>`  

## Films
Get a list of popular films, on `/api/films`  
**GET:** Gives the (id, title) of the 20 most popular films  
**POST:** Gives the (id, title of the *n* most popular films `arguments: aantal=<n>`  
**DELETE:** Removes a film from the index (untill restart) `arguments: film=<id>`  

### About a film
Get info about a film, on `/api/films/<id>`  
**GET:** Gives information about a film, everything from tmdb  
**DELETE:** Removes a film from the index (untill restart) `arguments: film=<id>`  


### Similar films
Get a list of similar films, on `/api/films/<id>/similar`  
**GET:** Gives (id, title) from similar films  
You can also select on criteria by using the endpoint `/films/<id>/similar/<criterium>`
for *actors*, *duration* or *genre*.


