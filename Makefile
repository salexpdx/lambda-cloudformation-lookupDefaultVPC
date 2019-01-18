all: clean build deploy

clean:
	rm -rf ./build entrypoint.zip || true

# The two disabled lint rules are 
# W0703: Too many arguments on send function
# R0913: Too general of an exception handler
build: clean
	pylint -d W0703,R0913  entrypoint.py
	mkdir -p build/
	cp entrypoint.py build/
	cd build && pip3 install -t ./ -r ../requirements.txt
	cd build && cp zip -r ../entrypoint.zip .

publish: build
