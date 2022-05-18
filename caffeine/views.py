from django.http import HttpResponse,JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import os, os.path
from .tools.down_movie import downYoutubeMp3, down_title
from .tools.stt import upload_blob_from_memory,transcribe_gcs
from .tools.sum import summary_text
from .tools.textrank import key_question
import json


models = list()
contents = list()
movie_urls = list()
movie_titles = list()

text_alls = list()

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def result(request):
    if request.method == 'POST':
        print(request.POST['address'])
        movie_url = request.POST['address']
        movie_urls.append(movie_url)
        # 동영상 이름 추출
        movie_title = down_title(movie_url).replace(":"," -")
        movie_titles.append(movie_title)

        # 파일 이름 정의
        content = movie_title + '.flac'
        contents.append(content)
        # 임베딩 링크 생성
        embed_url = movie_url.replace('watch?v=', "embed/")

        context = {
            'embed_url': embed_url,
            'movie_title': movie_title,
        }
    return render(request, 'result.html', context)

@csrf_exempt
def text(request):
    if request.method == 'POST':
        # 동영상 다운
        downYoutubeMp3(movie_urls[0])

        # 동영상 path가져오기
        path = os.getcwd()
        print(path)
        folder_yt = "yt"
        file_path = os.path.join(path, folder_yt, contents[0])
        print(file_path)
        # 동영상 스토리지 업로드
        upload_blob_from_memory("dgu_dsc_stt", file_path, contents[0])

        # 동영상 STT
        # 스토리지 path
        gcs_url = "gs://dgu_dsc_stt/"
        gcs_file = gcs_url + contents[0]
        try:
            text_all = transcribe_gcs(gcs_file, contents[0], 44100)
        except:
            text_all = transcribe_gcs(gcs_file, contents[0], 48000)

        text_alls.append(text_all)
        print(text_all)
        gen = {
            'text_all': text_all,
        }

    return JsonResponse(gen)

@csrf_exempt
def summary(request):
    if request.method == 'POST':
        # 요약문 생성
        sum_text = summary_text(text_alls[0])
        print(sum_text)

        result = {
            "sum_text" : sum_text
        }
    return JsonResponse(result)

# @csrf_exempt
# def keytext(request):
#     if request.method == 'POST':
#
#         #path 설정
#         path = os.getcwd()
#         folder_text = "text"
#         text_file = contents[0]
#
#         key_dict= key_question(os.path.join(path, folder_text, text_file))
#
#         keywords = ''
#         count = 1
#         for i in key_dict["keywords"]:
#
#             keywords += str(count) + '순위 : ' + str(i) + '<br>'
#             count += 1
#         print(keywords)
#         result ={
#             "keyword" : keywords
#         }
#     return JsonResponse(result)


@csrf_exempt
def keytext(request):
    if request.method == 'POST':

        # path 설정
        path = os.getcwd()
        folder_text = "text"
        text_file = contents[0] + ".txt"

        key_dict = key_question(os.path.join(path, folder_text, text_file))

        keywords = ''
        count = 1
        for i in key_dict["keywords"]:

            keywords += str(count) + '순위 : ' + str(i) + '<br>'
            count += 1
        print(keywords)
        result ={
            "keyword" : keywords,
            "sentence_blank" : key_dict["sentence_blank"] + '<br><br><br><br>',
            "sentence" : key_dict["sentence"] + '<br><br>',
            "answer": key_dict["answer"]
        }
    return JsonResponse(result)
