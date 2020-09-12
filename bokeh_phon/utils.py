# Utility functions
import os
import urllib

# The most frequent external url when launching from mybinder.org.
# This variable is defined here so that it is available to the
# remote_jupyter_proxy_url_callback function. The caller does not
# provide for a url param.
default_jupyter_url = 'https://hub.gke.mybinder.org/'

def set_default_jupyter_url(url):
    '''
    This function provides a way to change the default_jupyter_url
    used in the remote_jupyter_proxy_url_callback function from a
    notebook at runtime.
    '''
    global default_jupyter_url
    default_jupyter_url = url

# For more on running Bokeh within Juypyter see
# https://docs.bokeh.org/en/latest/docs/user_guide/jupyter.html
# Where the function is defined as `remote_jupyter_proxy_url`.
def remote_jupyter_proxy_url_callback(port):
    '''
    Callable to configure Bokeh's show method when a proxy must be
    configured.

    If port is None we're asking about the URL
    for the origin header.
    '''
    try:
        base_url = os.environ['EXTERNAL_URL']
    except KeyError:
        base_url = default_jupyter_url
    host = urllib.parse.urlparse(base_url).netloc

    # If port is None we're asking for the URL origin
    # so return the public hostname.
    if port is None:
        return host

    service_url_path = os.environ['JUPYTERHUB_SERVICE_PREFIX']
    proxy_url_path = 'proxy/%d' % port

    if not base_url.endswith('/'):
        base_url += '/'
    user_url = urllib.parse.urljoin(base_url, service_url_path)
    full_url = urllib.parse.urljoin(user_url, proxy_url_path)
    return full_url
