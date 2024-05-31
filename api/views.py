from django.shortcuts import render
from django.http import JsonResponse
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import os
from django.http import HttpResponse
import time
from django.conf import settings

def get_spotify_credentials():
    client_id = "f7d5d71ce8b143ff8041e3ead8196fda"
    client_secret = "c0af9b684328474e95ddd9cadfdc676a"
    return client_id, client_secret


# Create your views here.
def api(request):
    print(request)
    if request.method == 'POST':
        print(request)
        type_request = request.POST.get('type')
        if type_request is None:
            return None
        elif type_request == 'search':
            try : 
                name_music = request.POST.get('name')
                list_search = []
                client_id, client_secret = get_spotify_credentials()
                auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
                sp = spotipy.Spotify(auth_manager=auth_manager)
                resultados = sp.search(q=name_music, limit=5, type='track')
                canciones = resultados['tracks']['items']
                for idx, track in enumerate(canciones):
                    nombre = track['name']
                    artistas = ', '.join([artist['name'] for artist in track['artists']])
                    url = track['external_urls']['spotify']
                    portada_url = track['album']['images'][0]['url'] if track['album']['images'] else 'No disponible'
                    duracion_ms = track['duration_ms']
                    duracion_min = duracion_ms // 60000
                    duracion_seg = (duracion_ms % 60000) // 1000
                    duracion = f"{duracion_min}:{duracion_seg:02d}"
                    list_search.append({
                        'index': idx,
                        'nombre': nombre,
                        'artistas': artistas,
                        'url': url,
                        'portada_url': portada_url,
                        'duracion': duracion,
                        'duracion_ms': duracion_ms,
                        'album_name' : track['album']['name'],
                    })
                print(len(list_search))
                return JsonResponse({'list' : list_search})
            except:
                pass
        
        elif type_request == 'download':
            music_js_name = request.POST.get('name')
            music_js_artist = request.POST.get('artist')
            music_js_album = request.POST.get('album')
            music_js_duracion = request.POST.get('duracion')
            music_js_img = request.POST.get('img')

            file_path = os.path.join(settings.BASE_DIR, 'static/mp3/temp/musica.mp3')
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='audio/mpeg')
                    response['Content-Disposition'] = 'attachment; filename="archivo.mp3"'
                    print("se envio el archivo...")
                    return response
            else:
                return HttpResponse("Archivo no encontrado", status=404)