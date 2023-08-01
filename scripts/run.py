"""
usage: fsthrash --help
       fsthrash --version
       fsthrash [options] [--] <config>...

Run fsthrash tests

positional arguments:
  <config> one or more config files to read

optional arguments:
  -h, --help                     show this help message and exit
  -v, --verbose                  be more verbose
  --version                      the current installed version of fsthrash
  -a DIR, --archive DIR          path to archive results in
  --description DESCRIPTION      job description
  --name NAME                    name for this fsthrash run
  --suite-path SUITE_PATH        Location of suites on disk. If not specified,
                                 it will be fetched
"""
import docopt

import thrash.run


def main():
    args = docopt.docopt(__doc__, version=fsthrash.__version__)
    thrash.run.main(args)
