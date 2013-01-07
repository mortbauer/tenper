#!/usr/bin/env python
"""Tenper is a tmux wrapper with support for Python virtualenv.

It uses virtualenvwrapper's conventions, so they'll work side-by-side.

The name is a corruption of gibberish:
    tmuxvirtualenvwrapper -> tenvpapper -> tenper.
"""

import argparse
import os
import shutil
import subprocess
import sys

import yaml


shell = os.getenv('SHELL')
editor = os.getenv('EDITOR')
configs = os.path.join(os.path.expanduser('~'), '.tenper')
virtualenvs = os.path.join(os.path.expanduser('~'), '.virtualenvs')
config_template = """# Shows up in 'tmux list-sessions' and on the left side of the status bar.
session name: {env}

# Optional; if provided, the virtualenv activate script will be sourced in all
# new windows and panes by setting tmux's default-command option.
virtualenv:
    python binary: /usr/bin/python
    site packages?: false

# When starting a tenper session, all windows and panes will be changed to this
# directory.
project root: $HOME

windows:
  - name: One
    panes:
      - ls -l

  - name: Two
    # Layout of the panes: even-horizontal, even-vertical, main-horizontal,
    # main-vertical, or tiled. You can also specify the layout string in the
    # list-windows command (see man tmux's layout section).
    layout: main-vertical
    panes:
        - ls
        - vim
        - top
"""


def command_list(template, **kwargs):
    """Split a command into an array (for subprocess).

    >>> command_list('ls')
    ['ls']
    >>> command_list('ls /')
    ['ls', '/']
    >>> command_list('echo {message}', message='Hello, world.')
    ['echo', 'Hello, world.']

    Args:
        template: A string that will be split on ' ' and will have the
            remaining arguments to this function applied to the 'format' of
            each segment.

    Returns:
        A list of strings.
    """

    return [part.format(**kwargs) for part in template.split(' ')]


def run(cmd, **kwargs):
    """Run a command template (see command_list)."""

    return subprocess.call(command_list(cmd, **kwargs))


def config_for(env):
    """Return config (parsed YAML) for an environment.

    Args:
        env: An environment name.
    Returns:
        A dictionary of configuration.

    Raises:
        Exception; config file not found.
    """
    fn = os.path.join(configs, '{}.yml'.format(env))
    if os.path.exists(fn):
        with open(fn, 'r') as f:
            return yaml.load(f)

    raise Exception((
        'No configuration found for environment "{}". '
        '(Checked: {})').format(env, fn))


def confirm_virtualenv(config, delete_first=False):
    """Make sure the virtualenv is set up, if needed.

    Args:
        config: The environment dictionary.
        delete_first: If this is true, we'll delete an existing virtualenv.
    """
    # Short circuit: we're not using a virtualenv.
    if not config.get('virtualenv'):
        return

    path = os.path.join(virtualenvs, config['session name'])

    # Short circuit: virtualenv exists and we're not deleting it.
    if os.path.exists(path) and not delete_first:
        return

    if delete_first:
        shutil.rmtree(path)

    run('virtualenv -p {python_binary} {site_packages} {dir}',
        python_binary=config['virtualenv'].get('python binary', '/usr/bin/python'),
        site_packages='--system-site-packages' if config['virtualenv'].get('site packages?', False) else '--no-site-packages',
        dir=path)


def list_envs():
    """Print a list of the available yaml file names to stdout."""

    print('Available environments:')
    if not os.path.exists(configs):
        print('    None.')
    else:
        for f in os.listdir(configs):
            if f.endswith('.yml'):
                print('    {}'.format(f[0:-4]))


def edit(env):
    """Edit an environment; creates a new one if it doesn't exist."""

    if not os.path.exists(configs):
        os.mkdir(configs)

    config_file = os.path.join(configs, '{}.yml'.format(env))
    if not os.path.exists(config_file):
        with open(config_file, 'w') as f:
            f.write(config_template.format(env=env))

    run('{editor} {file}', editor=editor, file=config_file)


def delete(env):
    """Delete an environment; prompted to delete the virtualenv if it
    exists."""

    config_file = os.path.join(configs, '{}.yml'.format(env))
    virtualenv = os.path.join(virtualenvs, env)

    if os.path.exists(virtualenv):
        prompt = (
            'There\'s a virtualenv for this environment in {}. Do you want to '
            'delete it? ').format(virtualenv)
        try:
            resp = raw_input(prompt)
        except:
            resp = input(prompt)

        if resp.strip() in ['yes', 'YES', 'y', 'Y']:
            shutil.rmtree(virtualenv)
            print('Deleted {}.'.format(virtualenv))

    os.remove(config_file)
    print('Removed {}.'.format(config_file))

    try:
        # Clean up after ourselves.
        os.rmdir(configs)
    except: pass


def rebuild(env):
    """Rebuild a virtualenv."""

    confirm_virtualenv(config_for(env), delete_first=True)


def start(env):
    config = config_for(env)
    confirm_virtualenv(config)
    session = config['session name']
    virtualenv = config.get('virtualenv', None)
    virtualenv_path = os.path.join(virtualenvs, session, 'bin', 'activate') if virtualenv else None

    # Short circuit for a preexisting session.
    if run('tmux has-session -t {session}', session=config['session name']) == 0:
        prompt = 'Session already exists: attaching. (Press any key to continue.)'
        try:
            raw_input(prompt)
        except:
            input(prompt)

        run('tmux -2 attach-session -t {session}', session=config['session name'])
        return

    # Start the session.
    run('tmux new-session -d -s {session}', session=config['session name'])

    # Provide a venv environment variable. It's possible this should be named
    # something more unique, but since we'll be using it to manually run
    # 'source $venv', I'm opting for brevity.
    if virtualenv:
        run('tmux set-environment -t {session} venv {path}',
            session=session,
            path=virtualenv_path)

    for index, window in enumerate(config['windows']):
        window_target = ':'.join([session, str(index)])

        # Create the window (or rename the first window).
        if index == 0:
            run('tmux rename-window -t {window_target} {name}',
                window_target=window_target,
                name=window['name'])
        else:
            run('tmux new-window -t {window_target} -n {name}',
                window_target=window_target,
                name=window['name'])

        for pindex, pane in enumerate(window.get('panes', [])):
            pane_target = '{}.{}'.format(window_target, pindex)

            if pindex != 0:
                run('tmux split-window -t {window_target}.0',
                    window_target=window_target)

            # Activate the virtualenv.
            if virtualenv:
                run('tmux send-keys -t {pane_target} {command} ENTER',
                    pane_target=pane_target,
                    command='source {}'.format(virtualenv_path))

            # Go to the project directory.
            run('tmux send-keys -t {pane_target} {command} ENTER',
                pane_target=pane_target,
                command='cd {}'.format(config['project root']))

            # Run the window command, if available.
            if pane:
                run('tmux send-keys -t {pane_target} {command} ENTER',
                    pane_target=pane_target,
                    command=pane)

        if window.get('layout'):
            run('tmux select-layout -t {window_target} {layout}',
                window_target=window_target,
                layout=window['layout'])

        run('tmux select-pane -t {window_target}.0',
            window_target=window_target)

    run('tmux -2 attach-session -t {session}',
        session=session)


def parse_args(args):
    """Return a function and its arguments based on 'args'.

    Args:
        args: Probably never anything but sys.argv[1:].

    Returns:
        (callable, [...arguments])
    """

    parser = argparse.ArgumentParser(description=(
        'A wrapper for tmux sessions and (optionally) virtualenv{,wrapper}. '
        'Usage:\n'
        '  tenper -l\n'
        '  tenper -e new-environment\n'
        '  tenper --rebuild-env some-env\n'
        '  tenper some-env\n'))

    parser.add_argument('--list', '-l', action='store_true', help=(
        'List the available environments.'))
    parser.add_argument('--edit', '-e', action='store_true', help=(
        'Edit (or create) a new environment.'))
    parser.add_argument('--delete', '-d', action='store_true', help=(
        'Delete an environment. You\'ll be prompted to delete a virtualenv if '
        'it exists.'))
    parser.add_argument('--rebuild-env', action='store_true', help=(
        'If the environment uses virtualenv, rebuild it.'))
    parser.add_argument('env', nargs='?', help=(
        'An environment name.'))

    parsed = parser.parse_args(args)

    if parsed.list:
        return (list_envs, [])

    if not parsed.env:
        raise Exception('You must provide an environment name')

    if parsed.edit:
        return (edit, [parsed.env])

    if parsed.delete:
        return (delete, [parsed.env])

    if parsed.rebuild_env:
        return (rebuild, [parsed.env])

    if parsed.env:
        return (start, [parsed.env])

    # This description of the problem is rude (stupid); maybe this interface
    # sucks.
    raise Exception((
        'You must provide an environment name and maybe a flag, too. Use -h '
        'for help'))