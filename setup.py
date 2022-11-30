from setuptools import setup

setup(
    name='pybimi',
    version='0.0.1',
    author='Alex Do',
    author_email='alex@twofive25.com',
    packages=[
        'pybimi',
    ],
    package_data={
        'pybimi': [
            'cacert.pem',
            'jing.jar',
            'SVG_PS-latest.rnc',
        ]
    },
    include_package_data=True,
    url='https://github.com/anhdowastaken/pybimi',
    license='LICENSE',
    description='A BIMI validator',
    install_requires=[
        'asn1crypto',
        'cachetools',
        'certvalidator',
        'dnspython',
        'requests',
        'tld',
    ],
)