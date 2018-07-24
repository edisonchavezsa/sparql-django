from django.shortcuts import render
from django.shortcuts import render, render_to_response

import random, string
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
import time

from SPARQLWrapper import SPARQLWrapper, JSON
from django.template.loader import get_template
from django.http import HttpResponse, JsonResponse

from tokenize import tokenize, untokenize, NUMBER, STRING, NAME, OP
from io import BytesIO

from pycountry import countries, pycountry
from geotext import GeoText

import threading
import time

import es_core_news_md
import textacy.datasets as ds
import textacy
import spacy


#from datetime import datetime
from datetime import datetime, date, timedelta
# Create your views here.
def hola(request):
    datos = []
    nlp=spacy.load("es_core_news_md")



    if request.method == "POST":        
        text_box_value = request.POST['text_box']
        print (text_box_value)

    contenido = text_box_value
    contenido=nlp(contenido)
    docs=textacy.Doc(contenido)
    sentencias=[s for s in docs.sents]
    print(len(sentencias))
    tipos=set(ent.label_ for ent in contenido.ents)

    def cleanup(token, lower=True):
        if lower:
            token = token.lower()
        return token.strip()
    labels = set([w.label_ for w in contenido.ents])
    personas=""
    for label in labels:
        entities = [cleanup(e.string, lower=False) for e in contenido.ents if label==e.label_]
        entities = list(set(entities))
        if label== "PER":
            personas=entities
        print (label,entities)

    print("Esta son las entidades personas")


    return render(request, 'hola.html', {'datos':datos})


def decistmt(s):
    result = []
    g = tokenize(BytesIO(s.encode('utf-8')).readline) # tokenize the string
    for toknum, tokval, _, _, _  in g:
        if toknum == NUMBER and '.' in tokval:  # replace NUMBER tokens
            result.extend([
                (NAME, 'Decimal'),
                (OP, '('),
                (STRING, repr(tokval)),
                (OP, ')')
            ])
        else:
            result.append((toknum, tokval)) 
    return result


def index_view(request):
    resultados = []
    text_box_value = ""


    if request.method == "POST":        
        text_box_value = request.POST['text_box']
        print (text_box_value)

        tokens = decistmt(text_box_value)
        places = GeoText(text_box_value)

        cities = places.cities
        countries = places.countries
        
        """"for element in tokens:
            for ciudades in cities:
                if element == ciudades:
                    tokens.remove(element)
                    print ("siiissssssssssssss")
        """ 

        #extract_entities(text_box_value)

        for a in countries:
            print(a)

        for ciudades in cities:
            sparql = SPARQLWrapper("http://dbpedia.org/sparql")        
            sparql.setQuery("""
                                   SELECT distinct ?x 
                                   WHERE {  
                                        ?x a dbo:City .
                                        ?x rdfs:label ?name . 
                                        FILTER(fn:contains(?name, '"""+ciudades+"""'))  
                                   }
                               
                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            for result in results["results"]["bindings"]:
                print(result["x"]["value"])
                resultados.append((ciudades,result["x"]["value"]))
        
        



        for pais in countries:
            sparql = SPARQLWrapper("http://dbpedia.org/sparql")        
            sparql.setQuery("""
                               SELECT distinct ?x 
                               WHERE {  
                                    ?x a dbo:Country .
                                    ?x rdfs:label ?name . 
                                    FILTER(fn:contains(?name, '"""+pais+"""'))  
                               }
                           
                        """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            for result in results["results"]["bindings"]:
                print(result["x"]["value"])
                resultados.append((pais,result["x"]["value"]))


        print (len(resultados))        
        """for element in tokens:
            print (element)
        """
    return render(request, 'index.html', {'resultados':resultados})

def extract_entities(text):
    for sent in nltk.sent_tokenize(text):
        for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
            if hasattr(chunk, 'node'):
                print (chunk.node, ' '.join(c[0] for c in chunk.leaves()))



def prueba(request):
    nlp=spacy.load("es_core_news_md")
    text_box_value = ""
    paises = []
    personas = []
    ciudades = []
    resultados = []
    if request.method == "POST":        
        text_box_value = str(request.POST['text_box'])
        text = (text_box_value)
        for country in pycountry.countries:
            if country.name in text:
                paises.append(country.name)

        contenido = text_box_value
        contenido=nlp(contenido)
        docs=textacy.Doc(contenido)
        sentencias=[s for s in docs.sents]
        tipos=set(ent.label_ for ent in contenido.ents)

        def cleanup(token, lower=True):
            if lower:
                token = token.lower()
            return token.strip()
        labels = set([w.label_ for w in contenido.ents])
        
        for label in labels:
            entities = [cleanup(e.string, lower=False) for e in contenido.ents if label==e.label_]
            entities = list(set(entities))
            if label== "PER":
                personas=entities
            if label== "LOC":
                ciudades=entities
            print (label,entities)

        for per in ciudades:
            print (per)

        for temp in personas:
            print (temp)

    for ciu in ciudades:
            sparql = SPARQLWrapper("http://dbpedia.org/sparql")        
            sparql.setQuery("""
                                   SELECT distinct ?x 
                                   WHERE {  
                                        ?x a dbo:City .
                                        ?x rdfs:label ?name . 
                                        FILTER(fn:contains(?name, '"""+ciu+"""'))  
                                   }
                               
                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            for result in results["results"]["bindings"]:
                print(result["x"]["value"])
                resultados.append((ciu,result["x"]["value"]))

    for pais in paises:
            sparql = SPARQLWrapper("http://dbpedia.org/sparql")        
            sparql.setQuery("""
                               SELECT distinct ?x 
                               WHERE {  
                                    ?x a dbo:Country .
                                    ?x rdfs:label ?name . 
                                    FILTER(fn:contains(?name, '"""+pais+"""'))  
                               }
                           
                        """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            for result in results["results"]["bindings"]:
                print(result["x"]["value"])
                resultados.append((pais,result["x"]["value"]))

    for per in personas:
            sparql = SPARQLWrapper("http://dbpedia.org/sparql")        
            sparql.setQuery("""
                               SELECT distinct ?x 
                               WHERE {  
                                    ?x a dbo:Person .
                                    ?x rdfs:label ?name . 
                                    FILTER(fn:contains(?name, '"""+per+"""'))  
                               }
                           
                        """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            for result in results["results"]["bindings"]:
                print(result["x"]["value"])
                resultados.append((per,result["x"]["value"]))


    return render(request, 'prueba.html', {'resultados':resultados})