import os
import time
import logging
from collections import OrderedDict
from textwrap import dedent
from textwrap import fill

import thrash
from thrash.report import ResultsReporter
from thrash import misc
from thrash import beanstalk

log = logging.getLogger(__name__)

UNFINISHED_STATUSES = ('queued', 'running')


def main(args):
    log = logging.getLogger(__name__)
    try:
        jobs_info = build_email_body(args['--name'],args['--archive-dir'])
        print jobs_info[0]
        print jobs_info[1]
        email = args['--email']
        if email:
            email_results(
            subject=subject,
            from_=('fsthrash'),
            to=email,
            body=jobs_info[1],
            )
    except Exception:
        log.exception('error generating memo/results')
        raise


def note_rerun_params(subset, seed):
    if subset:
        log.info('subset: %r', subset)
    if seed:
        log.info('seed: %r', seed)


def email_results(subject, from_, to, body):
    log.info('Sending results to {to}: {body}'.format(to=to, body=body))
    import smtplib
    from email.mime.text import MIMEText
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_
    msg['To'] = to
    log.debug('sending email %s', msg.as_string())
    return msg
    smtp = smtplib.SMTP('localhost')
    smtp.sendmail(msg['From'], [msg['To']], msg.as_string())
    smtp.quit()


def build_email_body(name, archive_base):
    stanzas = OrderedDict([
        ('fail', dict()),
        ('dead', dict()),
        ('running', dict()),
#        ('waiting', dict()),
        ('queued', dict()),
        ('pass', dict()),
    ])
    reporter = ResultsReporter(archive_base)
#    fields = ('job_id', 'status', 'description', 'duration', 'failure_reason',
#              'sentry_event', 'log_href')
    jobs = reporter.get_all_runs()
    jobs.sort(key=lambda job: job['job_id'])
    for job in jobs:
        job_stanza = format_job(name, job)
        stanzas[job['status']][job['job_id']] = job_stanza

    sections = OrderedDict.fromkeys(stanzas.keys(), '')
    subject_fragments = []
    for status in sections.keys():
        stanza = stanzas[status]
        if stanza:
            subject_fragments.append('%s %s' % (len(stanza), status))
            sections[status] = email_templates['sect_templ'].format(
                title=status.title(),
                jobs=''.join(stanza.values()),
            )
    subject = ', '.join(subject_fragments) + ' '
    
    tube = 'fsthrash'
    connection = beanstalk.connect()
    beanstalk.watch_tube(connection, tube)
    connection.use(tube)
    queued_count = int(connection.stats_tube(tube)['current-jobs-ready'])

    body = email_templates['body_templ'].format(
        name=name,
        fail_count=len(stanzas['fail']),
        dead_count=len(stanzas['dead']),
        running_count=len(stanzas['running']),
#        waiting_count=len(stanzas['waiting']),
        queued_count=queued_count,
        pass_count=len(stanzas['pass']),
        fail_sect=sections['fail'],
        dead_sect=sections['dead'],
        running_sect=sections['running'],
#        waiting_sect=sections['waiting'],
        queued_sect=sections['queued'],
        pass_sect=sections['pass'],
    )

    subject += 'in {suite}'.format(suite=name)
    return (subject.strip(), body.strip())
#    return (subject, body)


def format_job(run_name, job):
    job_id = job['job_id']
    status = job['status']
    description = job['description']
    duration = seconds_to_hms(int(job['duration'] or 0))

    if status in UNFINISHED_STATUSES:
        format_args = dict(
            job_id=job_id,
            desc=description,
            time=duration,
            info_line=job,
        )
        return email_templates['running_templ'].format(**format_args)

    if status == 'pass':
        return email_templates['pass_templ'].format(
            job_id=job_id,
            desc=description,
            time=duration,
            info_line=job,
        )
    else:
        if job['failure_reason']:
            # 'fill' is from the textwrap module and it collapses a given
            # string into multiple lines of a maximum width as specified.
            # We want 75 characters here so that when we indent by 4 on the
            # next line, we have 79-character exception paragraphs.
            reason = fill(job['failure_reason'] or '', 75)
            reason = \
                '\n'.join(('    ') + line for line in reason.splitlines())
            reason_lines = email_templates['fail_reason_templ'].format(
                reason=reason).rstrip()
        else:
            reason_lines = ''

        format_args = dict(
            job_id=job_id,
            desc=description,
            time=duration,
            info_line=job,
            reason_lines=reason_lines,
        )
        return email_templates['fail_templ'].format(**format_args)

def seconds_to_hms(seconds):
    (minutes, seconds) = divmod(seconds, 60)
    (hours, minutes) = divmod(minutes, 60)
    return "%02d:%02d:%02d" % (hours, minutes, seconds)


email_templates = {
    'body_templ': dedent("""\
        Test Run: {name}
        =================================================================
        failed:  {fail_count}
        dead:    {dead_count}
        running: {running_count}
        queued:  {queued_count}
        passed:  {pass_count}

        {fail_sect}{dead_sect}{running_sect}{queued_sect}{pass_sect}
        """),
    'sect_templ': dedent("""\

        {title}
        =================================================================
        {jobs}
        """),
    'fail_templ': dedent("""\
        [{job_id}]  {desc}
        -----------------------------------------------------------------
        time:   {time}{reason_lines}

        """),
    'info_url_templ': "\ninfo:   {info}",
    'fail_log_templ': "\nlog:    {log}",
    'fail_sentry_templ': "\nsentry: {sentry_event}",
    'fail_reason_templ': "\n\n{reason}\n",
    'running_templ': dedent("""\
        [{job_id}] {desc}{info_line}

        """),
    'pass_templ': dedent("""\
        [{job_id}] {desc}
        time:   {time}{info_line}

        """),
}
