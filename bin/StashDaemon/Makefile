# Makefile for stashcache-daemon


# ------------------------------------------------------------------------------
# Release information: Update for each release
# ------------------------------------------------------------------------------

PACKAGE := stashcache-daemon
VERSION := 0.4


# ------------------------------------------------------------------------------
# Other configuration: May need to change for a release
# ------------------------------------------------------------------------------

SBIN_FILES := stashcache
INSTALL_SBIN_DIR := usr/sbin
CONDOR_CONFIG := 01-stashcache.conf
INSTALL_CONDOR_DIR := etc/condor/config.d
PYTHON_LIB := xrootd_cache_stats.py

DIST_FILES := $(SBIN_FILES) $(CONDOR_CONFIG) $(PYTHON_LIB) Makefile


# ------------------------------------------------------------------------------
# Internal variables: Do not change for a release
# ------------------------------------------------------------------------------

DIST_DIR_PREFIX := dist_dir_
TARBALL_DIR := $(PACKAGE)-$(VERSION)
TARBALL_NAME := $(PACKAGE)-$(VERSION).tar.gz
UPSTREAM := /p/vdt/public/html/upstream
UPSTREAM_DIR := $(UPSTREAM)/$(PACKAGE)/$(VERSION)
INSTALL_PYTHON_DIR := $(shell python -c 'from distutils.sysconfig import get_python_lib; print get_python_lib()')


# ------------------------------------------------------------------------------

.PHONY: _default distclean install dist upstream check

_default:
	@echo "There is no default target; choose one of the following:"
	@echo "make install DESTDIR=path     -- install files to path"
	@echo "make dist                     -- make a distribution source tarball"
	@echo "make upstream [UPSTREAM=path] -- install source tarball to upstream cache rooted at path"
	@echo "make check                    -- use pylint to check for errors"


distclean:
	rm -f *.tar.gz
ifneq ($(strip $(DIST_DIR_PREFIX)),) # avoid evil
	rm -fr $(DIST_DIR_PREFIX)*
endif

install:
	mkdir -p $(DESTDIR)/$(INSTALL_SBIN_DIR)
	install -p -m 0755 $(SBIN_FILES) $(DESTDIR)/$(INSTALL_SBIN_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_CONDOR_DIR)
	install -p -m 0644 $(CONDOR_CONFIG) $(DESTDIR)/$(INSTALL_CONDOR_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_PYTHON_DIR)
	install -p -m 0644 $(PYTHON_LIB) $(DESTDIR)/$(INSTALL_PYTHON_DIR)

$(TARBALL_NAME): $(DIST_FILES)
	$(eval TEMP_DIR := $(shell mktemp -d -p . $(DIST_DIR_PREFIX)XXXXXXXXXX))
	mkdir -p $(TEMP_DIR)/$(TARBALL_DIR)
	cp -pr $(DIST_FILES) $(TEMP_DIR)/$(TARBALL_DIR)/
	sed -i -e 's/##VERSION##/$(VERSION)/g' $(TEMP_DIR)/$(TARBALL_DIR)/stashcache
	tar czf $(TARBALL_NAME) -C $(TEMP_DIR) $(TARBALL_DIR)
	rm -rf $(TEMP_DIR)

dist: $(TARBALL_NAME)

upstream: $(TARBALL_NAME)
ifeq ($(shell ls -1d $(UPSTREAM) 2>/dev/null),)
	@echo "Must have existing upstream cache directory at '$(UPSTREAM)'"
else ifneq ($(shell ls -1 $(UPSTREAM_DIR)/$(TARBALL_NAME) 2>/dev/null),)
	@echo "Source tarball already installed at '$(UPSTREAM_DIR)/$(TARBALL_NAME)'"
	@echo "Remove installed source tarball or increment release version"
else
	mkdir -p $(UPSTREAM_DIR)
	install -p -m 0644 $(TARBALL_NAME) $(UPSTREAM_DIR)/$(TARBALL_NAME)
	rm -f $(TARBALL_NAME)
endif

check:
	pylint -E $(SBIN_FILES) $(PYTHON_LIB)

