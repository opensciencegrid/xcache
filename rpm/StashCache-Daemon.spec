Name:      xcache
Summary:   StashCache metapackages
Version:   1.0.0
Release:   1%{?dist}
License:   Apache 2.0
Group:     Grid
URL:       https://opensciencegrid.github.io/StashCache/
BuildArch: noarch
Source0:   StashCache-Daemon-%{version}.tar.gz

BuildRequires: systemd
%{?systemd_requires}

%description
%{summary}

########################################
%package daemon
Group: Grid
Summary: Scripts and configuration for StashCache management

# Necessary for daemon to report back to the OSG Collector.
Requires: condor-python
# We utilize a configuration directive (`continue`) introduced in XRootD 4.9.
Requires: xrootd-server >= 1:4.9.0
Requires: grid-certificates >= 7
Requires: fetch-crl

%description daemon
%{summary}

%post daemon
%systemd_post xcache-reporter.service xcache-reporter.timer
%preun daemon
%systemd_preun xcache-reporter.service xcache-reporter.timer
%postun daemon
%systemd_postun_with_restart xcache-reporter.service xcache-reporter.timer

########################################
%package origin-server
Group: Grid
Summary: Metapackage for the origin server

Requires: %{name}-daemon

%description origin-server
%{summary}

%post origin-server
%systemd_post xrootd@stash-origin.service cmsd@stash-origin.service
%preun origin-server
%systemd_preun xrootd@stash-origin.service cmsd@stash-origin.service
%postun origin-server
%systemd_postun_with_restart xrootd@stash-origin.service cmsd@stash-origin.service

########################################
%package cache-server
Group: Grid
Summary: Metapackage for a cache server

Requires: %{name}-daemon
Requires: curl

%description cache-server

%post cache-server
%systemd_post xrootd@stash-cache.service stash-cache-authfile.service stash-cache-authfile.timer
%preun cache-server
%systemd_preun xrootd@stash-cache.service stash-cache-authfile.service stash-cache-authfile.timer
%postun cache-server
%systemd_postun_with_restart xrootd@stash-cache.service stash-cache-authfile.service stash-cache-authfile.timer

########################################
%package cache-server-auth
Group: Grid
Summary: Metapackage for an authenticated cache server

Requires: %{name}-cache-server
Requires: xrootd-lcmaps >= 1.5.0
Requires: globus-proxy-utils

%description cache-server-auth
%{summary}

%post cache-server-auth
%systemd_post xrootd@stash-cache-auth.service xrootd-renew-proxy.service xrootd-renew-proxy.timer
%preun cache-server-auth
%systemd_preun xrootd@stash-cache-auth.service xrootd-renew-proxy.service xrootd-renew-proxy.timer
%postun cache-server-auth
%systemd_postun_with_restart xrootd@stash-cache-auth.service xrootd-renew-proxy.service xrootd-renew-proxy.timer

%prep
%setup -n StashCache-Daemon-%{version} -q

%install
%if 0%{?el6}
echo "*** This version does not build on EL 6 ***"
exit 1
%endif
mkdir -p %{buildroot}%{_sysconfdir}/xrootd
make install DESTDIR=%{buildroot}

# Create xrootd certificate directory
mkdir -p %{buildroot}%{_sysconfdir}/grid-security/xrd

%files daemon
%{_sbindir}/xcache-reporter
%{python_sitelib}/xrootd_cache_stats.py*
%{_unitdir}/xcache-reporter.service
%{_unitdir}/xcache-reporter.timer
%{_unitdir}/xrootd@stash-cache.service.d/10-stash-cache-overrides.conf
%{_unitdir}/xrootd@stash-cache-auth.service.d/10-stash-cache-auth-overrides.conf
%config %{_sysconfdir}/xrootd/config.d/40-osg-monitoring.cfg
%config %{_sysconfdir}/xrootd/config.d/40-osg-paths.cfg
%config(noreplace) %{_sysconfdir}/xrootd/config.d/50-stash-cache-logging.cfg
%config(noreplace) %{_sysconfdir}/xrootd/digauth.cfg

%files origin-server
%config %{_sysconfdir}/xrootd/xrootd-stash-origin-server.cfg
%config %{_sysconfdir}/xrootd/config.d/50-stash-origin-authz.cfg
%config %{_sysconfdir}/xrootd/config.d/50-stash-origin-paths.cfg
%config(noreplace) %{_sysconfdir}/xrootd/config.d/10-origin-site-local.cfg

%files cache-server
%config(noreplace) %{_sysconfdir}/xrootd/xcache-robots.txt
%config(noreplace) %{_sysconfdir}/xrootd/Authfile-noauth
%config %{_sysconfdir}/xrootd/xrootd-stash-cache.cfg
%config %{_sysconfdir}/xrootd/config.d/40-osg-http.cfg
%config %{_sysconfdir}/xrootd/config.d/40-osg-xcache.cfg
%config %{_sysconfdir}/xrootd/config.d/50-stash-cache-authz.cfg
%config(noreplace) %{_sysconfdir}/xrootd/config.d/10-cache-site-local.cfg
%{_libexecdir}/%{name}-cache-server/authfile-public-update
%{_tmpfilesdir}/%{name}-cache-server.conf
%attr(0755, xrootd, xrootd) %dir /run/%{name}-cache-server/

%files cache-server-auth
%config(noreplace) %{_sysconfdir}/xrootd/xrootd-stash-cache-auth.cfg
%config(noreplace) %{_sysconfdir}/xrootd/Authfile-auth
%{_unitdir}/xrootd-renew-proxy.service
%{_unitdir}/xrootd-renew-proxy.timer
%{_unitdir}/stash-cache-authfile.service
%{_unitdir}/stash-cache-authfile.timer
%{_libexecdir}/%{name}-cache-server-auth/authfile-update
%{_libexecdir}/%{name}-cache-server-auth/renew-proxy
%{_tmpfilesdir}/%{name}-cache-server-auth.conf
%attr(0755, xrootd, xrootd) %dir /run/%{name}-cache-server-auth/

%attr(-, xrootd, xrootd) %{_sysconfdir}/grid-security/xrd

%changelog
* Mon Dec 10 2018 Brian Bockelman <bbockelm@cse.unl.edu> - 1.0.0-1
- Overhaul configuration files to use new Xrootd 'continue' directive.
- Utilize systemd dependencies so all services start when XRootD does.
- Auto-generate the authorization files.

* Tue Oct 23 2018 Marian Zvada <marian.zvada@cern.ch> 0.10-1
- Remove condor daemon dependency from stats reporter
- Use systemd timer to periodically report stats
- Modify stats reporter to use python multiprocessing so ad won't expire
  during a long collection run
- Update XRootD cinfo parser to format v2

* Fri Sep 28 2018 Mátyás Selmeci <matyas@cs.wisc.edu> 0.9-1
- https://github.com/opensciencegrid/StashCache-Daemon/pull/8
  - Reduce the dependencies for the unauthenticated xrootd
  - Create the config and systemd unit files during the make install process
  - Tidy the stashcache configuration
    - Reduce the default disk usage of the cache to 90/95% to avoid
      accidentally filling filesystems too full
    - Move the certificate configuration inside the auth instance of xrootd
    - Set pfc.ram 7g to allow a bit of room for the OS on 8GB system
      (documented minimum RAM)
    - Added pss.origin redirector-itb as a commented line, rather than adding
      a separate itb config file

* Thu Aug 24 2017 Marian Zvada <marian.zvada@cern.ch> 0.8-1
- change homepage in origin server xrootd config file
- set proper redirector hostname in xrootd config files
- updated Makefile, replace properly VERSION in src/stashcache for make install target

* Thu Jun 1 2017 Marian Zvada <marian.zvada@cern.ch> 0.7-2
- added stanza so that we don't build StashCache for EL6
- no epoch of xrootd-lcmaps-1.3.3 for cache-server requirement

* Wed May 31 2017 Marian Zvada <marian.zvada@cern.ch> 0.7-1
- SOFTWARE-2295: restructure under opensciencegrid/StashCache-Daemon.git 

* Thu Feb 25 2016 Marian Zvada <marian.zvada@cern.ch> 0.6-2
- SOFTWARE-2196: redirector renamed to redirector.osgstorage.org, http export support
- SOFTWARE-2195: complete revamp of the origin server config using new redirector

* Tue Sep 29 2015 Brian Lin <blin@cs.wisc.edu> 0.6-1
- Bug fixes to xrootd service management

* Fri Sep 25 2015 Brian Lin <blin@cs.wisc.edu> 0.5-2
- Add systemd support

* Fri Sep 25 2015 Brian Lin <blin@cs.wisc.edu> 0.5-1
- Use FQDN instead of hostname in stashcache-daemon (SOFTWARE-2049)
- Refuse to start if missing host cert or key (SOFTWARE-2026)
- Fix log message if the xrootd service is already running

* Thu Aug 20 2015 Brian Lin <blin@cs.wisc.edu> 0.4-2
- Fix advertisement to central collector

* Thu Aug 20 2015 Brian Lin <blin@cs.wisc.edu> 0.4-1
- Advertise STASHCACHE_DaemonVersion in MasterAd (SOFTWARE-1971)
- Log daemon activity to /var/log/condor/StashcacheLog
- Use TCP to advertise StashCache ads

* Wed Jul 15 2015 Brian Lin <blin@cs.wisc.edu> 0.3-4
- Merge stashcache and stashcache-daemon packages

* Tue Jul 07 2015 Brian Lin <blin@cs.wisc.edu> 0.3-3
- Advertise stashcache startd and master ads to the central collector (SOFTWARE-1966)

* Tue Jun 30 2015 Brian Lin <blin@cs.wisc.edu> 0.3-2
- Restore ability for the daemon to run on EL5

* Thu Jun 25 2015 Brian Lin <blin@cs.wisc.edu> 0.3-1
- Update the cache query script

* Fri May 29 2015 Brian Lin <blin@cs.wisc.edu> 0.2-1
- Fix Python 2.6isms
- HTCondor heartbeats require at least condor-python 8.3.5

* Thu May 28 2015 Brian Lin <blin@cs.wisc.edu> 0.1-3
- Remove epoch from condor-python requirement

* Thu Apr 23 2015 Mátyás Selmeci <matyas@cs.wisc.edu> 0.1-2.osg
- Renamed stashcache-server to stashcache-cache-server, and stashcache-origin
  to stashcache-origin-server; rename config files to match

* Wed Apr 22 2015 Mátyás Selmeci <matyas@cs.wisc.edu> 0.1-1.osg
- Created metapackages with stub config files

