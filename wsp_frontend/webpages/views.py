# This Python file uses the following encoding: utf-8
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import Template
from django.template.loader import get_template
from django.utils import simplejson
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import Counter # genutzt für statistische Auswertungen
import itertools
import urllib
import requests
from show import show

import pprint
pp = pprint.PrettyPrinter(indent=4)


# Dictionary für Umwandlung der Sprachkürzel in ausgeschriebene Sprachen (ISO 639-3 specifier)
languages = {
#"ger": "german",
#"eng": "english",
#"fra": "france",
#"lat": "latin",
#"grc": "greek",
#"ara": "arabic",
#"ita": "italian",
#"nld": "dutch",
#"zho": "chinese",
"ger": u"Deutsch",
"eng": u"Englisch",
"fra": u"Französisch",
"lat": u"Latein",
"grc": u"Griechisch",
"ara": u"Arabisch",
"ita": u"Indisch",
"nld": u"Niederländisch",
"zho": u"Chinesisch",
 }


base_url = "http://wspdev.bbaw.de"
#import pdb; pdb.set_trace()

def search_form(request):
    return render_to_response('search_form.html')

def hello_world(request):
    template = get_template('base.html')

    url = base_url + "/wspCmsWebApp/query/QueryDocuments"

    request_options = {'query': 'a', 'outputFormat': 'json'}
    response = requests.get(url, params=request_options)
    show(response.url)

    reply = response.text

    show(reply)

    try:
        data = simplejson.loads(reply)
    except:
        print "Fehler beim JSON-Parsing\n" + reply
        #XXX ToDO: Fehlerpage rendern!

    totalDocuments = data["sizeTotalDocuments"]
    #show(totalDocuments)
    #url = base_url + "/wspCmsWebApp/query/QueryDocuments?" + post_data + "&outputFormat=json" + translate + "&" + page_data

    results = {'totalDocuments':totalDocuments}

    return render_to_response('search_form.html', results)

def search(request):

    ressourceTypes = {"application/pdf":"pdf",
                        "application/xml":"xml",
    }

    post_data = ''
    translate = ''
    translateQuery = False
    page = 1
    pagesize = 10

    query_parameters = ''

    try:
        if request.GET['morphologicalSearch'] == 'on':
            morphologicalSearch = True
            query_parameters = query_parameters + '&morphologicalSearch=on'
        else:
            morphologicalSearch = False
        #print "request.GET['morphologicalSearch']: " + request.GET['morphologicalSearch']
    except KeyError, e:
        morphologicalSearch = False

    if 'query' in request.GET:
        querydata = request.GET['query']
        querydata = querydata.encode("utf-8")
        original_query = querydata.strip()
        #show(original_query)

        #XXX Hier fehlt ein korrekter Parser & Transformation von Suchquery zu Lucene-Syntax
        if not '"' in original_query:
            querydata = "+" + " +".join(original_query.split(" "))

        # XXX Krudes Parsen falls Phrasensuche mit '"'
        # XXX TODO Macht Fehler wenn die Quotes im Query nicht richtig geschlossen sind
        if '"' in original_query:
            Queries = []
            for s in original_query.split(' "'):
                if '"' in s:
                    Queries.append('"' + s.strip('"') + '"')
                else:
                    Queries.append(s)
            querydata = "+" + " +".join(Queries)
            show(querydata)

        if original_query == '*':
            querydata = '*'

        post_data = [('query', querydata)]
        post_data = urllib.urlencode(post_data)


        # Wenn kein Suchterm eingegeben ist, wird das Suchformular angezeigt
        if querydata == "":
            print "Empty Query"
            return render(request, 'search_form.html')

    # Abfrage für Facette "AutorInnen"
    if 'author' in request.GET:
        authorFilter = []
        for author in request.GET.getlist('author'):
            authorFilter.append('"' + author + '"')
            # Für Seitennavigation/Umblättern werden die Facettenoptionen in query_paramters gespeichert,
            # daraus wird im Template dann entsprechend eine URL generiert
            query_parameters = query_parameters + "&author=" + author
    else:
        authorFilter = ""

    # Abfrage für Facette "Projekte/Vorhaben"
    if 'project' in request.GET:
        projectFilter = []
        for project in request.GET.getlist('project'):
            projectFilter.append('"' + project + '"')
            # Für Seitennavigation/Umblättern werden die Facettenoptionen in query_paramters gespeichert,
            # daraus wird im Template dann entsprechend eine URL generiert
            query_parameters = query_parameters + "&project=" + project
    else:
        projectFilter = ""

    # Abfrage für Facette "Sprachen"
    if 'language' in request.GET:
        languageFilter = []
        for language in request.GET.getlist('language'):
            languageFilter.append('"' + language + '"')
            # Für Seitennavigation/Umblättern werden die Facettenoptionen in query_paramters gespeichert,
            # daraus wird im Template dann entsprechend eine URL generiert
            query_parameters = query_parameters + "&language=" + language
    else:
        languageFilter = ""

    # Überprüfung ob moreLikeThis als Paramete in der Anfrage-URL enthalten ist
    try:
        if request.GET["morelikethis"] == "true":
            more_like_this = True
    except KeyError, e:
        more_like_this = False
    #print "moreLikeThis: " + str(more_like_this)

    if "translateCheck" in request.GET:
        if request.GET['translateCheck'] == "on":
            translateQuery = True
            translate = [("translate", "true")]
            translate = "&" + urllib.urlencode(translate)
            query_parameters = query_parameters + '&translateCheck=on'
    if "page" in request.GET:
        # Cast to integer, damit die Berechnung der angezeigten Seiten (s. u.) richtig funktioniert
        page = int(request.GET['page'])

    page_data = [("page", page)]
    page_data = urllib.urlencode(page_data)

    # AutorInnen-Facette zur query hinzufügen
    if authorFilter:
        querydata = querydata + " +author:(" + " ".join(authorFilter) + ")"

    # Projekt-Facette zur query hinzufügen
    if projectFilter:
        querydata = querydata + " +collectionNames:(" + " ".join(projectFilter) + ")"

    # Sprachen-Facette zur query hinzufügen
    if languageFilter:
        querydata = querydata + " +language:(" + " ".join(languageFilter) + ")"

    #base_url = "http://wspdev.bbaw.de"
    #base_url = "http://192.168.1.199:8080"
    #base_url = "http://192.168.1.203:8080"

    show(querydata)
    request_options = {'query': querydata, 'outputFormat': 'json', 'page': page, 'pagesize': pagesize, 'translate': str(translateQuery).lower()}

    if morphologicalSearch == True:
        request_options['fieldExpansion'] = "allMorph"

    #url = base_url + "/wspCmsWebApp/query/QueryDocuments?" + post_data + "&outputFormat=json" + translate + "&" + page_data

    url = base_url + "/wspCmsWebApp/query/QueryDocuments?"

    # XXX moreLikeThis ist noch ein ziemlicher Hack! Die URL/IP muss hier auch noch angepasst werden (Josefs Installation bzw. wspdev kann das noch nicht!
    if more_like_this == True:
        #url = "http://192.168.1.199:8080/wspCmsWebApp/MoreLikeThis?docId=" + querydata + "&outputFormat=json"
        url = base_url + "/wspCmsWebApp/query/MoreLikeThis?docId=" + querydata + "&outputFormat=json"
        request_options = {}

#    h = httplib2.Http(".cache")
#    response, content = h.request(url)
    #print response
    #XXX hier muss geprüft werden, ob die Anfage erfolgreich war (d. h. Statuscode 200)

#    reply = content

    response = requests.get(url, params=request_options)
    #print "\nAnfrage an: " + response.url
    show(response.url)

    reply = response.text

    #print reply
    #reply = "{\"search_term\":\"Haus\",\"number_of_hits\":46,\"hit_locations\":[{\"project\":\"Post von drueben\",\"url\":\"http://#\"},{\"project\":\"Etymologisches Wörterbuch\",\"url\":\"value\"}],\"hits\":[{\"url\":\"http://telotadev.bbaw.de:8085/exist/rest/db/mgh/data/610816a.xml\",\"fragment\":\"Wilhelm I. von Meißen ein Haus in Prag in der Altstadt, bei dem Kloster St. Jakob gelegen. Karl IV. hatte dieses Haus bereits 1348 Okt. 31 Markgraf Friedrich II. von Meißen, dem Vater der drei\"},{\"url\":\"http://telotadev.bbaw.de:8085/exist/rest/db/mgh/data/740309a.xml\",\"fragment\":\"als Markgrafen von Brandenburg dem Edlen Friedrich von Torgau, Herrn zu Zossen, Haus und Stadt Zossen\"},{\"url\":\"http://telotadev.bbaw.de:8085/exist/rest/db/pvd/briefe/M%C3%BCFro_1986-02-07.xml\",\"fragment\":\"Herzliche Güße Dir und allen Lieben von Haus zu Haus Deine Marlies\"}]}"

    try:
        data = simplejson.loads(reply)
    except:
        print "Fehler beim JSON-Parsing\n" + reply
        #XXX ToDO: Fehlerpage rendern!

    results = {}

    # XXX: Warum die folgende Zeile? wofür wird translated auf TRUE gesetzt?
    results["translated"] = True

    results["totalDocuments"] = data["sizeTotalDocuments"]
    results["personList"] = []
    #results["search_term"] = data["searchTerm"].replace("tokenOrig:", "", 1)
    results["search_term"] = original_query
    results["search_term"] = results["search_term"].replace("tokenMorph:", "", 1)
    results["search_term"] = results["search_term"].strip("()")

    results["number_of_hits"] = int(data["numberOfHits"])
    results["morphologicalSearch"] = morphologicalSearch
    results["translateSearch"] = translateQuery
    results["treffer"] = ""

    projekte = set()

    if results["number_of_hits"] > 0:
        treffer = []
        for j, single_treffer in enumerate(data["hits"]):
            #print(single_treffer)

            # Herumarbeiten um Fehler in Volltextindex (z. B. Suchanfrage "Haus")

            i = {}
            i["relevantPersons"] = []
            i["places"] = []
            i["docId"] = "none"
            i["projectRdfURI"] = ""

            # Nummerierung der Treffer, da die Angaben nicht im JSON enthalten sind
            # 1 wird addiert, da die Zählung von j in der Schleife bei 0 beginnt
            i["hitNumber"] = ( page - 1) * pagesize + j + 1

            #docID parsen
            try:
                i["docId"] = single_treffer["docId"]
            except:
                #print "KeyError docId"
                pass

            #webURI (Rücksprungadresse) parsen
            try:
                i["url"] = single_treffer["webUri"].encode("utf-8")
            except:
                #print "KeyError webUri @ " + i["docId"]
                i["url"] = single_treffer["uri"].encode("utf-8")
                pass

            #Fragmente mit Trefferexzerpten parsen
            i["fragments"] = []
            for fragment in single_treffer["fragments"]:
                fragment = fragment.encode("utf-8")

                # XXX müsste auch wieder zu UTF-8 werden
                i["fragments"].append(fragment)

            #Autorinformation parsen
            i["author"] = []
            try:
                for single_author in single_treffer["author"]:
                    i["author"].append(single_author["name"])
            except KeyError, e:
                #print "KeyError author " + i["docId"]
                pass

            #Titel parsen
            try:
                i["title"] = single_treffer["title"].replace(" TITEL DES BRIEFS", "", 1)
            except KeyError, e:
                # Wenn kein Titel vorhanden ist, wird die URL zum Dokument als Titel genommen
                i["title"] = i["url"]
                #print "KeyError title " + i["docId"]
                pass

            try:
                i["collectionName"] = single_treffer["project"]["name"]
                i["collectionURL"] = single_treffer["project"]["url"]
                i["collectionID"] = single_treffer["project"]["id"]
                projekte.add(i["collectionID"])
            except KeyError, e:
                #print "KeyError collectionName " + i["docId"]
                pass

            try:
                i["type"] = ressourceTypes[single_treffer["type"]]
            except KeyError, e:
                #print error...
                i["type"] = "undefined"
                pass

            #RDF URI parsen
            try:
                i["projectRdfURI"] = single_treffer["rdfUri"]
            except KeyError, e:
                pass

            #Personeninformationen parsen
            try:
                for single_person in single_treffer["persons"]:
                    person = {"name":"Testname", "url":"http://example.org", "role":"unknown"}
                    person = {"name":single_person["name"], "url": single_person["referenceAbout"], "role": single_person["role"]}
                    i["relevantPersons"].append(person)
                    if not person["role"] == "editor":
                        results["personList"].append(person["name"])
                    #print person
            except KeyError, e:
                #print "KeyError persNames " + i["docId"]
                pass

            # Notwending, falls eine Person im JSON nur "null" ist, und keine zugehörigen Werte hat:
            except TypeError, e:
                pass

            try:
                for single_place in single_treffer["places"]:
                    place = {"place":"Beispielshausen", "url":"http://example.org"}
                    place = {"place":single_place["name"], "url":single_place["link"]}
                    i["places"].append(place)
                    #print place
            except KeyError, e:
                #print "KeyError places " + i["docId"]
                #print "KeyError places"
                pass
            #
            # Duplikate aus Personen- und Ortslisten entfernen
            #

            newlist = []
            for person_entry in sorted(i["relevantPersons"], key = lambda elt: elt["name"]):
                if newlist == [] or person_entry["name"] != newlist[-1]["name"]:
                    newlist.append(person_entry)
            i["relevantPersons"] = newlist

            newlist = []
            for place_entry in sorted(i["places"], key = lambda elt: elt["place"]):
                if newlist == [] or place_entry["place"] != newlist[-1]["place"]:
                    newlist.append(place_entry)
            i["places"] = newlist
            #print "E: " + i["docId"] + "   " + i["type"]
            treffer.append(i)
            #pp.pprint(i)
            #show(i)
        results["treffer"] = treffer

        # facets parsen
        results["authorFacet"] = []
        results["projectFacet"] = []
        results["languageFacet"] = []
        for single_author in data["facets"]["author"]:
            authorName = single_author["value"]
            authorCount = single_author["count"]
            author = {"name":authorName, "count": authorCount}
            results["authorFacet"].append(author)
        for single_project in data["facets"]["collectionNames"]:
            projectName = projectShortname = single_project["value"]
            projectCount = single_project["count"]
            projectRDFUri = single_project["rdfUri"]
            project = {"project": projectName, "count": projectCount, "rdfURI": projectRDFUri, "projectShortname": projectShortname}
            results["projectFacet"].append(project)
        for single_language in data["facets"]["language"]:
            languageID = single_language["value"]
            languageCount = single_language["count"]
            try:
                languageText = languages[languageID]
            except KeyError:
                languageText = languageID
            language = {"languageID": languageID, "count": languageCount, "language": languageText}
            results["languageFacet"].append(language)

        treffer_list = results["treffer"]
        treffer_save = []
        treffer_save = results["treffer"][:]

        # Anfrage der Projektmetadaten (für die Projekte in projekte)
        results["projektMetadaten"] = dict()
        rdfURL = "http://wspdev.bbaw.de" + "/wspCmsWebApp/query/QueryMdSystem"
        #rdfURL = "http://192.168.1.199" + "/wspCmsWebApp/query/QueryMdSystem"
        for projekt in results["projectFacet"]:
            # Wenn es keine RDF URI gibt, dann muss der Triplestore auch nicht angefragt werden
            # XXX Wie soll mit Projekten umgegangen werden, die keine RDF-URI haben (edoc, wfe, bkvb, ...)
            if projekt["rdfURI"] == "none":
                continue

            #print("Requesting Metadata for " + projekt["rdfURI"])
            request_options_rdf = {'detailedSearch': 'true', 'outputFormat': 'json', 'query': projekt["rdfURI"], 'isProjectId': 'true'}

            # Fehler auf Serverseite umgehen
            # Beispiel:
            # http://wspdev.bbaw.de/wspCmsWebApp/query/QueryMdSystem?query=http%3A%2F%2Fwsp.normdata.rdf%2FAvHForschungsstelle&detailedSearch=true&isProjectId=true&outputFormat=json
            # liefert eine Exception
            # show(rdfURL)
            try:
                response = requests.get(rdfURL, params=request_options_rdf)
                #show(response.url)
            except UnicodeEncodeError, error:
                continue

            #print(response.url)

            try:

                projektMetadaten = simplejson.loads(response.text)

                # verwendete Variablen mit "NA" initieren (falls Metadaten aus dem Triplestore nicht vollständig sind)
                projectName = projectStatus = projectAbstract = webURI = rdfURI = projectShortname = "NA"

                if projektMetadaten["hitGraphes"] != []:
                    for o in projektMetadaten["hitGraphes"][0][projekt["rdfURI"]]:

                        if "name" in o:
                            #print(o["name"])
                            projectName = o["name"]
                            #show(projectName)
                        else:
                            pass
                        if "status" in o:
                            projectStatus = o["status"]
                        if "abstract" in o:
                            projectAbstract = o["abstract"]
                        if "homepage" in o:
                            webURI = "http://" + o["homepage"]
                        rdfURI = projekt["rdfURI"]
                    # XXX ToDo:
                    # Die Metadaten zu den Projekten/Vorhaben in sinnvolle Datenstruktur überführen.
                    # Wie soll im Template darauf zugegriffen werden? Eventuell diese Daten direkt in
                    # entsprechende Facetten-Datenstruktur einfügen?
                    #if projectAbstract == "NA":
                    #    show(response.url)
                    projectShortname = projekt["project"]
                    projektDaten = {"name": projectName, "status": projectStatus, "abstract": projectAbstract, "webURI": webURI, "rdfURI": rdfURI, "projectShortname": projectShortname}
                    #show(projektDaten)


                results["projektMetadaten"][projekt["rdfURI"]] = projektDaten
            except Exception, e:
                #print(e)
                #print(response.url)
                pass
                #print "Fehler beim JSON-Parsing\n" + reply

        #pp.pprint(results["projektMetadaten"])
        #print(results["projektMetadaten"])
        #XXX ToDO: Fehlerpage rendern!
        #print "\nAnfrage an: " + response.url
        #show(response.url)
        #reply = response.text


        # Paginierung
        # XXX Dokumentieren, wie genau die Seitennummerierung hier funktioniert!
        # XXX Die Addition von number_of_hits % 10 ist notwendig, um auf der letzten Seite (z. B. 24 von 24) nicht eine Seite zu wenig anzuzeigen.
        # XXX Muss genauer nachvollzogen werden.
        for x in range(10, (results["number_of_hits"] + (int(results['number_of_hits']) % 10))):
            treffer_list.append("TEST")


        #print(len(treffer_list))



        paginator = Paginator(treffer_list, 10)

        #print "paginator.count: " + str(paginator.count) # + (int(results['number_of_hits']) % 10))

        #page = request.GET.get("page")
        #print page

        try:
            treffer = paginator.page(page)
        except PageNotAnInteger:
            treffer = paginator.page(1)
        except EmptyPage:
            treffer = paginator.page(paginator.num_pages)

        #XXX next: überzählige Einträge aus treffer_list entfernen,
        #show(projekte)

        #print treffer
        #print treffer_save
        results["treffer"] = treffer_save
        results["pagination"] = treffer

        # Berechnung/Einfügen der Nummer der gezeigten Treffer (um z. B. "Treffer 11 - 20" anzeigen zu können)
        results["endTreffer"] = page * pagesize
        if results["endTreffer"] > int(results["number_of_hits"]):
            results["endTreffer"] = int(results["number_of_hits"])

        if page == 1:
            results["startTreffer"] = 1
        else:
            results["startTreffer"] = (page - 1) * pagesize + 1



        # Auswertung der Personenlist um statistische Angaben zu gefundenen Personen machen zu können
        # vgl. http://docs.python.org/dev/library/collections.html#counter-objects

        cnt = Counter()
        for word in results["personList"]:
            cnt[word] += 1
        #print cnt

        mostCommonPersons = []
        for person in Counter(results["personList"]).most_common(8):
            mostCommonPersons.append(person[0])
        #print mostCommonPersons

        results["mostCommonPersons"] = mostCommonPersons

    #print query_parameters
    results['query_parameters'] = query_parameters
    show(query_parameters)

    #request_options = {'query': original_query, 'outputFormat': 'json', 'conceptSearch': 'true'}

    #response = requests.get(url, params=request_options)
    #print "\nAnfrage an: " + response.url
    #show(response.url)

    #reply = response.text

    #show(results)

    #results["conceptSearch"] = reply

    if more_like_this == True:
        return render_to_response('results-more-like-this.html', results)

    return render_to_response('results.html', results)
