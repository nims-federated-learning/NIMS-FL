# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

.PHONY: docker-sphinx
docker-sphinx:
	@docker run --rm -v $$(pwd):/docs sphinxdoc/sphinx-latexpdf make prep-and-run USER=$$(id -u) GROUP=$$(id -g)

###
## Do not run this target directly => use make docker-sphinx
## used by docker-sphinx to install the extension module missing in the std images
## but required for our build, then it will launch the latexpdf command
.PHONY: prep-and-run
prep-and-run:
	@pip install sphinx-rtd-theme
	@groupadd -g $(GROUP) docker-group
	@useradd -g docker-group -u $(USER) docker-user
	@su -g docker-group - docker-user bash -l -c 'cd /docs; make latexpdf'
###


# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
