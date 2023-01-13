default: all

state_dir = ${HOME}/.local/share/Paradox\ Interactive/Stellaris
game_dir = ${HOME}/.local/share/Steam/steamapps/common/Stellaris

mkdir = @mkdir -p

tail-logs:
	@tail -f $(state_dir)/logs/error.log $(state_dir)/logs/game.log

setup:
	ln -sfT $(game_dir) game_dir
	ln -sfT $(state_dir) state_dir

all:
