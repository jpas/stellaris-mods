default: all

name = $(shell basename '$(CURDIR)')

state_dir = ${HOME}/.local/share/Paradox\ Interactive/Stellaris
game_dir = ${HOME}/.local/share/Steam/steamapps/common/Stellaris

mkdir = @mkdir -p

descriptor.mod: ./src/build.py
	python $<
	touch descriptor.mod

install: all
	$(mkdir) $(state_dir)/mod
	cp -v descriptor.mod $(state_dir)/mod/$(name).mod
	echo 'path="$(CURDIR)"' >> $(state_dir)/mod/$(name).mod

tail-logs:
	@tail -f $(state_dir)/logs/error.log $(state_dir)/logs/game.log

all: descriptor.mod
