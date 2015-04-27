# This Python file uses the following encoding: utf-8
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import Template
from django.utils import simplejson
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import Counter  # used for statistic calculations

import logging
import requests
import urllib
from show import show

# set up logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# handler = logging.FileHandler('site.log')
# handler.setLevel(logging.DEBUG)

# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - '
#    '%(message)s')
# handler.setFormatter(formatter)

# logger.addHandler(handler)

# Set logging information for the requests module to WARNING only, otherwise
# we get lots of trivial connection information
# logging.getLogger("requests").setLevel(logging.WARNING)

# Dictionary for conversion of language codes to full languagen names.
# (ISO 639-3 specifier)
# XXX possibly use <https://github.com/LuminosoInsight/langcodes>
languages = {
    # "ger": "german",
    # "eng": "english",
    # "fra": "france",
    # "lat": "latin",
    # "grc": "greek",
    # "ara": "arabic",
    # "ita": "italian",
    # "nld": "dutch",
    # "zho": "chinese",
    "ger": u"Deutsch",
    "eng": u"Englisch",
    "fra": u"Französisch",
    "lat": u"Latein",
    "grc": u"Griechisch",
    "ara": u"Arabisch",
    "ita": u"Italienisch",
    "nld": u"Niederländisch",
    "zho": u"Chinesisch",
}

# Dictionary for MIME-Types
ressourceTypes = {"application/pdf": "pdf",
                  "application/xml": "xml",
                  }

# XXX Dokumentieren
base_url = "http://wspdev.bbaw.de"


# View for start page. The simple search request for 'a' is only used in order
# to receive and subsequently show the total number of indexed
# documents/resources.
def hello_world(request):

    url = base_url + "/wspCmsWebApp/query/QueryDocuments"
    request_options = {'query': 'a', 'outputFormat': 'json'}
    response = requests.get(url, params=request_options)
    reply = response.text

    try:
        data = simplejson.loads(reply)
    except:
        logger.exception("Fehler beim JSON-Parsing")
        logger.exception(reply)
        # XXX ToDO: Fehlerpage rendern! LOGGING!

    totalDocuments = data["sizeTotalDocuments"]
    results = {'totalDocuments': totalDocuments}

    return render_to_response('search_form.html', results)


# View for full-text-query. This is where the magic happens.
def search(request):

    # Initialization of some needed variables
    translate = ''
    translateQuery = False
    page = 1
    pagesize = 10
    query_parameters = ''

    # Check for "morphological search" option
    try:
        morphologicalSearch = False
        if request.GET['morphologicalSearch'] == 'on':
            morphologicalSearch = True
            query_parameters = query_parameters + '&morphologicalSearch=on'
    except KeyError, e:
        pass

    # Important: every part of request.GET needs to be converted to a string,
    # conversion of utf-8 --> python2-string
    if 'query' in request.GET:
        querydata = request.GET['query']
        querydata = querydata.encode("utf-8")
        original_query = querydata.strip()

        # If no search query was entered, the empty search form is shown.
        if original_query == "":
            print "Empty Query"
            # LOGGING!
            return render(request, 'search_form.html')

    logger.info('query: %s', querydata)

    # Check for "AutorInnen"-facette
    if 'author' in request.GET:
        querydata += ' author:("' + \
            '"" '.join(request.GET.getlist('author')).encode('utf-8') + '")'

        # To enable navigation and results browsing selected facettes are
        # saved in query_parameters. A matching URL is generated in the
        # template.
        query_parameters += '&author=' + \
            '&author='.join(request.GET.getlist('author'))

    # Check for "Projekte/Vorhaben"-facette
    if 'project' in request.GET:
        querydata += ' collectionNames:(' + \
            ' '.join(request.GET.getlist('project')).encode('utf-8') + ')'

        # To enable navigation and results browsing selected facettes are
        # saved in query_parameters. A matching URL is generated in the
        # template.
        query_parameters += '&project=' + \
            '&project='.join(request.GET.getlist('project'))

    # Check for "Sprachen"-facette
    if 'language' in request.GET:
        querydata += ' language:(' + \
            ' '.join(request.GET.getlist('language')).encode('utf-8') + ')'

        # To enable navigation and results browsing selected facettes are
        # saved in query_parameters. A matching URL is generated in the
        # template.
        query_parameters += '&language=' + \
            '&language='.join(request.GET.getlist('language'))

    # Check if moreLikeThis is selected as a search option
    try:
        if request.GET["morelikethis"] == "true":
            more_like_this = True
    except KeyError, e:
        more_like_this = False

    # Check if translation option is selected
    if "translateCheck" in request.GET:
        if request.GET['translateCheck'] == "on":
            translateQuery = True
            translate = [("translate", "true")]
            translate = "&" + urllib.urlencode(translate)
            query_parameters = query_parameters + '&translateCheck=on'

    # Check if a certain page from the set of search results is requested.
    if "page" in request.GET:
        # Cast to integer, in order to make the calculation of the current page
        # work (see further below).
        page = int(request.GET['page'])

    # base_url = "http://wspdev.bbaw.de"
    # base_url = "http://192.168.1.199:8080" # Marco
    # base_url = "http://192.168.1.203:8080" # Josef

    request_options = {'query': querydata, 'outputFormat': 'json',
                       'page': page, 'pagesize': pagesize,
                       'translate': str(translateQuery).lower(),
                       'queryLanguage': 'gl'}

    if morphologicalSearch is True:
        request_options['fieldExpansion'] = "allMorph"

    url = base_url + "/wspCmsWebApp/query/QueryDocuments?"

    # XXX moreLikeThis ist noch ein ziemlicher Hack! Die URL/IP muss hier auch
    # noch angepasst werden (Josefs Installation bzw. wspdev kann das noch
    # nicht!
    if more_like_this is True:
        url = base_url + "/wspCmsWebApp/query/MoreLikeThis?docId=" + \
            querydata + "&outputFormat=json"
        request_options = {}

    # Send search request to full text index (queryDocuments)
    # XXX TODO: Catch errors via response.ok or response.raise_for_status()
    response = requests.get(url, params=request_options)
    reply = response.text
    logger.info('Requested URL: %s', response.url)
    results = {}
    results["number_of_hits"] = 0
    try:
        data = simplejson.loads(reply)
        results["totalDocuments"] = data["sizeTotalDocuments"]
        results["number_of_hits"] = int(data["numberOfHits"])
    except:
        print "Fehler beim JSON-Parsing\n" + reply
        # XXX ToDO: Fehlerpage rendern! LOGGING

    results["personList"] = []
    results["search_term"] = original_query
    results["search_term"] = \
        results["search_term"].replace("tokenMorph:", "", 1)
    results["search_term"] = results["search_term"].strip("()")
    results["morphologicalSearch"] = morphologicalSearch
    results["translateSearch"] = translateQuery
    results["treffer"] = ""

    projekte = set()

    if results["number_of_hits"] > 0:
        treffer = []
        for j, single_treffer in enumerate(data["hits"]):
            i = {}
            i["relevantPersons"] = []
            i["places"] = []
            i["entities"] = []
            i["docId"] = "none"
            i["projectRdfURI"] = ""

            # Numbering of search results (JSON provided by queryDocuments
            # contains no numbering)
            # 1 is added, because 'j' is initially zero
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
                        "name": "Testname", "url": "http://example.org",
                        "role": "unknown"}
                    person = {"name": single_person["name"],
                              "url": single_person["referenceAbout"],
                              "role": single_person["role"]}
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
                        "place": "Beispielshausen",
                        "url": "http://example.org"}
                    place = {"place": single_place["name"],
                             "url": single_place["link"]}
                    i["places"].append(place)
                    # print place
            except KeyError, e:
                # print "KeyError places " + i["docId"]
                # print "KeyError places"
                pass

            # Parse list of DBpedia spotlight entities
            try:
                if 'entities' in single_treffer:
                    for entity in single_treffer["entities"]:
                        entityLabel = entity["label"]
                        entityType = entity["type"]
                        entityDBpediaURI = entity["uri"]
                        if "uriGnd" in entity:
                            entityGND = entity["uriGnd"]
                        else:
                            entityGND = ""

                        if entityType == "person":
                            person = {"name": entityLabel,
                                      "url": entityDBpediaURI,
                                      "role": "mentioned",
                                      "GND": entityGND}
                            i["relevantPersons"].append(person)
                        elif entityType == "place":
                            place = {"place": entityLabel,
                                     "url": entityDBpediaURI,
                                     "GND": entityGND}
                            i["places"].append(place)
                        else:
                            i["entities"].append({"label": entityLabel,
                                                  "type": entityType,
                                                  "dbpediaURI":
                                                  entityDBpediaURI,
                                                  "GND": entityGND})
                        # logger.debug({"label": entityLabel,
                        #               "type": entityType,
                        #               "dbpediaURI": entityDBpediaURI,
                        #               "GND": entityGND})
            except KeyError, e:
                logger.exception('Error in entity parsing (DBpedia spotlight \
                                 entities')
                logger.exception(single_treffer)

            #
            # Duplikate aus Personen- und Ortslisten entfernen
            #

            newlist = []
            for person_entry in sorted(i["relevantPersons"],
                                       key=lambda element: element["name"]):
                if newlist == [] or person_entry["name"] != \
                        newlist[-1]["name"]:
                    newlist.append(person_entry)
            i["relevantPersons"] = newlist

            newlist = []
            for place_entry in sorted(i["places"],
                                      key=lambda element: element["place"]):
                if newlist == [] or place_entry["place"] != \
                        newlist[-1]["place"]:
                    newlist.append(place_entry)
            i["places"] = newlist
            # print "E: " + i["docId"] + "   " + i["type"]
            treffer.append(i)
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

        # Sort author list alphabetically
        results["authorFacet"].sort(key=lambda element: element["name"])

        for single_project in data["facets"]["collectionNames"]:
            projectName = projectShortname = single_project["value"]
            projectCount = single_project["count"]
            projectRDFUri = single_project["rdfUri"]
            project = {"project": projectName, "count": projectCount,
                       "rdfURI": projectRDFUri,
                       "projectShortname": projectShortname}
            results["projectFacet"].append(project)

        # The project list is sorted later, because the full project names are
        # only available after querying for metadata.

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

        # Sort language list alphabetically
        results["languageFacet"].sort(key=lambda element: element["language"])

        treffer_list = results["treffer"]
        treffer_save = []
        treffer_save = results["treffer"][:]

        # Anfrage der Projektmetadaten (für die Projekte in projekte)
        results["projektMetadaten"] = dict()
        rdfURL = "http://wspdev.bbaw.de" + "/wspCmsWebApp/query/QueryMdSystem"
        # rdfURL = "http://192.168.1.199" + "/wspCmsWebApp/query/QueryMdSystem"

        for projekt in results["projectFacet"]:
            # Wenn es keine RDF URI gibt, dann muss der Triplestore auch nicht
            # angefragt werden
            # XXX Wie soll mit Projekten umgegangen werden, die keine RDF-URI
            # haben (edoc, wfe, bkvb, ...)
            if projekt["rdfURI"] == "none":
                continue

            logger.debug('Requesting Metadata for: %s', projekt["rdfURI"])
            request_options_rdf = {'detailedSearch': 'true', 'outputFormat':
                                   'json', 'query': projekt["rdfURI"],
                                   'isProjectId': 'true'}

            # Request for project metadata (QueryMdSystem)
            # XXX ToDo: Catch erros via response.ok or
            # response.raise_for_status()
            try:
                response = requests.get(rdfURL, params=request_options_rdf,
                                        timeout=1.6)
                if not response.ok or not response.text:
                    logger.warning('Problem with QueryMdSystem request: %s',
                                   response.url)
                    logger.warning('HTTP Status Code: %s',
                                   response.status_code)
                    if response.ok:
                        logger.warning('Reply: %s', response.text)
            except UnicodeEncodeError, error:
                continue
            except requests.exceptions.Timeout:
                logger.warning('Timeout: %s', projekt["rdfURI"])

            try:
                projektMetadaten = simplejson.loads(response.text)

                # verwendete Variablen mit "NA" initieren (falls Metadaten aus
                # dem Triplestore nicht vollständig sind)
                projectName = projectStatus = projectAbstract = webURI = \
                    rdfURI = projectShortname = "NA"

                rdfURI = projekt['rdfURI']
                projectName = projektMetadaten[rdfURI]['name']
                webURI = projektMetadaten[rdfURI]['homepage']
                projectShortname = projektMetadaten[rdfURI]['nick']
                if 'abstract' in projektMetadaten[rdfURI]:
                    projectAbstract = projektMetadaten[rdfURI]['abstract']
                else:
                    logger.warning('No abstract found for: %s',
                                   projektMetadaten[rdfURI])

                if 'status' in projektMetadaten[rdfURI]:
                    projectStatus = projektMetadaten[rdfURI]['status']

                # XXX ToDo:
                # Die Metadaten zu den Projekten/Vorhaben in sinnvolle
                # Datenstruktur überführen.
                # Wie soll im Template darauf zugegriffen werden? Eventuell
                # diese Daten direkt in entsprechende Facetten-Datenstruktur
                # einfügen?
                projektDaten = {"name": projectName,
                                "status": projectStatus,
                                "abstract": projectAbstract,
                                "webURI": webURI, "rdfURI": rdfURI,
                                "projectShortname": projectShortname}

                results["projektMetadaten"][projekt["rdfURI"]] = projektDaten

            except Exception, e:
                logger.error('Error in metadata processing: %s, %s',
                             e.__class__.__name__, e)
                logger.error('rdfURI: %s', projekt['rdfURI'])
                logger.error('Requested URL: %s', response.url)

        # Assign full project names from metadata to project facet
        # (needed for correct sorting of facet)
        for i, project in enumerate(results["projectFacet"]):
            try:
                results["projectFacet"][i]["project"] = (
                    results["projektMetadaten"]
                    [results["projectFacet"][i]["rdfURI"]]["name"])
            except KeyError, e:
                logger.exception('Error while assigning full project ',
                                 'names from metadata.')
                logger.exception(e)

        # Sort project facet
        # XXX this doesn't sort german umlauts correctly (they get placed at
        # the end of the list)
        results["projectFacet"].sort(
            key=lambda element: element["project"])

        # Paginierung
        # XXX Dokumentieren, wie genau die Seitennummerierung hier
        # XXX funktioniert!
        # XXX Die Addition von number_of_hits % 10 ist notwendig, um auf der
        # letzten Seite (z. B. 24 von 24) nicht eine Seite zu wenig anzuzeigen.
        # XXX Muss genauer nachvollzogen werden.
        for x in range(10, (results["number_of_hits"] +
                            (int(results['number_of_hits']) % 10))):
            treffer_list.append("TEST")

        paginator = Paginator(treffer_list, 10)

        # print "paginator.count: " + str(paginator.count) # +
        # (int(results['number_of_hits']) % 10))

        # page = request.GET.get("page")
        # print page

        try:
            treffer = paginator.page(page)
        except PageNotAnInteger:
            treffer = paginator.page(1)
        except EmptyPage:
            treffer = paginator.page(paginator.num_pages)

        # XXX next: überzählige Einträge aus treffer_list entfernen,

        # print treffer
        # print treffer_save
        results["treffer"] = treffer_save
        results["pagination"] = treffer

        # Berechnung/Einfügen der Nummer der gezeigten Treffer (um z. B.
        # "Treffer 11 - 20" anzeigen zu können)
        results["endTreffer"] = page * pagesize
        if results["endTreffer"] > int(results["number_of_hits"]):
            results["endTreffer"] = int(results["number_of_hits"])

        if page == 1:
            results["startTreffer"] = 1
        else:
            results["startTreffer"] = (page - 1) * pagesize + 1

        # Auswertung der Personenlist um statistische Angaben zu gefundenen
        # Personen machen zu können, vgl.
        # http://docs.python.org/dev/library/collections.html#counter-objects
        cnt = Counter()
        for word in results["personList"]:
            cnt[word] += 1

        mostCommonPersons = []
        for person in Counter(results["personList"]).most_common(8):
            mostCommonPersons.append(person[0])
        results["mostCommonPersons"] = mostCommonPersons

    results['query_parameters'] = query_parameters
    logger.info('query_parameters: %s', query_parameters)

    # Currently not used.
    # if more_like_this == True:
    #    return render_to_response('results-more-like-this.html', results)

    return render_to_response('results.html', results)
