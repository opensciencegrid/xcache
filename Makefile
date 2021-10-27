# Makefile for xcache-daemon


# ------------------------------------------------------------------------------
# Release information: Update for each release
# ------------------------------------------------------------------------------

PACKAGE := xcache
VERSION := 3.0.0


# ------------------------------------------------------------------------------
# Other configuration: May need to change for a release
# ------------------------------------------------------------------------------

PYTHON = python

LIBEXEC_FILES := src/xcache-reporter \
                 src/authfile-update \
                 src/renew-proxy
INSTALL_LIBEXEC_DIR := usr/libexec/xcache
XROOTD_CONFIG := $(wildcard configs/atlas-xcache/xrootd/*) \
		 $(wildcard configs/cms-xcache/xrootd/*) \
		 $(wildcard configs/stash-cache/xrootd/*) \
		 $(wildcard configs/xcache/xrootd/*) \
		 $(wildcard configs/xcache-redir/xrootd/*) \
		$(wildcard configs/stash-origin/xrootd/*)


XROOTD_CONFIGD := $(wildcard configs/atlas-xcache/config.d/*) \
                  $(wildcard configs/cms-xcache/config.d/*) \
                  $(wildcard configs/stash-cache/config.d/*) \
                  $(wildcard configs/xcache/config.d/*) \
                  $(wildcard configs/xcache-redir/config.d/*) \
                  $(wildcard configs/stash-origin/config.d/*)

SYSTEMD_UNITS := $(wildcard configs/stash-cache/systemd/*) \
                 $(wildcard configs/xcache/systemd/*) \
                 $(wildcard configs/stash-origin/systemd/*) \
                 $(wildcard configs/xcache-consistency-check/systemd/*)

TMPFILES_D := configs/stash-cache/tmpfiles/stash-cache.conf \
              configs/stash-origin/tmpfiles/stash-origin.conf \
              configs/xcache/tmpfiles/xcache.conf

INSTALL_XROOTD_DIR := etc/xrootd
INSTALL_SYSTEMD_UNITDIR := usr/lib/systemd/system
PYTHON_LIB := src/xrootd_cache_stats.py

DIST_FILES := $(LIBEXEC_FILES) $(PYTHON_LIB) Makefile


# ------------------------------------------------------------------------------
# Internal variables: Do not change for a release
# ------------------------------------------------------------------------------

DIST_DIR_PREFIX := dist_dir_
TARBALL_DIR := $(PACKAGE)-$(VERSION)
TARBALL_NAME := $(PACKAGE)-$(VERSION).tar.gz
UPSTREAM := /p/vdt/public/html/upstream
UPSTREAM_DIR := $(UPSTREAM)/$(PACKAGE)/$(VERSION)
INSTALL_PYTHON_DIR := $(shell $(PYTHON) -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())')


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
	mkdir -p $(DESTDIR)/$(INSTALL_LIBEXEC_DIR)
	install -p -m 0755 $(LIBEXEC_FILES) $(DESTDIR)/$(INSTALL_LIBEXEC_DIR)
	sed -i -e 's/##VERSION##/$(VERSION)/g' $(DESTDIR)/$(INSTALL_LIBEXEC_DIR)/xcache-reporter
	mkdir -p $(DESTDIR)/$(INSTALL_PYTHON_DIR)
	install -p -m 0644 $(PYTHON_LIB) $(DESTDIR)/$(INSTALL_PYTHON_DIR)
	mkdir -p $(DESTDIR)/$(INSTALL_XROOTD_DIR)
	# XRootD configuration files
	install -p -m 0644 $(XROOTD_CONFIG) $(DESTDIR)/$(INSTALL_XROOTD_DIR)
	ln -srf $(DESTDIR)/$(INSTALL_XROOTD_DIR)/xrootd-stash-cache.cfg $(DESTDIR)/$(INSTALL_XROOTD_DIR)/xrootd-stash-cache-auth.cfg
	ln -srf $(DESTDIR)/$(INSTALL_XROOTD_DIR)/xrootd-stash-origin.cfg $(DESTDIR)/$(INSTALL_XROOTD_DIR)/xrootd-stash-origin-auth.cfg
	mkdir -p $(DESTDIR)/$(INSTALL_XROOTD_DIR)/config.d
	install -p -m 0644 $(XROOTD_CONFIGD) $(DESTDIR)/$(INSTALL_XROOTD_DIR)/config.d
	# Condor config files
	mkdir -p $(DESTDIR)/etc/condor/config.d
	install -p -m 0644 configs/xcache/condor/01-xcache-reporter-auth.conf $(DESTDIR)/etc/condor/config.d/01-xcache-reporter-auth.conf
	# XCache Consistency Check
	mkdir -p $(DESTDIR)/usr/bin
	mkdir -p $(DESTDIR)/var/lib/xcache-consistency-check
	install -p -m 0755 src/xcache-consistency-check $(DESTDIR)/usr/bin/xcache-consistency-check
	install -p -m 0644 configs/xcache-consistency-check/xrootd/xcache-consistency-check.cfg $(DESTDIR)/etc/xrootd/xcache-consistency-check.cfg
	# systemd unit files
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)
	install -p -m 0644 $(SYSTEMD_UNITS) $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)
	# systemd unit overrides
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd-renew-proxy.service.d
	# stash-cache
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@stash-cache.service.d
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@stash-cache-auth.service.d
	install -p -m 0644 configs/stash-cache/overrides/10-stash-cache-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@stash-cache.service.d/
	install -p -m 0644 configs/stash-cache/overrides/10-stash-cache-auth-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@stash-cache-auth.service.d/
	# stash-origin
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@stash-origin.service.d
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@stash-origin-auth.service.d
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/cmsd@stash-origin.service.d
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/cmsd@stash-origin-auth.service.d
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd-privileged@stash-origin-auth.service.d
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/cmsd-multiuser@stash-origin-auth.service.d
	install -p -m 0644 configs/stash-origin/systemd/cmsd-multiuser@.service $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/cmsd-multiuser@.service
	install -p -m 0644 configs/stash-origin/overrides/xrootd/10-stash-origin-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@stash-origin.service.d/
	install -p -m 0644 configs/stash-origin/overrides/xrootd/10-stash-origin-auth-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@stash-origin-auth.service.d/
	install -p -m 0644 configs/stash-origin/overrides/xrootd-privileged/10-stash-origin-auth-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd-privileged@stash-origin-auth.service.d/
	install -p -m 0644 configs/stash-origin/overrides/cmsd/10-stash-origin-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/cmsd@stash-origin.service.d/
	install -p -m 0644 configs/stash-origin/overrides/cmsd/10-stash-origin-auth-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/cmsd@stash-origin-auth.service.d/
	install -p -m 0644 configs/stash-origin/overrides/cmsd-multiuser/10-stash-origin-auth-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/cmsd-multiuser@stash-origin-auth.service.d/
	# atlas-xcache
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@atlas-xcache.service.d
	install -p -m 0644 configs/atlas-xcache/overrides/10-atlas-xcache-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@atlas-xcache.service.d/
	install -p -m 0644 configs/atlas-xcache/overrides/xrootd-renew-proxy/10-atlas-refresh-proxy-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd-renew-proxy.service.d/
	# cms-xcache
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@cms-xcache.service.d
	mkdir -p $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/cmsd@cms-xcache.service.d
	install -p -m 0644 configs/cms-xcache/overrides/xrootd/10-cms-xcache-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd@cms-xcache.service.d/
	install -p -m 0644 configs/cms-xcache/overrides/cmsd/10-cms-xcache-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/cmsd@cms-xcache.service.d/
	install -p -m 0644 configs/cms-xcache/overrides/xrootd-renew-proxy/10-cms-refresh-proxy-overrides.conf $(DESTDIR)/$(INSTALL_SYSTEMD_UNITDIR)/xrootd-renew-proxy.service.d/
	# systemd tempfiles
	mkdir -p $(DESTDIR)/run/stash-cache
	mkdir -p $(DESTDIR)/run/stash-cache-auth
	mkdir -p $(DESTDIR)/run/stash-origin
	mkdir -p $(DESTDIR)/run/stash-origin-auth
	mkdir -p $(DESTDIR)/run/xcache-auth
	mkdir -p $(DESTDIR)/run/xcache-redir
	mkdir -p $(DESTDIR)/usr/lib/tmpfiles.d
	install -p -m 0644 $(TMPFILES_D) $(DESTDIR)/usr/lib/tmpfiles.d

$(TARBALL_NAME): $(DIST_FILES)
	$(eval TEMP_DIR := $(shell mktemp -d -p . $(DIST_DIR_PREFIX)XXXXXXXXXX))
	mkdir -p $(TEMP_DIR)/$(TARBALL_DIR)
	cp -pr $(DIST_FILES) $(TEMP_DIR)/$(TARBALL_DIR)/
	sed -i -e 's/##VERSION##/$(VERSION)/g' $(TEMP_DIR)/$(TARBALL_DIR)/xcache-reporter
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
	pylint -E $(LIBEXEC_FILES) $(PYTHON_LIB)
