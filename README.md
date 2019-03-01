

### This code is associated with the paper from Greenstein et al., "Noncoding RNA-nucleated heterochromatin spreading is intrinsically labile and requires accessory elements for epigenetic stability". eLife, 2018. http://dx.doi.org/10.7554/eLife.32948



![alt tag](https://raw.github.com/jimrybarski/fylm/dev/fylmcritic.png)
====
Extracts data from Fission Yeast Lifespan Microdissector images.

### Installation

fylm_critic has only been run on Ubuntu 14.04. Use other operating systems only if you really
know what you're doing.

First, in a terminal, install the required system packages:

    $ sudo apt-get update
    $ sudo apt-get install -y git gcc gfortran build-essential python2.7 python2.7-dev python-pip python-virtualenv tk tk-dev python-tk mencoder

Then clone this repo and make a virtual environment:

    $ git clone https://github.com/jimrybarski/fylm.git
    $ cd fylm
    $ virtualenv env
    $ . env/bin/activate

Now install the Python dependencies (this could take a while):

    $ pip install numpy Cython scipy
    $ pip install -r requirements.txt
    $ pip install -r external_requirements.txt
