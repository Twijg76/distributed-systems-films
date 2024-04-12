from flask import Flask
from flask import request, jsonify
from flask_restful import Resource, Api
import requests

app = Flask(__name__)
api = Api(app)


favourites = set()
deleted = set()

tmdb_api_key: str = ""
tmdb_base_url: str = "https://api.themoviedb.org/3/"

def get_n_first_movies(n: int):
    page: int = 1
    # get enough pages to get n movies

    url: str = tmdb_base_url + "movie/popular?api_key=" + tmdb_api_key + "&page=" + str(page)
    r = requests.get(url)
    results = r.json()["results"]
    # remove deleted films
    res2 = results.copy()
    for film in res2:
        if str(film["id"]) in deleted:
            results.remove(film)
    """
    for film in results:
        if str(film["id"]) in deleted:
            results.remove(film)
    """
    while len(results) <= n:
        page += 1
        r = requests.get(tmdb_base_url + "movie/popular?api_key=" + tmdb_api_key + "&page=" + str(page))
        results += r.json()["results"]
        # remove deleted films
        for film in results:
            if str(film["id"]) in deleted:
                results.remove(film)
    output = []
    for res in results:
        if res["id"] not in deleted:
            output.append((res["id"], res["title"]))
    return output[:n]

def get_movies_with_same_two_actors(movie_id: int):
    url = tmdb_base_url + "movie/" + str(movie_id) + "/credits?api_key=" + tmdb_api_key
    
    r = requests.get(url)
    actors = r.json()["cast"][:2]
    actor1 = actors[0]["id"]
    actor2 = actors[1]["id"]
    url = tmdb_base_url + "discover/movie?api_key=" + tmdb_api_key + "&with_cast=" + str(actor1) + "&with_cast=" + str(actor2)
    r = requests.get(url)
    output = []
    for res in r.json()["results"]:
        output.append((res["id"], res["title"]))
    for film in output:
        if str(film[0]) in deleted:
            output.remove(film)
    return output

def get_movies_with_same_duration(movie_id: int):
    url = tmdb_base_url + "movie/" + str(movie_id) + "?api_key=" + tmdb_api_key
    r = requests.get(url)
    duration = r.json()["runtime"]
    # get movies with duration between 10 minutes shorter or longer:
    url = tmdb_base_url + "discover/movie?api_key=" + tmdb_api_key + "&with_runtime.gte=" + str(duration-10) + "&with_runtime.lte=" + str(duration+10)
    r = requests.get(url)
    output = []
    for res in r.json()["results"]:
        runtime = get_movie(res["id"])["runtime"]
        output.append((res["id"], res["title"], runtime))
    for film in output:
        if str(film[0]) in deleted:
            output.remove(film)
    return output

def get_movies_with_same_genre(movie_id: int):
    # Find movies with the same list of genres
    url = tmdb_base_url + "movie/" + str(movie_id) + "?api_key=" + tmdb_api_key
    r = requests.get(url)
    genres = r.json()["genres"]
    r = requests.get(url)
    url = tmdb_base_url + "discover/movie?api_key=" + tmdb_api_key + "&with_genres="
    for genre in genres:
        url += str(genre["id"]) + ","
    url = url[:-1]
    r = requests.get(url)
    output = []
    for res in r.json()["results"]:
        output.append((res["id"], res["title"]))
    for film in output:
        if str(film[0]) in deleted:
            output.remove(film)
    return output

def get_movie(movie_id: int):
    url = tmdb_base_url + "movie/" + str(movie_id) + "?api_key=" + tmdb_api_key
    r = requests.get(url)
    return r.json()

def get_movie_score(movie_id: int):
    url = tmdb_base_url + "movie/" + str(movie_id) + "?api_key=" + tmdb_api_key
    r = requests.get(url)
    return r.json()["vote_average"]

def get_similar_movies(movie_id: int):
    url = tmdb_base_url + "movie/" + str(movie_id) + "/similar?api_key=" + tmdb_api_key
    r = requests.get(url)
    output = []
    for res in r.json()["results"]:
        output.append((res["id"], res["title"]))
    for film in output:
        if str(film[0]) in deleted:
            output.remove(film)
    return output

def get_quickchart(filmnames: list[str], scores: list[int]) -> str:
    url = "https://quickchart.io/chart?c={type:'bar',data:{labels:" + str(filmnames) + ",datasets:[{label:'Average score',data:" + str(scores) + "}]}}"
    return url


class Film(Resource):
    def get(self, film_id):
        return get_movie(film_id)

    def delete(self, film_id):
        deleted.add(film_id)
        if film_id in favourites:
            favourites.remove(film_id)
        return "gelukt", 204

class Favourites(Resource):
    def get(self):
        return list(favourites)
        #return jsonify(favourites=list(favourites))
    def post(self):
        #args = parser.parse_args()
        #favourites.append(args['film'])
        favourites.add(request.form['film'])
        return "gelukt", 201
    def delete(self):
        favourites.remove(request.form['film'])
        return "gelukt", 204

# Best niet gebruiken, enkel om te testen
class Deleted(Resource):
    def get(self):
        return list(deleted)
        #return jsonify(deleted=list(deleted))
    def post(self):
        deleted.add(request.form['film'])
        return "gelukt", 201
    def delete(self):
        deleted.remove(request.form['film'])
        return "gelukt", 204

class Films(Resource):
    def get(self):
        aantal = 25
        films = get_n_first_movies(25)
        return jsonify(films)

    def post(self):
        aantal = request.form['aantal']
        films = get_n_first_movies(int(aantal))
        return jsonify(films)

        
    def delete(self):
        deleted.add(request.form['film'])
        if request.form['film'] in favourites:
            favourites.remove(request.form['film'])
        return "gelukt", 204

class Similar(Resource):
    def get(self, film_id):
        films = get_similar_movies(film_id)
        for film in films:
            if str(film["id"]) in deleted:
                films.remove(film)
        output = []
        for film in films:
            output.append({"id": film["id"], "title": film["title"]})
        return output


class SimilarCrit(Resource):
    def get(self, film_id, criterium):
        if criterium == "actors":
            films = get_movies_with_same_two_actors(film_id)
        elif criterium == "duration":
            films = get_movies_with_same_duration(film_id)
        elif criterium == "genre":
            films = get_movies_with_same_genre(film_id)
        else:
            return "Criterium niet herkend", 400
        return jsonify(films)

def get_chart(filmids: list[int]) -> str:
    filmnames = []
    scores = []
    i = 1
    for filmid in filmids:
        # Because filmnames contain all kinds of special characters, for now just return their number as label, not their names
        #filmnames.append(get_movie(int(filmid))["title"])
        filmnames.append(str(i))
        i += 1
        scores.append(get_movie_score(int(filmid)))
    return get_quickchart(filmnames, scores)

@app.route("/")
def hello_world():
    films = get_n_first_movies(25)
    out = "<html><body><h1>Top 10 films</h1><ol>"
    ids = []
    for film in films:
        ids.append(film[0])
        out += "<li> <a href=\"/film/" + str(film[0]) + "\">" + film[1] + "</a></li>" 
    out += "</ol>"
    out += "<a href=\"favourites\">Favourites</a>"
    out += "<img src=\"" + str(get_chart(ids)) + "\">"
    out += "</body></html>"
    return out

@app.route("/film/<film_id>")
def filminfo(film_id):
    filminfo = get_movie(film_id)
    out = "<html> <body> <h1>" + filminfo["title"] + "</h1>"
    out += "<img src=\"https://image.tmdb.org/t/p/w500" + filminfo["poster_path"] + "\">"
    out += "<p>" + filminfo["overview"] + "</p>"
    out += "<p>Score: " + str(filminfo["vote_average"]) + "</p>"
    #out += "<form action=\"/api/films/" + film_id + "\" method=\"DELETE\">" + "<input type=\"submit\" value=\"Delete\"></form>"
    out += '<br/><a href=""" onclick="addFav(' + film_id + ')">Add to favourites</a>'
    out += "<script>function addFav(film_id) {fetch('/api/favourites', {method: 'POST', body: new URLSearchParams('film=' + film_id)})}</script>"
    out += '<br/><a href="#" onclick="removeFav(' + film_id + ')">Remove from favourites</a>'
    out += "<script>function removeFav(film_id) {fetch('/api/favourites', {method: 'DELETE', body: new URLSearchParams('film=' + film_id)})}</script>"
    out += '<br/><a href="#" onclick="deleteFilm(' + film_id + ')">Delete film</a>'
    out += "<script>function deleteFilm(film_id) {fetch('/api/films/' + film_id, {method: 'DELETE'})}</script>"
    out += '<br/><a href="/film/' + film_id + '/similar">Similar movies</a>'
    out += "</body></html>"
    return out

@app.route("/film/<film_id>/similar")
def similarfilm(film_id):
    films = get_similar_movies(film_id)
    out = "<html><body><h1>Similar movies</h1><ul>"
    for film in films:
        out += "<li> <a href=\"/film/" + str(film[0]) + "\">" + film[1] + "</a></li>" 
    out += "</ul>"
    out += '<a href="/film/' + film_id + '/similar/actors">Similar movies by actors</a>'
    out += '<br/><a href="/film/' + film_id + '/similar/duration">Similar movies by duration</a>'
    out += '<br/><a href="/film/' + film_id + '/similar/genre">Similar movies by genre</a>'
    out += "</body></html>"
    return out

@app.route("/film/<film_id>/similar/<criterium>")
def similarcritfilm(film_id, criterium):
    if criterium == "actors":
        films = get_movies_with_same_two_actors(film_id)
    elif criterium == "duration":
        films = get_movies_with_same_duration(film_id)
    elif criterium == "genre":
        films = get_movies_with_same_genre(film_id)
    else:
        return "Criterium niet herkend", 400
    out = "<html><body><h1>Similar movies" + criterium + "</h1><ul>"
    for film in films:
        out += "<li> <a href=\"/film/" + str(film[0]) + "\">" + film[1] + "</a></li>"
    out += "</ul>"
    out += "</body></html>"
    return out


@app.route("/favourites")
def favs():
    out = "<html><body><h1>Favourites</h1><ul>"
    ids = []
    for film in favourites:
        ids.append(film)
        out += "<li> <a href=\"/film/" + str(film) + "\">" + get_movie(film)["title"] + "</a></li>" 
    out += "</ul>"
    out += "<img src=\"" + get_chart(ids) + "\">"

    out += "</body></html>"
    return out


api.add_resource(Film, '/api/films/<film_id>')
api.add_resource(Favourites, '/api/favourites')
api.add_resource(Deleted, '/api/deleted')
api.add_resource(Films, '/api/films')
api.add_resource(Similar, '/api/films/<film_id>/similar')
api.add_resource(SimilarCrit, '/api/films/<film_id>/similar/<criterium>')

if __name__ == '__main__':
    if tmdb_api_key == "":
        print("no API-token")
    else:
        app.run(debug=True)

