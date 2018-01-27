.PHONY: clean build
BINDIR = ./bin

run: | $(BINDIR)
	python3 orrery.py
build:
	python3 builder.py
$(BINDIR):
	mkdir bin
	python3 builder.py
prepUbuntu:
	sudo apt-get update
	sudo apt-get -y install python3.6 python3-pip
	sudo apt-get install python3-tk

clean-build:
	@rm bin/*  2> /dev/null || true
	@rmdir bin 2> /dev/null || true

clean-py:
	@rm -f __pycache__/* 
	@rmdir __pycache__ 2>/dev/null || true 

clean: clean-build clean-py; 



