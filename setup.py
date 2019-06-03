import bothe
import os
import setuptools


here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file.
with open(os.path.join(here, "README.md"), encoding="utf-8") as md:
    long_description = md.read()


setuptools.setup(
    name="bothe",
    version=bothe.__version__,

    long_description=long_description,
    long_description_content_type="text/markdown",
    description="ML serving engine",

    url="https://github.com/netrack/bothe",
    author="Yasha Bubnov",
    author_email="girokompass@gmail.com",

    classifiers=[
      "Intended Audience :: Developers",
      "License :: OSI Approved :: MIT License",
    ],

    packages=setuptools.find_packages(exclude=["tests"]),

    entry_points={
        "console_scripts": ["bothe = bothe.shell.main:main"],
    },
)
