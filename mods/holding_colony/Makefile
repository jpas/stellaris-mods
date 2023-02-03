name=$(shell basename '$(CURDIR)')

state_dir=${HOME}/.local/share/Paradox\ Interactive/Stellaris
game_dir=${HOME}/.local/share/Steam/steamapps/common/Stellaris

install:
	cp descriptor.mod $(state_dir)/mod/$(name).mod
	echo 'path="$(CURDIR)"' >> $(state_dir)/mod/$(name).mod

archive:
	git archive --format tar -o "$(name).tar" main

update:
	./update.sh

