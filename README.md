# How to Install (local/development)

 #. Clone git Repository 

    <samp>ssh://user@telotadev.bbaw.de/opt/git/wspSite.git/</samp>

 #. Create Virtual Environment (Python)

    Create a virtual environment for running this Django set up. Depending on
    the machine this can be done with <samp>pyvenv</samp> or 
    <samp>mkvirtualenv</samp>. Activate the newly created virtual environment.

 #. Install requirements

    Run <samp>pip install -r requirements.txt</samp>

 #. Create local settings file

    Create a new local settings file based on
    <samp>wsp_frontend/settings/local.py</samp> where the paths are adopted to
    your local set up.

 #. Running the local server

    Run <samp>manage.py runserver
    --settings=PATH_TO_LOCAL_SETTINGS_AS_MODULE</samp>

    The local test server should then be available at
    [`http://127.0.0.1:8000`](http://127.0.0.1:8000). If you want to run the
    test server at a different port or want to change other options, see the
    [Django documentation](https://docs.djangoproject.com/en/1.9/ref/django-admin/#runserver)
    for more details.
