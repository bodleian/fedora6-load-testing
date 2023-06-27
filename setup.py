from setuptools import setup, find_packages

setup(
    name='ORA DPS',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'rdflib==6.2.0',
        'requests==2.28.1',
        'python-dotenv==0.21.0'
    ],
    url='',
    author='Anusha Ranganathan',
    author_email='anusha@cottagelabs.com',
    description='ORA DPS',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
