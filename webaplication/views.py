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
from django.http import HttpResponseRedirect
from django.urls import reverse

#from datetime import datetime
from datetime import datetime, date, timedelta

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
    nlp=spacy.load("es_core_news_md")
    text_box_value = ""
    paises = []
    personas = []
    ciudades = []
    resultados = []
    token = []
    if request.method == "POST":
        text_box_value = str(request.POST['text_box'])
        token = decistmt(text_box_value)
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

    #for ciu in ciudades:
    sparql = SPARQLWrapper("http://localhost:8890/sparql/gep")
    sparql.setQuery("""
                           SELECT ?name
                            WHERE {
                                ?person foaf:name ?name .
                            }

                    """)  # the previous query as a literal string
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    print(len(results))
    for result in results["results"]["bindings"]:
        print(result["name"]["value"])
        resultados.append((result["name"]["value"],"dbo:City"))


    for tok in token:
        print (tok)

    return render(request, 'index.html', {'resultados':resultados})
def search(request):
    nlp=spacy.load("es_core_news_md")

    paises = []
    personas = []
    ciudades = []
    resultados = []
    #dalsbc
    if request.method =="POST":
        search = str(request.POST['search']).upper()
        for search in search.split(' '):
            sparql = SPARQLWrapper("http://localhost:8890/sparql/datoSBC")
            sparql.setQuery("""
                                    prefix ocio:<http://www.ocio.com/>
                                    prefix schema:<http://schema.org/>
                                   SELECT DISTINCT ?nombre
                                    WHERE {
                                        ?s rdf:type ocio:Establishment .
                                        ?s schema:offer ?d .
                                        ?d foaf:name ?nombre"""
                                        +""" filter contains (?nombre,'"""+search+"""')
                                    } limit 10

                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print(results["results"])
            for result in results["results"]["bindings"]:
                resultados.append((result["nombre"]["value"],"foaf:name",result["nombre"]["value"]))

            sparql.setQuery("""
                                    prefix ocio:<http://www.ocio.com/>
                                    prefix schema:<http://schema.org/>
                                   SELECT DISTINCT ?actividad
                                    WHERE {
                                        ?s rdf:type ocio:Establishment .
                                        ?s ocio:have ?d .
                                        ?d foaf:title ?actividad """
                                        +""" filter contains (?actividad,'"""+search+"""')

                                    } ORDER BY DESC(?actividad) limit 10

                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print(results["results"])
            for result in results["results"]["bindings"]:
                print(result["actividad"]["value"])
                resultados.append((result["actividad"]["value"],"foaf:title",result["actividad"]["value"]))

            sparql.setQuery("""
                                    prefix ocio:<http://www.ocio.com/>
                                    prefix schema:<http://schema.org/>
                                    prefix dbo:<http://dbpedia.org/ontology/>
                                   SELECT DISTINCT ?locales
                                    WHERE {
                                        ?s rdf:type ocio:Establishment .
                                        ?s dbo:province ?d .
                                        ?d rdfs:label ?locales"""
                                        +""" filter contains (?locales,'"""+search+"""')
                                    } ORDER BY DESC(?locales) limit 10

                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print(results["results"])
            for result in results["results"]["bindings"]:
                resultados.append((result["locales"]["value"],"rdfs:label",result["locales"]["value"]))


            sparql.setQuery("""
                                    prefix ocio:<http://www.ocio.com/>
                                    prefix schema:<http://schema.org/>
                                   SELECT DISTINCT ?categoria ?nombre
                                    WHERE {
                                        ?s rdf:type ocio:Establishment .
                                        ?s rdfs:label ?nombre .
                                        ?s ocio:reputation ?r .
                                        ?r foaf:name ?categoria"""
                                        +""" filter contains (?categoria,'"""+search+"""')"""
                                        +"""filter regex (?nombre,'"""+search+"""')

                                    } limit 10

                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print(results["results"])
            for result in results["results"]["bindings"]:
                #print(result["categoria"]["value"])
                resultados.append((result["categoria"]["value"],"foaf:name",result["categoria"]["value"]))

            sparql.setQuery("""
                                    prefix ocio:<http://www.ocio.com/>
                                    prefix schema:<http://schema.org/>
                                    prefix dbo:<http://dbpedia.org/ontology/>
                                   SELECT DISTINCT ?fecha ?nombre
                                    WHERE {
                                        ?s rdf:type ocio:Establishment .
                                        ?s dbo:startDate ?fecha .
                                        ?s rdfs:label ?nombre"""
                                        +""" filter contains (?fecha,'"""+search+"""')"""
                                        +"""filter regex (?nombre,'"""+search+"""')
                                    } limit 10

                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print(results["results"])
            for result in results["results"]["bindings"]:
                #resultados.append((result["fecha"]["value"],"dbo:startDate"))
                resultados.append((result["nombre"]["value"],"dbo:startDate",result["fecha"]["value"]))

            sparql.setQuery("""
                                    prefix ocio:<http://www.ocio.com/>
                                    prefix schema:<http://schema.org/>
                                   SELECT DISTINCT ?telefono ?nombre
                                    WHERE {
                                        ?s rdf:type ocio:Establishment .
                                        ?s rdfs:label ?nombre .
                                        ?s schema:telephone ?telefono"""
                                        +""" filter contains (?telefono,'"""+search+"""')"""
                                        +"""filter regex (?nombre,'"""+search+"""')
                                    } limit 10

                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print(results["results"])
            for result in results["results"]["bindings"]:
                #resultados.append((result["nombre"]["value"],"rdfs:label"))
                resultados.append((result["nombre"]["value"],"schema:telephone",result["telefono"]["value"]))

            sparql.setQuery("""
                                    prefix ocio:<http://www.ocio.com/>
                                    prefix schema:<http://schema.org/>
                                    prefix dbo:<http://dbpedia.org/ontology/>
                                   SELECT DISTINCT ?correo ?nombre
                                    WHERE {
                                        ?s rdf:type ocio:Establishment .
                                        ?s rdfs:label ?nombre .
                                        ?s dbo:owner ?d .
                                        ?d schema:email ?correo"""
                                        +""" filter contains (?correo,'"""+search+"""')"""
                                        +"""filter regex (?nombre,'"""+search+"""')
                                    } limit 10

                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print(results["results"])
            for result in results["results"]["bindings"]:
                #resultados.append((result["nombre"]["value"],"rdfs:label"))
                resultados.append((result["nombre"]["value"],"schema:email",result["correo"]["value"].lower()))

            sparql.setQuery("""
                                    prefix ocio:<http://www.ocio.com/>
                                    prefix schema:<http://schema.org/>
                                    prefix dbo:<http://dbpedia.org/ontology/>
                                   SELECT DISTINCT ?repre ?nombrelocal
                                    WHERE {
                                        ?s rdf:type ocio:Establishment .
                                        ?s rdfs:label ?nombrelocal .
                                        ?s dbo:owner ?repre """
                                        +""" filter contains(?nombrelocal,'"""+search+"""')"""
                                        +"""filter regex (?repre,'"""+search+"""')
                                    } limit 10

                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print(results["results"])
            for result in results["results"]["bindings"]:
                #resultados.append((result["nombrelocal"]["value"],"rdfs:label"))
                resultados.append((result["repre"]["value"],"dbo:owner",result["nombrelocal"]["value"]))

            sparql.setQuery("""
                                    prefix ocio:<http://www.ocio.com/>
                                    prefix schema:<http://schema.org/>
                                   SELECT DISTINCT ?capacidad ?nombrelocal
                                    WHERE {
                                        ?s rdf:type ocio:Establishment .
                                        ?s rdfs:label ?nombrelocal .
                                        ?s schema:offer ?d .
                                        ?d foaf:name ?actividad .
                                        ?s schema:numberOfRooms ?capacidad
                                        FILTER contains(?actividad,'alojamiento')"""
                                        +"""filter regex (?nombrelocal,'"""+search+"""')
                                    } limit 10

                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print(results["results"])
            for result in results["results"]["bindings"]:
                #resultados.append((result["nombrelocal"]["value"],"rdfs:label"))
                resultados.append((result["nombrelocal"]["value"],"schema:numberOfRooms",result["capacidad"]["value"]))

            sparql.setQuery("""
                                    prefix ocio:<http://www.ocio.com/>
                                    prefix schema:<http://schema.org/>
                                   SELECT DISTINCT ?empleados ?nombrelocal
                                    WHERE {
                                        ?s rdf:type ocio:Establishment .
                                        ?s rdfs:label ?nombrelocal .
                                        ?s schema:numberOfEmployees ?empleados"""
                                        +""" filter contains (?empleados,'"""+search+"""')"""
                                        +"""filter regex (?nombrelocal,'"""+search+"""')
                                    } limit 10

                            """)  # the previous query as a literal string
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

            print(results["results"])
            for result in results["results"]["bindings"]:
                #resultados.append((result["nombrelocal"]["value"],"rdfs:label"))
                resultados.append((result["nombrelocal"]["value"],"schema:numberOfEmployees",result["empleados"]["value"]))

        request.session['results'] = resultados
    return HttpResponseRedirect('/')
def index(request):
    resultados=[]
    if request.session.has_key('results'):
        resultados = request.session.get('results')

        del request.session['results']
    return render(request, 'index2.html', {'resultados':resultados,'valor':len(resultados)})
