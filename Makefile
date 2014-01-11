plugin_name=e2iptv
extensions_path=/usr/lib/enigma2/python/Plugins/Extensions
skins_path=/usr/share/enigma2

SOURCES := $(shell find build -name '*.py')

init:
	if ! test -d build; then \
		mkdir -p "build/${extensions_path}/${plugin_name}"; \
	fi

clean:
	if test -d build; then rm -rf build; fi

build: clean init
	cp -rf api build/${extensions_path}/${plugin_name}/
	cp KartinaTV.png build/${extensions_path}/${plugin_name}/
	cp -rf DEBIAN build/

$(PYC): $(SOURCES)
	./bin/py-compile $(SOURCES)
	rm $(SOURCES)

ipk:
	if ! test -d packages; \
		then mkdir packages; fi; \
	dpkg-deb -b build  packages;
	cd packages; \
	for file in `ls |grep deb`; do \
		mv $$file `echo $$file |sed s/deb/ipk/`; \
	done
