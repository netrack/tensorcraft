import polynome
import os
import setuptools


here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file.
with open(os.path.join(here, "README.md"), encoding="utf-8") as md:
    long_description = md.read()


setuptools.setup(
    name="polynome",
    version=polynome.__version__,

    long_description=long_description,
    long_description_content_type="text/markdown",
    description="ML serving engine",

    url="https://github.com/netrack/polynome",
    author="Yasha Bubnov",
    author_email="girokompass@gmail.com",

    classifiers=[
      "Intended Audience :: Developers",
      "License :: OSI Approved :: MIT License",
    ],

    packages=setuptools.find_packages(exclude=["tests"]),
    tests_require=[
        "pytest-aiohttp>=0.3.0",
    ],
    install_requires=[
        "aiojobs>=0.2.2",
        "aiofiles>=0.4.0",
        "aiorwlock>=0.6.0",
        "aiohttp>=3.5.4",
        "humanize>=0.5.1",
        "numpy>=1.16.3",
        "pid>=2.2.3",
        "tensorflow>=2.0.0a0",
        "tinydb>=3.13.0",
    ],

    entry_points={
        "console_scripts": ["polynome = polynome.shell.main:main"],
    },
)
