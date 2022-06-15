VERSION ?= 0.1

IMAGE_NAME ?= xapp-test
CONTAINER_NAME ?= xapp-test
REPOSITORY ?= edgeapps-docker-local.artifactory-blr1.int.net.nokia.com

.PHONY: build push run rm release

build: examples/Dockerfile-Xapp
	docker build -t $(IMAGE_NAME):$(VERSION) -f examples/Dockerfile-Xapp .

push:
	docker tag $(IMAGE_NAME):$(VERSION) $(REPOSITORY)/$(IMAGE_NAME):$(VERSION)
	docker push $(REPOSITORY)/$(IMAGE_NAME):$(VERSION)

run:
	docker run --rm --name $(CONTAINER_NAME) -ti $(ENV) $(IMAGE_NAME):$(VERSION)

rm:
	docker rm $(CONTAINER_NAME)

default: build
