.PHONY: build
run: build
	python3 orrery.py
build: 
	python3 builder.py
prepUbuntu:
	sudo apt-get update
	sudo apt-get -y install python3.6 python3-pip
	sudo apt-get install python3-tk

clean-build:
	-rm bin/*
clean: clean-build
	if [ -d "__pycache__" ]; then\
		rm __pycache__/*;\
		rmdir __pycache__;\
	fi


