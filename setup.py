#!/usr/bin/env python

from setuptools import find_packages, setup

with open("requirements.txt") as req_file:
    install_requires = [
        req for req in req_file if req.strip() and not req.lstrip().startswith("#")
    ]


setup(
    name="hub20",
    url="https://github.com/mushroomlabs/hub20",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    zip_safe=False,
    classifiers=["Operating System :: Linux"],
    keywords="hub20 ethereum payment-gateway",
)
