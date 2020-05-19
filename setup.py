import sys
from shutil import copy

from setuptools import find_packages, setup
import versioneer

# We want to have the license at the top level of the GitHub repo, but setup
# can't include it from there, so copy it to the package directory first thing
copy('LICENSE', 'bokeh_phon/')

# State our runtime deps here, also used by meta.yaml (so KEEP the spaces)
REQUIRES = [
#    'bokeh >=2.0',
    'numpy',
]

setup(
    # basic package metadata
    name='bokeh_phon',
    version=versioneer.get_version(),
    description='Interactive plots for doing phonetics',

    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='BSD-3-Clause',
    author='Ronald L. Sprouse',
    author_email='ronald@berkeley.edu',
    url='http://github.com/rsprouse/bokeh_phon',
    classifiers=open('classifiers.txt').read().strip().split('\n'),

    # details needed by setup
    install_requires=REQUIRES,
    python_requires='>=3.6',
    packages=['bokeh_phon', 'bokeh_phon.models'],
    include_package_data=True
)
