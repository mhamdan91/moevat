import os
from setuptools import setup, find_packages
from pip._internal.network.session import PipSession
from pip._internal.req.req_file import parse_requirements

VERSION = "1.0.1"
PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
REQUIREMENTS = parse_requirements(os.path.join(PROJECT_DIR, 'requirements.txt'), session=PipSession())
DESCRIPTION = 'Python libary to quickly label data/images.'
LONG_DESCRIPTION = open('README.md').read()
setup(
    name="moevat",
    version=VERSION,
    author="mhamdan91 (Hamdan, Muhammad)",
    author_email="<mhamdan-91@hotmail.com>",
    url='https://github.com/mhamdan91/moevat',
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[str(ir.requirement) for ir in REQUIREMENTS],
    keywords=['python', 'gui', 'labeling', 'machine-learning', 'labeler', 'classification', 'images', 'annotation'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
          'console_scripts': ['moevat=moevat.cli:main'],
      }
)