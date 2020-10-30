import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext
from setuptools import setup, find_packages

setup(
    name="fbfscan",
    version="0.2.0",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    scripts=[],
    install_requires=['wipistepper','gphoto2','curses-menu','curtsies'],
    package_data={'': ['*.txt', '*.rst','config.ini'],
    },

    # metadata to display on PyPI
    author="Chris Ringeval",
    author_email="eatdirt@mageia.org",
    description="Fbfscan film scanner",
    license="GPLv3",
    keywords="scanner film stepper",
    url="https://github.com/eatdust/fbfscan/",   
)
