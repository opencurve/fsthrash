"""
usage: fsthrash-results [-h] [-v] [--dry-run] [--email EMAIL]  [--timeout TIMEOUT] --archive-dir DIR --name NAME

Email fsthrash suite results

optional arguments:
  -h, --help         show this help message and exit
  -v, --verbose      be more verbose
  --timeout TIMEOUT  how many seconds to wait for all tests to finish
                     [default: 0]
  --archive-dir DIR  path under which results for the suite are stored
  --name NAME        name of the suite
  --email EMAIL      address to email test failures to
"""
import docopt
import thrash.results


def main():
    args = docopt.docopt(__doc__)
    thrash.results.main(args)

if __name__ == "__main__":
    main()
