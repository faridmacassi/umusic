from django.shortcuts import render
from django.http import JsonResponse
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import os
from django.http import HttpResponse
import time
from django.conf import settings
from youtubesearchpython import VideosSearch
import requests
from pydub import AudioSegment
from pytube import YouTube
from mutagen.mp3 import MP3
from mutagen.id3 import APIC, ID3, TIT2, TPE1, TALB
from datetime import datetime

def get_spotify_credentials():
    client_id = "f7d5d71ce8b143ff8041e3ead8196fda"
    client_secret = "c0af9b684328474e95ddd9cadfdc676a"
    return client_id, client_secret

def buscar_en_youtube(nombre, artista, album):
    query = f"{nombre} {artista} {album}"
    resultados = VideosSearch(query, limit=8).result()['result']
    video_data = []
    for video in resultados:
        video_info = {
            'title': video['title'],
            'link': video['link'],
            'thumbnail': video['thumbnails'][0]['url'],
            'duration': video['duration']
        }
        video_data.append(video_info)
    return video_data

def convertir_duracion(duracion):
    partes = duracion.split(':')
    if len(partes) == 2:  # mm:ss
        minutos = int(partes[0])
        segundos = int(partes[1])
        return (minutos * 60 + segundos) * 1000
    elif len(partes) == 3:  # hh:mm:ss
        horas = int(partes[0])
        minutos = int(partes[1])
        segundos = int(partes[2])
        return (horas * 3600 + minutos * 60 + segundos) * 1000
    return 0

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
            resultados_youtube = buscar_en_youtube(music_js_name, music_js_artist, music_js_album)
            # Encontrar la mejor coincidencia en YouTube basándose en la duración
            mejor_coincidencia = None
            mejor_diferencia = float('inf')
            
            for resultado in resultados_youtube:
                duracion_youtube = convertir_duracion(resultado['duration'])
                diferencia = abs(duracion_youtube - int(music_js_duracion))
                if diferencia < mejor_diferencia:
                    mejor_diferencia = diferencia
                    mejor_coincidencia = resultado
            
            if mejor_coincidencia:
                music_link_youtube = mejor_coincidencia['link']
                
                yt = YouTube(music_link_youtube)
                audio = yt.streams.filter(only_audio=True).first()
                music_1_down = audio.download()
                file_path = os.path.join(settings.BASE_DIR, 'static/mp3/temp/')

                music_2_audio = AudioSegment.from_file(music_1_down)
                music_path_down = datetime.now().strftime("%Y_%m_%d_%H_%M_%S.mp3")
                music_path_down = os.path.join(file_path, music_path_down)
                
                music_2_audio.export(music_path_down, format='mp3')
                
                response_img = requests.get(music_js_img)
                audio_new = MP3(music_path_down, ID3=ID3)
                audio_new.tags.delall('APIC')
                if response_img.status_code == 200:
                    cover_response = response_img.content
                    audio_new.tags.add(
                        APIC(
                            encoding=3,
                            type=3,
                            mime='image/jpeg',
                            desc=u'Cover',
                            data=cover_response,
                        )
                    )
                audio_new["TIT2"] = TIT2(encoding =3, text = u'{}'.format(music_js_name))
                audio_new["TPE1"] = TPE1(encoding =3, text = u'{}'.format(music_js_artist))
                audio_new["TALB"] = TALB(encoding =3, text = u'{}'.format(music_js_album))
                audio_new.save()
                
                if os.path.exists(music_path_down):
                    with open(music_path_down, 'rb') as f:
                        response = HttpResponse(f.read(), content_type='audio/mpeg')
                        response['Content-Disposition'] = 'attachment; filename="archivo.mp3"'
                        print("se envio el archivo...")
                        return response
                print(f"La música se ha descargado correctamente como {9}.")
            else:
                print("No se encontró una coincidencia adecuada en YouTube.")
                    
                    
            
            
            file_path = os.path.join(settings.BASE_DIR, 'static/mp3/temp/musica.mp3')
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='audio/mpeg')
                    response['Content-Disposition'] = 'attachment; filename="archivo.mp3"'
                    print("se envio el archivo...")
                    return response
            else:
                return HttpResponse("Archivo no encontrado", status=404)