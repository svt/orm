import os

from setuptools import setup

setup(
    name='origin-routing-machine',
    # Do not set 'version' manually and do not check in generated version.
    # 'version' is substituted when running make. See the Makefile.
    version=os.environ.get('ORM_TAG', 'no_tag'),
    author='Webcore Infra',
    author_email='webcore-infra@svt.se',
    packages=['orm'],
    include_package_data=True,
    entry_points={
        'console_scripts': ['orm=orm.__main__:main']
    },
    url='https://github.com/SVT/orm',
    license='MIT License',
    description=('Origin Routing Machine. '
                 'Generating config for HTTP routing software.'),
    install_requires=[
        'pyyaml>=5.1,<6',
        'jsonschema>=2.6.0,<3',
        'rfc3986>=1.2.0,<2',
        'greenery>=3.1,<4',
        'requests>=2.18.4,<3',
        'jinja2>=2.10,<3'
    ],
)
