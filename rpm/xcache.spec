Name:      xcache
Summary:   XCache scripts and configurations
Version:   1.0.0
Release:   1%{?dist}
License:   Apache 2.0
Group:     Grid
URL:       https://opensciencegrid.org/docs/
BuildArch: noarch
Source0:   %{name}-%{version}.tar.gz

BuildRequires: systemd
%{?systemd_requires}

# Necessary for daemon to report back to the OSG Collector.
Requires: condor-python
Requires: python-xrootd

# We utilize a configuration directive (`continue`) introduced in XRootD 4.9.
Requires: xrootd-server >= 1:4.9.0
Requires: xrootd-libs

Requires: grid-certificates >= 7
Requires: fetch-crl

Provides: stashcache-daemon = %{name}-%{version}
Obsoletes: stashcache-daemon < 1.0.0

%description
%{summary}

%post
%systemd_post xcache-reporter.service xcache-reporter.timer
%preun
%systemd_preun xcache-reporter.service xcache-reporter.timer
%postun
%systemd_postun_with_restart xcache-reporter.service xcache-reporter.timer

########################################
%package -n stash-origin
Summary: The OSG Data Federation origin server

Requires: %{name}
Requires: wget

Provides: stashcache-origin-server = %{name}-%{version}
Obsoletes: stashcache-origin-server < 1.0.0

%description -n stash-origin
%{summary}

%post -n stash-origin
%systemd_post xrootd@stash-origin.service cmsd@stash-origin.service
%preun -n stash-origin
%systemd_preun xrootd@stash-origin.service cmsd@stash-origin.service
%postun -n stash-origin
%systemd_postun_with_restart xrootd@stash-origin.service cmsd@stash-origin.service

########################################
%package -n stash-cache
Summary: The OSG data federation cache server

Requires: %{name}
Requires: wget
Requires: xrootd-lcmaps >= 1.5.1
Requires: globus-proxy-utils

Provides: stashcache-cache-server = %{name}-%{version}
Provides: stashcache-cache-server-auth = %{name}-%{version}
Obsoletes: stashcache-cache-server < 1.0.0
Obsoletes: stashcache-cache-server-auth < 1.0.0

%description -n stash-cache
%{summary}

%post -n stash-cache
%systemd_post xrootd@stash-cache.service stash-cache-authfile.service stash-cache-authfile.timer xrootd@stash-cache-auth.service xrootd-renew-proxy.service xrootd-renew-proxy.timer
%preun -n stash-cache
%systemd_preun xrootd@stash-cache.service stash-cache-authfile.service stash-cache-authfile.timer xrootd@stash-cache-auth.service xrootd-renew-proxy.service xrootd-renew-proxy.timer
%postun -n stash-cache
%systemd_postun_with_restart xrootd@stash-cache.service stash-cache-authfile.service stash-cache-authfile.timer xrootd@stash-cache-auth.service xrootd-renew-proxy.service xrootd-renew-proxy.timer

%prep
%setup -n %{name}-%{version} -q

%install
%if 0%{?el6}
echo "*** This version does not build on EL 6 ***"
exit 1
%endif
mkdir -p %{buildroot}%{_sysconfdir}/xrootd
make install DESTDIR=%{buildroot}

# Create xrootd certificate directory
mkdir -p %{buildroot}%{_sysconfdir}/grid-security/xrd

%files
%{_libexecdir}/%{name}/xcache-reporter
%{python_sitelib}/xrootd_cache_stats.py*
%{_unitdir}/xcache-reporter.service
%{_unitdir}/xcache-reporter.timer
%config %{_sysconfdir}/xrootd/config.d/40-osg-monitoring.cfg
%config %{_sysconfdir}/xrootd/config.d/40-osg-paths.cfg
%config(noreplace) %{_sysconfdir}/xrootd/config.d/90-xcache-logging.cfg
%config(noreplace) %{_sysconfdir}/xrootd/digauth.cfg
%attr(-, xrootd, xrootd) %{_sysconfdir}/grid-security/xrd

%files -n stash-origin
%config %{_sysconfdir}/xrootd/xrootd-stash-origin.cfg
%config %{_sysconfdir}/xrootd/xrootd-stash-origin-auth.cfg
%config %{_sysconfdir}/xrootd/config.d/50-stash-origin-authz.cfg
%config %{_sysconfdir}/xrootd/config.d/50-stash-origin-paths.cfg
%config(noreplace) %{_sysconfdir}/xrootd/config.d/10-origin-site-local.cfg
%{_libexecdir}/%{name}/authfile-update
%{_unitdir}/stash-origin-authfile.service
%{_unitdir}/stash-origin-authfile.timer
%{_unitdir}/xrootd@stash-origin.service.d/10-stash-origin-overrides.conf
%{_unitdir}/xrootd@stash-origin-auth.service.d/10-stash-origin-auth-overrides.conf
%{_tmpfilesdir}/stash-origin.conf
%attr(0755, xrootd, xrootd) %dir /run/stash-origin/
%attr(0755, xrootd, xrootd) %dir /run/stash-origin-auth/

%files -n stash-cache
%config(noreplace) %{_sysconfdir}/xrootd/Authfile-auth
%config(noreplace) %{_sysconfdir}/xrootd/xcache-robots.txt
%config %{_sysconfdir}/xrootd/xrootd-stash-cache.cfg
%config %{_sysconfdir}/xrootd/xrootd-stash-cache-auth.cfg
%config %{_sysconfdir}/xrootd/config.d/40-osg-http.cfg
%config %{_sysconfdir}/xrootd/config.d/40-osg-xcache.cfg
%config %{_sysconfdir}/xrootd/config.d/50-stash-cache-authz.cfg
%config(noreplace) %{_sysconfdir}/xrootd/config.d/10-cache-site-local.cfg
%{_libexecdir}/%{name}/authfile-update
%{_libexecdir}/%{name}/renew-proxy
%{_unitdir}/xrootd-renew-proxy.service
%{_unitdir}/xrootd-renew-proxy.timer
%{_unitdir}/stash-cache-authfile.service
%{_unitdir}/stash-cache-authfile.timer
%{_unitdir}/xrootd@stash-cache.service.d/10-stash-cache-overrides.conf
%{_unitdir}/xrootd@stash-cache-auth.service.d/10-stash-cache-auth-overrides.conf
%{_tmpfilesdir}/stash-cache.conf
%attr(0755, xrootd, xrootd) %dir /run/stash-cache/
%attr(0755, xrootd, xrootd) %dir /run/stash-cache-auth/

%changelog
* Mon Jan 14 2019 Brian Bockelman <brian.bockelman@cern.ch> - 1.0.0-1
- Final release of XCache 1.0.0.

* Fri Jan 11 2019 Mátyás Selmeci <matyas@cs.wisc.edu> - 1.0.0-0.rc2
- Auto-generate the origin authorization files as well.
- Fix configuration file syntax.

* Mon Jan 7 2019 Brian Bockelman <bbockelm@cse.unl.edu> - 1.0.0-0.rc1
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

