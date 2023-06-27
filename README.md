# DPS

This is a project to manage code and tests related to the ORA-developed test of Fedora 6 as an API layer for the BDLSS Digital Preservation Service.

A description of the overall set of tasks and background can be found on the wiki: https://github.com/tomwrobel/dps/wiki/home

## Getting Started with running [Fedora 6.x](https://wiki.lyrasis.org/display/FEDORA6x)
Clone the repository with git clone https://github.com/tomwrobel/dps.git.

Ensure you have docker and docker-compose. See [notes on installing docker](https://github.com/tomwrobel/dps/wiki/Installing-Docker).

Open a console and try running `docker -h` and `docker-compose -h` to verify they are both accessible.

### Copy the environment variables

Copy the template environment variables file `.env.template` to `.env`. It has default values for working with Fedora running in docker.

```
cp .env.template .env
```
### Start the fedora 6 docker container

Start the docker containers for Fedora 6
```bash
$ docker-compose up -d
```
You should see the containers being built and the services start.

Note : This is only needed if you do not have a fedora 6 container provided. Skip if you have fedora 6 available as a service and add the connection details to the .env file.

## Testing Fedora6

There were two class of tests to run, to test Fedora6 meets the needs of the digital preservation service, as laid out in the ticket https://gitlab.bodleian.ox.ac.uk/ORA4/dps/-/issues/3

1. Load test Fedora6, to ensure its performance is adequate under load, when creating and updating the  [5 different types of objects](https://gitlab.bodleian.ox.ac.uk/ORA4/dps/-/issues/3#types-of-objects).
   * before we tested the performance of Fedora6 at full load, we spent some time testing Fedora 6 at minimum acceptable loads and different system settings, to find the optimum system settings for creating objects in OCFL using Fedora6, for the [5 different types of objects](https://gitlab.bodleian.ox.ac.uk/ORA4/dps/-/issues/3#types-of-objects)
2. Load test Fedora6, to ensure its performance is adequate for everyday use, when downloading, creating and updating OCFL objects.

The code in this repository is to enable running these tests.

### Different types of objects created by the test

The script `create_behavioural_objects.py` creates 5 types of objects in OCFL, as set out in https://gitlab.bodleian.ox.ac.uk/ORA4/dps/-/issues/3#types-of-objects

- Metadata only object

  - a single 2Kb metadata file
- Binary file object

  - 2 binary files 5Mb in size and a single metadata file 2Kb in size
- Large binary file objects

  - 5 binary files 1Gb in size and a single metadata file 2Kb in size
- Complex binary file objects

  - 100 binary files 500Mb in size and a single metadata file 2Kb in size
- Very large binary file objects

  - This is defined as 1 256Gb file and a single metadata file 2Kb in size.

  - In order for this to work, a file is first created, copied to a shared volume, which fedora has access to and then do a POST asking Fedora to copy an external file.

### Install the python packages
```
python3 -m venv dps_venv
source dps_venv/bin/activate
pip install --upgrade -r requirements.txt
```

**Note :** If you have a `.env` file, you can load the variables into your bash session using the command

```
export $(cat .env | xargs)
```

### Load testing Fedora 6

*Creating and updating behavioural objects in Fedora 6*

Before running the test, in the file [create_behavioural_objects.py](https://gitlab.bodleian.ox.ac.uk/ORA4/dps/-/blob/feature/behavioural_check/create_behavioural_objects.py), you can

1. Set the total number of objects you would like created
2. Choose the types of objects you would like created (all 5 or a subset of the 5)
3. Choose the fraction of each type of job within the total

​	The number of threads is passed as a command-line option to the script.

Once these are set, you can run the script to create the objects. 

` python create_behavioural_objects.py <thead_count>`


The script will create the list of jobs, randomise the list and loop over each job in the list in a threaded format, to simulate multiple simultaneous uploads.

The test produces logs and a csv file with the test results. The csv file has the following columns

* description, 
* HTTP result - message
* HTTP result - status
* Test status
* start time
* end time
* time difference
* object location

The script [overview.py](https://gitlab.bodleian.ox.ac.uk/ORA4/dps/-/blob/feature/behavioural_check/overview.py) is a convenience script used to run the behavioural objects test. 

* It runs `create_behavioural_objects.py` in 1, 3 and 5 threads
* It also runs `systemLoad.py`, to monitor the load on the system while the tests are being run.

* It collates all of the csv and log files and moves them into its corresponding results folder, one folder per thread

`python overview.py`

### Everyday test of Fedora6

*Creating, updating and downloading behavioural objects in Fedora 6*

```
python download_behavioural_objects.py
```

This script `download_behavioural_objects.py` is used to run the everyday tests. It complements the create_behavioural_objects.py by running downloads on the different types of jobs, with arguments similar to the create_behavioural_objects.

### Plotting
The output .csv file has the information on the test results and can be plotted graphically for example, using R. A script that does the plotting is included with the results directories, named "plot2.r". This script is customised to the current directory as there have been (minor) changes to add information to the log file over time. You run the script using :

 $ source("plot2.r", echo=TRUE)





