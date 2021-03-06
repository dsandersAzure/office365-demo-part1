import os
import logging
from flask import Flask, redirect, request, render_template, current_app, url_for
from helper.authentication import get_azure_signon_uri
from helper.configuration import Configuration
from datetime import datetime

# Configure logging to a basic level. We will allow logging to be configured
# later if there is a setting in the config_dict file.
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
app = Flask(__name__)
app.config.from_object(__name__)

# Load the configuration file from a file specified in an environment variable
# called config_dict
logging.debug('Instantiating a configuration object')
configuration = Configuration()
try:
    # Get the name of the configuration file from an environment variable. A
    # KeyError will be thrown if this has not been defined.
    configuration_file = os.environ['o365_demo_config']

    # Read the configuration file
    logging.debug('Loading configuration from the file: {0}'.format(configuration_file))
    configuration.configure_from_file(configuration_file, append=True)

    # Define a list of required items that must be defined and non-empty
    # in the file.
    required_items_list = ['client_id', 'resource', 'authority']

    # Validate the configuration file against the required items list
    logging.debug('Validating configuration contains non-empty items for: {0}'.format(required_items_list))
    configuration.validate(required_items=required_items_list)
except KeyError as ke:
    # Key Error means that the environment variable isn't defined.
    logging.error(
        'The environment variable "o365_demo_config" has not been set ' +
        'and must be set. The variable should point to a json file ' +
        'defining a dictionary of keys and values. A sample is' +
        'provided in the repository.'
    )
    exit(1)
except FileNotFoundError as fnf:
    # File Not Found error means the file couldn't be located.
    logging.error(
        'The file "{0}" specified in the config environment variable cannot be found.'
        .format(configuration_file)
    )
    exit(1)

# Configuration is complete
logging.debug('Configuration complete.')


@app.route('/', methods=['GET'])
def index_html():
    logging.debug('index_html has been loaded by a client.')
    return render_template(
        'index.html',
        auth_source=url_for('doauth'),
        publication_date='{0}'.format(datetime.now().strftime('%A %d %b %Y')),
        method=request.method
    )


@app.route('/doauth', methods=['GET'])
def doauth():
    return redirect(
        get_azure_signon_uri(
            client_id=configuration.config_dict.get('client_id'),
            resource=configuration.config_dict.get('resource'),
            redirect_uri=url_for('authenticated', _external=True),
            authority=configuration.config_dict.get('authority')
        )
    )


@app.route('/authenticated', methods=['POST'])
def authenticated():
    logging.debug('In authenticated')
    logging.debug('Method: POST')
    logging.debug('Request data: {0}'.format(request.data))
    logging.debug('Request args: {0}'.format(request.args))
    logging.debug('Request form: {0}'.format(request.form.get('id_token')))

    return render_template(
        'authindex.html',
        publication_date='{0}'.format(datetime.now().strftime('%A %d %b %Y')),
        method=request.method
    )


@app.route('/cert-key', methods=['GET'])
def cert_key():
    return render_template(
        'cert-key.html'
    )


port = configuration.config_dict.get('port', 8000)
server = configuration.config_dict.get('server', "127.0.0.1")

logging.debug('Starting application on {0}:{1}'.format(server, port))
app.run(host=server, port=port)
