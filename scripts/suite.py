import docopt
import sys

import thrash.suite
#from thrash.suite import override_arg_defaults as defaults
from thrash.config import config

doc = """
usage: fsthrash-suite --help
       fsthrash-suite [-v | -vv ] --suite_path  <suite_path>  --testdir  <testdir>   --numjobs <numjobs>  [options] [<config_yaml>...]


Miscellaneous arguments:
  -h, --help                  Show this help message and exit
  -v, --verbose               Be more verbose

Standard arguments:
  <config_yaml>               Optional extra job yaml to include
  --suite_path <suite_path>     Use this alternative directory as-is when
                              assembling jobs from yaml fragments. This causes
                              <suite_branch> to be ignored for scheduling
                              purposes, but it will still be used for test
                              running. The <suite_dir> must have `qa/suite`
                              sub-directory.

  --timeout <timeout>         How long, in seconds, to wait for jobs to finish
                              before sending email. This does not kill jobs.
                              [default: {default_results_timeout}]
  --filter KEYWORDS           Only run jobs whose description contains at least one
                              of the keywords in the comma separated keyword
                              string specified.
  --filter-out KEYWORDS       Do not run jobs whose description contains any of
                              the keywords in the comma separated keyword
                              string specified.
  --filter-all KEYWORDS       Only run jobs whose description contains each one
                              of the keywords in the comma separated keyword
                              string specified.
  --testdir <testdir>         testdir
  --debug                     default is false
  --numjobs <numjobs>          default is 1
""".format(
   default_results_timeout=config.results_timeout
) 

def main(argv=sys.argv[1:]):
    args = docopt.docopt(doc, argv=argv)
#    print args
    return thrash.suite.main(args)

if __name__ == "__main__":
    main()
