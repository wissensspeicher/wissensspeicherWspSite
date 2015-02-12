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
import logging
from show import show
import os

logger = logging.getLogger(__name__)

# Dictionary für Umwandlung der Sprachkürzel in ausgeschriebene Sprachen
# (ISO 639-3 specifier)
language_dictionary = {
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
            if 'abstract' in single_project_metadata[rdfURI]:
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
                logger.debug("projectType: %s - %s", rdfURI, projectType)
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


def status_details(request):
    
    if 'rdfURI' in request.GET:
        rdfURI = request.GET['rdfURI']
    else:
        logger.warning('No rdfURI in query')
        #XXX ToDo Render error/help page

    # Query for project metadata
    rdfURL = base_url + "/wspCmsWebApp/query/QueryMdSystem"

    request_options_rdf = {'detailedSearch': 'true', 'outputFormat':
                           'json', 'query': rdfURI, 'isProjectId': 'true'}
    try:
        logger.info('Requesting Metadata for: %s', rdfURI)
        response = requests.get(rdfURL, params=request_options_rdf, 
            timeout = 2)
        if not response.ok or not response.text:
            logger.warning('Problem with QueryMdSystem request: %s', 
                response.url)
            logger.warning('HTTP Status Code: %s', 
                response.status_code)
            if response.ok:
                logger.warning('Reply: %s', response.text)
            #XXX ToDo Render error/help page
    except requests.exceptions.Timeout, error:
        logger.warning('Timeout: %s', response.url)
        #XXX ToDo Render error/help page

    logger.info('Requested Metadata from URL: %s', response.url)

    # Initialize variables with "NA" (in case metadata is not complete)
    name = status = abstract = webURI = shortname = "NA"
    descriptions = topics = languages = publishing_formats = life_span = \
        contributors = ["NA"]

    try:
        project_metadata = simplejson.loads(response.text)[rdfURI]
        if 'name' in project_metadata:
            name = project_metadata['name'].encode('utf-8')
        if 'abstract' in project_metadata:
            abstract = project_metadata['abstract'].encode('utf-8')
        if 'homepage' in project_metadata:
            webURI = project_metadata['homepage'].encode('utf-8')
        if 'nick' in project_metadata:
            shortname = project_metadata['nick'].encode('utf-8')
        if 'status' in project_metadata:
            status = project_metadata['status'].encode('utf-8')
        if 'description' in project_metadata: 
            descriptions = []
            # complicated json structure makes the for loop necessary
            for entry in project_metadata['description']:
                descriptions.append(entry['description'].encode('utf-8'))
        if 'topic' in project_metadata: 
            topics = []
            # complicated json structure makes the for loop necessary
            for entry in project_metadata['topic']:
                topics.append(entry['topic'].encode('utf-8'))
        if 'language' in project_metadata: 
            languages = []
            # complicated json structure makes the for loop necessary
            for entry in project_metadata['language']:
                languages.append(language_dictionary[entry['language'].encode('utf-8')])
        if 'format' in project_metadata:
            if not isinstance(project_metadata['format'], basestring):
                publishing_formats = [i.encode('utf-8') for i in project_metadata['format']]
            else:
                publishing_formats = []
                publishing_formats.append(project_metadata['format'])
        if 'valid' in project_metadata and ('end' in project_metadata['valid']):
            life_span = []
            
            # Get the list indices for start and end of project:
            # The string ist splitted along '; ' and the resulting list 
            # searched for 'start=' and 'end='. Because this search returns a 
            # list [of indices], the first (and supposedly only) entry in each 
            # list is then selected.
            # Append start and end dates to life_span using the indices 
            # found. Parts of the string is deleted, in order to get
            # only the year.
            if 'start' in project_metadata['valid']:
                start_index = [i for i, s in enumerate(project_metadata['valid'].split('; ')) if 'start=' in s][0]
                life_span.append(project_metadata['valid'].split('; ')[start_index].replace('start=', '').encode('utf-8'))
            if 'end' in project_metadata['valid']:
                end_index = [i for i, s in enumerate(project_metadata['valid'].split('; ')) if 'end=' in s][0]
                life_span.append(project_metadata['valid'].split('; ')[end_index].replace('end=', '').encode('utf-8'))

        if 'contributor' in project_metadata:
            contributors = []
            for single_contributor in project_metadata['contributor']:
                contributor = {}
                if 'title' in single_contributor:
                    contributor['title'] = single_contributor['title'].encode('utf-8')
                else:
                    contributor['title'] = "None"
                if 'familyName' in single_contributor:
                    contributor['familyName'] = \
                        single_contributor['familyName'].encode('utf-8')
                else:
                    contributor['familyName'] = "NA"
                if 'givenName' in single_contributor:
                    contributor['givenName'] = \
                        single_contributor['givenName'].encode('utf-8')
                else:
                    contributor['givenName'] = "NA"
                if 'functionOrRole' in single_contributor:
                    contributor['role'] = \
                        single_contributor['functionOrRole'].encode('utf-8')
                else:
                    contributor['role'] = "NA"
                if 'subject' in single_contributor:
                    contributor['rdfURI'] = \
                        single_contributor['subject'].encode('utf-8')
                if 'gndIdentifier' in single_contributor:
                    contributor['gnd'] = \
                        single_contributor['gndIdentifier'].encode('utf-8')
                else:
                    contributor['gnd'] = "NA"
                if 'mbox' in single_contributor:
                    contributor['email'] = single_contributor['mbox']

                contributors.append(contributor)

        project_data = {"name": name, "status": status, 
                            "abstract": abstract, "webURI": webURI, 
                            "rdfURI": rdfURI, 
                            "shortname": shortname, 
                            'descriptions': descriptions,
                            'topics': topics,
                            'languages': languages,
                            'publishing_formats': publishing_formats,
                            'life_span': life_span,
                            'contributors': contributors,
                            #"projectType": projectType, 
                            #"projectDefinition": projectDefinition, 
                            #"indexingProgress": indexingProgress, 
                            #"projectLastIndex": projectLastIndex, 
                            #"indexingComment": indexingComment,
                        }
        logger.debug('%s', project_data)

    except Exception, e:
        logger.exception('Error in metadata processing: %s, %s', 
                    rdfURI, response.url)
        raise
        #XXX ToDo: render error page



    return render_to_response('status_details.html', project_data)

#def getMetadataValue(metadata, key):
#    
#    try:
#        data = metadata[key]
#        if isinstance(data, list):
#            pass
#        if isinstance(data, dict):
#            pass
#
#
#    except KeyError, error:
#        logger.exception('Error in metadata processing')
#        return 'NA'


