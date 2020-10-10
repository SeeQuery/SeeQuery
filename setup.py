import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="seequery",  # Replace with your own username
    version="0.0.1",
    author="dwisniewski",
    author_email="wisniewski.dawid@gmail.com",
    description="SPARQL-OWL queries from Ontology Competency Questiosn generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(
         exclude=[
            "*.tests",
            "*.tests.*",
            "tests.*",
            "tests",
            "test_fixtures",
            "test_fixtures.*",
            "benchmarks",
            "benchmarks.*",
         ]
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "nltk==3.5",
        "numpy==1.18.4",
        "Owlready2==0.23",
        "python-crfsuite==0.9.7",
        "PyYAML==5.3.1",
        "regex==2020.4.4",
        "scikit-learn==0.22.2.post1",
        "scipy==1.4.1",
        "sklearn==0.0",
        "spacy==2.2.4",
        "toml==0.10.1",
        "tqdm==4.46.0"
    ],
    entry_points={
        'console_scripts': [
            'seequery = seequery.translation_loop:main',
        ],
    }
)
