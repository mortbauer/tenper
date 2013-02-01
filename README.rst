======
tenper
======

Tenper is a tmux wrapper. It provides project-based tmux window/pane layouts.
It has optional support for Python's virtualenv and the conventions it uses
permits concurrent usage of virtualenvwrapper.

(The name is a corruption of 'tmuxvirtualenvwrapper'.)



Installation
============
I registered it in the PyPi, so you can ::

    pip install tenper
    # ...or...
    easy_install tenper

Or clone the repo and install it with ::

    python setup.py install
    # ...or (without admin privileges)...
    python setup.py install --user



Usage
=====

Create (or edit) a project.
---------------------------
This will open a YAML file in your environment var $EDITOR.::

    tenper edit my-project

The template looks like this.::

    # Shows up in 'tmux list-sessions' and on the left side of the status bar.
    session name: my-project

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

Start a session.
----------------
If a session already exists, you'll be reattached.::

    tenper start my-project


Delete a project.
-----------------
You'll be prompted about deleting an associated virtualenv since you might be
using it with virtualenvwrapper and want to keep it.::

    tenper del my-project


List projects.
--------------
::

    tenper list


Rebuild a virtualenv.
---------------------
If you want to change the Python binary in a virtualenv, you can edit the
project and then rebuild it with::

    tenper rebuild my-project



License
=======
Copyright (c) 2013 Mason Staugler

See LICENSE; it's the MIT license.
