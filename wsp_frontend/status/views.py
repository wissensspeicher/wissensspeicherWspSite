# This Python file uses the following encoding: utf-8
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import Template
from django.template.loader import get_template
from django.utils import simplejson
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import Counter  # genutzt für statistische Auswertungen
from datetime import datetime
import itertools
import urllib
import requests
from show import show

import pprint
pp = pprint.PrettyPrinter(indent=4)


# Dictionary für Umwandlung der Sprachkürzel in ausgeschriebene Sprachen
# (ISO 639-3 specifier)
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

def status(request):
    ressourceTypes = {"application/pdf": "pdf",
                  "application/xml": "xml",
                  }

    post_data = ''
    translate = ''
    translateQuery = False
    morphologicalSearch = False
    page = 1
    pagesize = 10

    query_parameters = ''


    original_query = querydata = '*'

    post_data = [('query', querydata)]
    post_data = urllib.urlencode(post_data)

    # Falls die Suche nach "*" ist und Facetten ausgewählt sind, muss eine "leere Suche"+Facetten
    # durchgeführt werden, weil Josefs Tomcat sonst muckt.
    if any(word in request.GET for word in ['author', 'project', 'language']) and querydata == "*":
        querydata = ""

    page_data = [("page", page)]
    page_data = urllib.urlencode(page_data)

    #show(querydata)
    request_options = {'query': querydata, 'outputFormat': 'json', 'page':
                       page, 'pagesize': pagesize, 'translate': str(translateQuery).lower()}

    if morphologicalSearch == True:
        request_options['fieldExpansion'] = "allMorph"

    url = base_url + "/wspCmsWebApp/query/QueryDocuments?"

    # XXX hier muss geprüft werden, ob die Anfage erfolgreich war (d. h.
    # Statuscode 200)

    response = requests.get(url, params=request_options)
    # print "\nAnfrage an: " + response.url
    show(response.url)

    reply = response.text

    try:
        data = simplejson.loads(reply)
    except:
        print "Fehler beim JSON-Parsing\n" + reply
        # XXX ToDO: Fehlerpage rendern!

    results = {}

    # XXX: Warum die folgende Zeile? wofür wird translated auf TRUE gesetzt?
    results["translated"] = True

    results["totalDocuments"] = data["sizeTotalDocuments"]
    results["personList"] = []
    #results["search_term"] = data["searchTerm"].replace("tokenOrig:", "", 1)
    results["search_term"] = original_query
    results["search_term"] = results[
        "search_term"].replace("tokenMorph:", "", 1)
    results["search_term"] = results["search_term"].strip("()")

    results["number_of_hits"] = int(data["numberOfHits"])
    results["morphologicalSearch"] = morphologicalSearch
    results["translateSearch"] = translateQuery
    results["treffer"] = ""

    projekte = set()

    if results["number_of_hits"] > 0:
        treffer = []
        for j, single_treffer in enumerate(data["hits"]):
            # print(single_treffer)

            # Herumarbeiten um Fehler in Volltextindex (z. B. Suchanfrage
            # "Haus")

            i = {}
            i["relevantPersons"] = []
            i["places"] = []
            i["docId"] = "none"
            i["projectRdfURI"] = ""

            # Nummerierung der Treffer, da die Angaben nicht im JSON enthalten sind
            # 1 wird addiert, da die Zählung von j in der Schleife bei 0
            # beginnt
            i["hitNumber"] = (page - 1) * pagesize + j + 1

            # docID parsen
            try:
                i["docId"] = single_treffer["docId"]
            except:
                # print "KeyError docId"
                pass

            # webURI (Rücksprungadresse) parsen
            try:
                i["url"] = single_treffer["webUri"].encode("utf-8")
            except:
                # print "KeyError webUri @ " + i["docId"]
                i["url"] = single_treffer["uri"].encode("utf-8")
                pass

            # Fragmente mit Trefferexzerpten parsen
            i["fragments"] = []
            for fragment in single_treffer["fragments"]:
                fragment = fragment.encode("utf-8")

                # XXX müsste auch wieder zu UTF-8 werden
                i["fragments"].append(fragment)

            # Autorinformation parsen
            i["author"] = []
            try:
                for single_author in single_treffer["author"]:
                    i["author"].append(single_author["name"])
            except KeyError, e:
                # print "KeyError author " + i["docId"]
                pass

            # Titel parsen
            try:
                i["title"] = single_treffer[
                    "title"].replace(" TITEL DES BRIEFS", "", 1)
            except KeyError, e:
                # Wenn kein Titel vorhanden ist, wird die URL zum Dokument als
                # Titel genommen
                i["title"] = i["url"]
                # print "KeyError title " + i["docId"]
                pass

            try:
                i["collectionName"] = single_treffer["project"]["name"]
                i["collectionURL"] = single_treffer["project"]["url"]
                i["collectionID"] = single_treffer["project"]["id"]
                projekte.add(i["collectionID"])
            except KeyError, e:
                # print "KeyError collectionName " + i["docId"]
                pass

            try:
                i["type"] = ressourceTypes[single_treffer["type"]]
            except KeyError, e:
                # print error...
                i["type"] = "undefined"
                pass

            # RDF URI parsen
            try:
                i["projectRdfURI"] = single_treffer["rdfUri"]
            except KeyError, e:
                pass

            # Personeninformationen parsen
            try:
                for single_person in single_treffer["persons"]:
                    person = {
                        "name": "Testname", "url": "http://example.org", "role": "unknown"}
                    person = {"name": single_person["name"], "url": single_person[
                        "referenceAbout"], "role": single_person["role"]}
                    i["relevantPersons"].append(person)
                    if not person["role"] == "editor":
                        results["personList"].append(person["name"])
                    # print person
            except KeyError, e:
                # print "KeyError persNames " + i["docId"]
                pass

            # Notwending, falls eine Person im JSON nur "null" ist, und keine
            # zugehörigen Werte hat:
            except TypeError, e:
                pass

            try:
                for single_place in single_treffer["places"]:
                    place = {
                        "place": "Beispielshausen", "url": "http://example.org"}
                    place = {"place": single_place[
                        "name"], "url": single_place["link"]}
                    i["places"].append(place)
                    # print place
            except KeyError, e:
                # print "KeyError places " + i["docId"]
                # print "KeyError places"
                pass
            #
            # Duplikate aus Personen- und Ortslisten entfernen
            #

            newlist = []
            for person_entry in sorted(i["relevantPersons"], key=lambda elt: elt["name"]):
                if newlist == [] or person_entry["name"] != newlist[-1]["name"]:
                    newlist.append(person_entry)
            i["relevantPersons"] = newlist

            newlist = []
            for place_entry in sorted(i["places"], key=lambda elt: elt["place"]):
                if newlist == [] or place_entry["place"] != newlist[-1]["place"]:
                    newlist.append(place_entry)
            i["places"] = newlist
            # print "E: " + i["docId"] + "   " + i["type"]
            treffer.append(i)
            # pp.pprint(i)
            # show(i)
        results["treffer"] = treffer

        # facets parsen
        results["authorFacet"] = []
        results["projectFacet"] = []
        results["languageFacet"] = []
        for single_author in data["facets"]["author"]:
            authorName = single_author["value"]
            authorCount = single_author["count"]
            author = {"name": authorName, "count": authorCount}
            results["authorFacet"].append(author)
        for single_project in data["facets"]["collectionNames"]:
            projectName = projectShortname = single_project["value"]
            projectCount = single_project["count"]
            projectRDFUri = single_project["rdfUri"]
            projectLastIndex = datetime.strptime(single_project["lastModified"], "%Y-%m-%dT%H:%M:%S.%fZ")
            project = {"project": projectName, "count": projectCount,
                       "rdfURI": projectRDFUri, "projectShortname": projectShortname, "projectLastIndex": projectLastIndex}
            results["projectFacet"].append(project)
        for single_language in data["facets"]["language"]:
            languageID = single_language["value"]
            languageCount = single_language["count"]
            try:
                languageText = languages[languageID]
            except KeyError:
                languageText = languageID
            language = {"languageID": languageID, "count":
                        languageCount, "language": languageText}
            results["languageFacet"].append(language)

        treffer_list = results["treffer"]
        treffer_save = []
        treffer_save = results["treffer"][:]

        # Open JSON-File with index status for all projects

        with open('status/index_status.json', 'r') as f:
            index_status = simplejson.load(f)

        #show(index_status)

        # Anfrage der Projektmetadaten (für die Projekte in projekte)
        results["projektMetadaten"] = dict()
        rdfURL = "http://wspdev.bbaw.de" + "/wspCmsWebApp/query/QueryMdSystem"
        #rdfURL = "http://192.168.1.199" + "/wspCmsWebApp/query/QueryMdSystem"
        for projekt in results["projectFacet"]:
            # Wenn es keine RDF URI gibt, dann muss der Triplestore auch nicht angefragt werden
            # XXX Wie soll mit Projekten umgegangen werden, die keine RDF-URI
            # haben (edoc, wfe, bkvb, ...)
            if projekt["rdfURI"] == "none":
                continue

            #print("Requesting Metadata for " + projekt["rdfURI"])
            request_options_rdf = {'detailedSearch': 'true', 'outputFormat':
                                   'json', 'query': projekt["rdfURI"], 'isProjectId': 'true'}

            # Fehler auf Serverseite umgehen
            # Beispiel:
            # http://wspdev.bbaw.de/wspCmsWebApp/query/QueryMdSystem?query=http%3A%2F%2Fwsp.normdata.rdf%2FAvHForschungsstelle&detailedSearch=true&isProjectId=true&outputFormat=json
            # liefert eine Exception
            # show(rdfURL)
            try:
                response = requests.get(rdfURL, params=request_options_rdf, timeout = 0.5)
                # show(response.url)
            except UnicodeEncodeError, error:
                continue
            except requests.exceptions.Timeout, error:
                show(error)
                continue

            # print(response.url)

            try:

                projektMetadaten = simplejson.loads(response.text)

                # verwendete Variablen mit "NA" initieren (falls Metadaten aus
                # dem Triplestore nicht vollständig sind)
                projectName = projectStatus = projectAbstract = webURI = rdfURI = projectShortname = "NA"

                if projektMetadaten["hitGraphes"] != []:
                    for o in projektMetadaten["hitGraphes"][0][projekt["rdfURI"]]:

                        if "name" in o:
                            # print(o["name"])
                            projectName = o["name"]
                            # show(projectName)
                        else:
                            pass
                        if "status" in o:
                            projectStatus = o["status"]
                        if "abstract" in o:
                            projectAbstract = o["abstract"]
                        if "homepage" in o:
                            webURI = "http://" + o["homepage"]
                        if "description" in o:
                            #XXX muss für Python 3 wahrscheinlich angepasst werden
                            if o["description"] == u"interdisziplinäre Arbeitsgruppe":
                                projectType = "IAG"
                            else:
                                projectType = o["description"]
                        if "definition" in o:
                            projectDefinition = o["definition"]
                        rdfURI = projekt["rdfURI"]
                        projectLastIndex = projekt["projectLastIndex"]
                    try:
                        indexingProgress = ""
                        indexingProgress = index_status[rdfURI]["status"]
                        indexingComment = ""
                        indexingComment = index_status[rdfURI]["comment"]
                        #show(indexingComment)
                    except KeyError, e:
                        pass
                    # XXX ToDo:
                    # Die Metadaten zu den Projekten/Vorhaben in sinnvolle Datenstruktur überführen.
                    # Wie soll im Template darauf zugegriffen werden? Eventuell diese Daten direkt in
                    # entsprechende Facetten-Datenstruktur einfügen?
                    # if projectAbstract == "NA":
                    #    show(response.url)
                    projectShortname = projekt["project"]
                    projektDaten = {"name": projectName, "status": projectStatus, "abstract":
                                    projectAbstract, "webURI": webURI, "rdfURI": rdfURI, "projectShortname": projectShortname, 
                                    "projectType": projectType, "projectDefinition": projectDefinition, "indexingProgress": indexingProgress, 
                                    "projectLastIndex": projectLastIndex, "indexingComment": indexingComment}
                    #show(projektDaten)

                results["projektMetadaten"][projekt["rdfURI"]] = projektDaten
                #show(projektDaten)
            except Exception, e:
                # print(e)
                # print(response.url)
                pass
                # print "Fehler beim JSON-Parsing\n" + reply
            #show(len(results["projektMetadaten"]))

        # pp.pprint(results["projektMetadaten"])
        # print(results["projektMetadaten"])
        # XXX ToDO: Fehlerpage rendern!
        # print "\nAnfrage an: " + response.url
        # show(response.url)
        #reply = response.text

    return render_to_response('status.html', results)