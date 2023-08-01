from setuptools import setup, find_packages
import re

module_file = open("thrash/__init__.py").read()
metadata = dict(re.findall(r"__([a-z]+)__\s*=\s*['\"]([^'\"]*)['\"]", module_file))
long_description = open('README.rst').read()

setup(
    name='fsthrash',
    version=metadata['version'],
    packages=find_packages(),
    package_data={
     'thrash.tasks': ['adjust-ulimits', 'edit_sudoers.sh', 'daemon-helper'],
#     'thrash.tasks': ['adjust-ulimits', 'edit_sudoers.sh', 'daemon-helper'],
    },
    author='YunHui Chen.',
    author_email='18868877340@163.com',
    description='Filesystem thrash test framework',
    license='MIT',
    keywords='fsthrash test storage cluster',
    url='https://github.com/fsthrash',
    long_description=long_description,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Filesystems',
    ],
    install_requires=['gevent',
                      'PyYAML',
                      'argparse >= 1.2.1',
                      'docopt',
                      'humanfriendly',
                      ],
    extras_require = {
        'orchestra': [
            'beanstalkc3 >= 0.4.0',
        ],
    },


    # to find the code associated with entry point
    # A.B:foo first cd into directory A, open file B
    # and find sub foo
    entry_points={
        'console_scripts': [
            'fsthrash-suite = scripts.suite:main',
            'fsthrash-results = scripts.results:main',
            ],
        },

    )
