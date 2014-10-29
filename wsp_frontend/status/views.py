# This Python file uses the following encoding: utf-8
from django.http import HttpResponse
from django.shortcuts import render, render_to_response
from django.template import Template
from django.template.loader import get_template
from django.utils import simplejson
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import Counter  # genutzt für statistische Auswertungen
import datetime #http://stackoverflow.com/questions/12906402/type-object-datetime-datetime-has-no-attribute-datetime
import itertools
import urllib
import requests
from show import show
import os

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
    # Requesting a list of all projects/collections
    # Query with '*', that way we get all projects/collections
    request_options = {'query': '*', 'outputFormat': 'json', 
                        'page': '1', 'pagesize': '10', 
                        'translate': 'false'}
    url = base_url + "/wspCmsWebApp/query/QueryDocuments?"

    response = requests.get(url, params=request_options)

    # XXX hier muss geprüft werden, ob die Anfage erfolgreich war (d. h.
    # Statuscode 200)
    reply = response.text

    try:
        data = simplejson.loads(reply)
    except:
        print "Fehler beim JSON-Parsing\n" + reply
        # XXX ToDO: Fehlerpage rendern!

    results = {}
    results["totalDocuments"] = data["sizeTotalDocuments"]

    # Get projects and some information from QueryDocuments
    projects = []
    for project in data["facets"]["collectionNames"]:
        if project["rdfUri"] == "http://wsp.normdata.rdf/DTM/Transkription":
            continue
        projectName = projectShortname = project["value"]
        projectCount = project["count"]
        projectRDFUri = project["rdfUri"]
        projectLastIndex = datetime.datetime.strptime(project["lastModified"], 
            "%Y-%m-%dT%H:%M:%S.%fZ")
        project = {"project": projectName, "count": projectCount,
                   "rdfURI": projectRDFUri, 
                   "projectShortname": projectShortname, 
                   "projectLastIndex": projectLastIndex}
        projects.append(project)
 
    # Open JSON-File with index status for all projects
    module_dir = os.path.dirname(__file__)  # get current directory
    file_path = os.path.join(module_dir, 'index_status.json')
    with open(file_path, 'r') as f:
        index_status = simplejson.load(f)

    # Query for project metadata (for items in projects)
    results["projektMetadaten"] = dict()

    rdfURL = base_url + "/wspCmsWebApp/query/QueryMdSystem"

    for project in projects:

        # If no RDF URI is present, no need to query the triple store
        if project["rdfURI"] == "none":
            continue

        request_options_rdf = {'detailedSearch': 'true', 'outputFormat':
                               'json', 'query': project["rdfURI"], 'isProjectId': 'true'}
        try:
            response = requests.get(rdfURL, params=request_options_rdf, timeout = 0.5)
            if not response.ok:
                    #print("Error in QueryMdSystem request: HTTP status " + str(response.status_code) + "\n" + response.url)
                    pass
        except requests.exceptions.Timeout, error:
            show(error)
            show(response.url)
            continue

        # verwendete Variablen mit "NA" initieren (falls Metadaten aus
        # dem Triplestore nicht vollständig sind)
        projectName = projectStatus = projectAbstract = webURI = \
            rdfURI = projectShortname = projectType = projectDefinition = \
            "NA"
        rdfURI = project['rdfURI']

        try:
            single_project_metadata = simplejson.loads(response.text)
            if not 'name' in single_project_metadata[rdfURI]:
                projectName = single_project['projectShortname']
            projectName = single_project_metadata[rdfURI]['name']
            projectAbstract = \
                single_project_metadata[rdfURI]['abstract']
            webURI = single_project_metadata[rdfURI]['homepage']
            projectShortname = single_project_metadata[rdfURI]['nick']

            if 'status' in single_project_metadata[rdfURI]:
                projectStatus = single_project_metadata[rdfURI]['status']

            if 'description' in single_project_metadata[rdfURI]:
                #XXX muss für Python 3 wahrscheinlich angepasst werden
                if single_project_metadata[rdfURI]['description'] == \
                    u"interdisziplinäre Arbeitsgruppe":
                    projectType = "IAG"
                else:
                    projectType = ""
                    for entry in single_project_metadata[rdfURI]['description']:
                        projectType += entry['description']

            if 'definition' in single_project_metadata[rdfURI]:
                projectDefinition = single_project_metadata[rdfURI]['definition']

        except Exception, e:
            show(e)
            show(rdfURI)
            show(response.url)

        # Loading status information obtained from .json file
        try:
            indexingProgress = indexingComment = ""
            indexingProgress = index_status[rdfURI]["status"]
            indexingComment = index_status[rdfURI]["comment"]
            projectLastIndex = project["projectLastIndex"]
        except Exception, error:
            show(error)
            show(rdfURI)
            indexingProgress = indexingComment = "NA"


        # XXX ToDo:
        # Die Metadaten zu den Projekten/Vorhaben in sinnvolle Datenstruktur überführen.
        # Wie soll im Template darauf zugegriffen werden? Eventuell diese Daten direkt in
        # entsprechende Facetten-Datenstruktur einfügen?

        projectShortname = project["project"]
        projektDaten = {"name": projectName, "status": projectStatus, 
                        "abstract": projectAbstract, "webURI": webURI, 
                        "rdfURI": rdfURI, 
                        "projectShortname": projectShortname, 
                        "projectType": projectType, 
                        "projectDefinition": projectDefinition, 
                        "indexingProgress": indexingProgress, 
                        "projectLastIndex": projectLastIndex, 
                        "indexingComment": indexingComment}

        results['projektMetadaten'][project['rdfURI']] = projektDaten

    return render_to_response('status.html', results)