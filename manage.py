#!/usr/bin/env python
from gevent import monkey; monkey.patch_all()

from werkzeug.serving import run_with_reloader
from gevent import wsgi
from rowboat.web import rowboat
from yaml import load

import os
import copy
import click
import signal
import logging
import gevent
import subprocess


class BotSupervisor(object):
    def __init__(self, env={}):
        self.proc = None
        self.env = env
        self.bind_signals()
        self.start()

    def bind_signals(self):
        signal.signal(signal.SIGUSR1, self.handle_sigusr1)

    def handle_sigusr1(self, signum, frame):
        print 'SIGUSR1 - RESTARTING'
        gevent.spawn(self.restart)

    def start(self):
        env = copy.deepcopy(os.environ)
        env.update(self.env)
        self.proc = subprocess.Popen(['python', '-m', 'disco.cli', '--config', 'config.yaml'], env=env)

    def stop(self):
        self.proc.terminate()

    def restart(self):
        try:
            self.stop()
        except:
            pass

        self.start()

    def run_forever(self):
        while True:
            self.proc.wait()
            gevent.sleep(5)


@click.group()
def cli():
    logging.getLogger().setLevel(logging.INFO)


@cli.command()
@click.option('--reloader/--no-reloader', '-r', default=False)
def serve(reloader):
    def run():
        wsgi.WSGIServer(('0.0.0.0', 8686), rowboat.app).serve_forever()

    if reloader:
        run_with_reloader(run)
    else:
        run()


@cli.command()
@click.option('--env', '-e', default='local')
def bot(env):
    with open('config.yaml', 'r') as f:
        config = load(f)

    supervisor = BotSupervisor(env={
        'ENV': env,
        'DSN': config['DSN'],
        'GOOGLE_APPLICATION_CREDENTIALS': config['GOOGLE_APPLICATION_CREDENTIALS'],
    })
    supervisor.run_forever()


if __name__ == '__main__':
    cli()
