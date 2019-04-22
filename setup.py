from setuptools import find_packages, setup


with open("README.md") as fd:
    long_description = fd.read()


setup(
    name="tamizdat",
    version="0.0.0",
    description="flibusta.net indexing and email delivery service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ioreshnikov/tamizdat",

    author="Ivan Oreshnikov",
    author_email="oreshnikov.ivan@gmail.com",

    python_requirements=[],
    install_requires=[
        "jinja2",
        "lxml",
        "python-telegram-bot",
        "py3-validate-email",
        "peewee",
        "requests",
        "transliterate"
    ],
    extra_requires=[],

    packages=find_packages(exclude=("tests",)),
    package_data={
        "tamizdat": ["templates/*.md"]
    },
    scripts=["bin/tamizdat"],
    include_package_data=True,

    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3"
    ])
