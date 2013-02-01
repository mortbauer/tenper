# bash completion for tenper a tmux and Python virtualenv wrapper. (Works
# concurrently with virtualenvwrapper.)

# it completes the available commands and environments for the subcommands
# to activate it just source it in your ~.bashrc
# Author: Martin Ortbauer, mortbauer@gmail.com
# Notes: inspired by the git and hg bash completion files

_tenper_commands()
{
    local commands
    commands="list edit del rebuild start"
    COMPREPLY=(${COMPREPLY[@]:-} $(compgen -W '$commands' -- "$cur"))
}

_tenper_envs()
{
    local envs
    envs="$(tenper list)"
    COMPREPLY=(${COMPREPLY[@]:-} $(compgen -W '$envs' -- "$cur"))
}

_tenper()
{
    local cur prev cmd cmd_index opts i
    # global options that receive an argument
    local global_args='--cwd|-R|--repository'
    local hg="$1"
    local canonical=0

    COMPREPLY=()
    cur="$2"
    prev="$3"

    # searching for the command
    # (first non-option argument that doesn't follow a global option that
    #  receives an argument)
    for ((i=1; $i<=$COMP_CWORD; i++)); do
	if [[ ${COMP_WORDS[i]} != -* ]]; then
	    if [[ ${COMP_WORDS[i-1]} != @($global_args) ]]; then
		cmd="${COMP_WORDS[i]}"
		cmd_index=$i
		break
	    fi
	fi
    done

    if [ -z "$cmd" ] || [ $COMP_CWORD -eq $i ]; then
        _tenper_commands
        return
    fi

    # complete subcommands with envs
    case "$cmd" in
        edit)
            _tenper_envs
            return
        ;;
        del)
            _tenper_envs
            return
        ;;
        rebuild)
            _tenper_envs
            return
        ;;
        start)
            _tenper_envs
            return
        ;;
    esac
}

complete -o bashdefault -o default -F _tenper tenper
