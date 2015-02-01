pyfiles_kartina := $(shell find -name '*.py' -type f)
scanver_file_kartina := api/kartina_api.py
datafiles_kartina = KartinaTV.png

all: ipk
src/%:
	ln -s . src

include ../iptvdream.mk
$(call doipk,kartina)
