#!/usr/bin/env python

from setuptools import find_packages, setup

with open("requirements.txt") as req_file:
    install_requires = [
        req for req in req_file if req.strip() and not req.lstrip().startswith("#")
    ]

with open("README.md") as readme_file:
    description = readme_file.read()


setup(
    name="hub20",
    url="https://github.com/mushroomlabs/hub20",
    description=description,
    version="0.2.1",
    python_requires="~=3.7",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    zip_safe=False,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
    ],
    keywords="hub20 ethereum payment-gateway",
)
