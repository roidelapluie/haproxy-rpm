%{?scl:%scl_package haproxy}
%{!?scl:%global pkg_name %{name}}

%define haproxy_user    haproxy
%define haproxy_group   %{haproxy_user}
%define haproxy_home    %{_root_localstatedir}/lib/haproxy
%define haproxy_confdir %{_sysconfdir}/haproxy
%define haproxy_datadir %{_datadir}/haproxy

%{?el8:%global _hardened_build 1}

%if 0%{!?scl:1}
%global _root_sbindir %{_sbindir}
%global _root_sysconfdir %{_sysconfdir}
%global _root_localstatedir %{_localstatedir}
%endif

Name:           %{?scl_prefix}haproxy
Version:        2.1.0
Release:        7%{?dist}
Summary:        TCP/HTTP proxy and load balancer for high availability environments

Group:          System Environment/Daemons
License:        GPLv2+

URL:            http://www.haproxy.org/
Source0:        https://www.haproxy.org/download/2.1/src/%{pkg_name}-%{version}.tar.gz
Source1:        %{pkg_name}.service
Source2:        %{pkg_name}.cfg
Source3:        %{pkg_name}.logrotate
Source4:        %{pkg_name}.sysconfig
Source5:        halog.1

Patch0:        fa137e3b5c994508370e0cd2396ece081a1316c4.patch

%{?el8:BuildRequires:  lua-devel}
%{?el7:BuildRequires:  lua53-static}
%{?el7:BuildRequires:  lua53-devel}
BuildRequires:  pcre-devel
BuildRequires:  zlib-devel
BuildRequires:  openssl-devel
BuildRequires:  systemd-units
BuildRequires:  systemd-devel
%if 0%{!?scl:1}
BuildRequires:  scl-utils-build
%endif

%{?scl:Requires: %scl_runtime}

Requires(pre):      shadow-utils
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd

%description
HAProxy is a TCP/HTTP reverse proxy which is particularly suited for high
availability environments. Indeed, it can:
 - route HTTP requests depending on statically assigned cookies
 - spread load among several servers while assuring server persistence
   through the use of HTTP cookies
 - switch to backup servers in the event a main server fails
 - accept connections to special ports dedicated to service monitoring
 - stop accepting connections without breaking existing ones
 - add, modify, and delete HTTP headers in both directions
 - block requests matching particular patterns
 - report detailed status to authenticated users from a URI
   intercepted by the application

%if 0%{?scl:1}
%scl_syspaths_package -d
%endif

%prep
%setup -q -n %{pkg_name}-%{version}
%patch0 -p1

%build
regparm_opts=
%ifarch %ix86 x86_64
regparm_opts="USE_REGPARM=1"
%endif

%{__make} %{?_smp_mflags} CPU="generic" TARGET="linux-glibc" USE_LUA=1 ${?el7:LUA_LIB_NAME=:liblua.a} USE_OPENSSL=1 USE_PCRE=1 USE_ZLIB=1 USE_CRYPT_H=1 USE_SYSTEMD=1 USE_LINUX_TPROXY=1 USE_GETADDRINFO=1 ${regparm_opts} ADDINC="%{optflags}" ADDLIB="%{__global_ldflags}" EXTRA_OBJS="contrib/prometheus-exporter/service-prometheus.o"

pushd contrib/halog
%{__make} halog OPTIMIZE="%{optflags}" LDFLAGS=
popd

pushd contrib/iprange
%{__make} iprange OPTIMIZE="%{optflags}" LDFLAGS=
popd

%install
%{__make} install-bin DESTDIR=%{buildroot} PREFIX=%{_prefix} TARGET="linux2628"
%{__make} install-man DESTDIR=%{buildroot} PREFIX=%{_prefix}

%{__install} -p -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
%{__install} -p -D -m 0644 %{SOURCE2} %{buildroot}%{haproxy_confdir}/%{pkg_name}.cfg
%{__install} -p -D -m 0644 %{SOURCE3} %{buildroot}%{_root_sysconfdir}/logrotate.d/%{name}
%{__install} -p -D -m 0644 %{SOURCE4} %{buildroot}%{_root_sysconfdir}/sysconfig/%{name}
%{__install} -p -D -m 0644 %{SOURCE5} %{buildroot}%{_mandir}/man1/halog.1
%{__install} -d -m 0755 %{buildroot}%{haproxy_home}
%if 0%{?scl:1}
%{__install} -d -m 0755 %{buildroot}%{_localstatedir}/lib/%{pkg_name}
%endif
%{__install} -d -m 0755 %{buildroot}%{haproxy_datadir}
%{__install} -d -m 0755 %{buildroot}%{_bindir}
%{__install} -p -m 0755 ./contrib/halog/halog %{buildroot}%{_bindir}/halog
%{__install} -p -m 0755 ./contrib/iprange/iprange %{buildroot}%{_bindir}/iprange
%{__install} -p -m 0644 ./examples/errorfiles/* %{buildroot}%{haproxy_datadir}

for httpfile in $(find ./examples/errorfiles/ -type f)
do
    %{__install} -p -m 0644 $httpfile %{buildroot}%{haproxy_datadir}
done

%{__rm} -rf ./examples/errorfiles/

find ./examples/* -type f ! -name "*.cfg" -exec %{__rm} -f "{}" \;

for textfile in $(find ./ -type f -name "*.txt" -o -name README)
do
    %{__mv} $textfile $textfile.old
    iconv --from-code ISO8859-1 --to-code UTF-8 --output $textfile $textfile.old
    %{__rm} -f $textfile.old
done

# scl paths fixes
%if 0%{?scl:1}
sed -i \
    -e 's|%{_root_sysconfdir}/sysconfig/%{pkg_name}|%{_root_sysconfdir}/sysconfig/%{name}|g' \
    -e 's|%{_root_sbindir}|%{_sbindir}|g' \
    -e 's|/run/%{pkg_name}.pid|/run/%{name}.pid|g' \
    -e 's|%{_root_sysconfdir}/haproxy|%{haproxy_confdir}|g' \
    %{buildroot}%{_unitdir}/%{name}.service

sed -i \
    -e 's|%{_root_localstatedir}/log|%{_localstatedir}/log|g' \
    -e 's|%{_root_localstatedir}/lib/%{pkg_name}|%{_localstatedir}/lib/%{pkg_name}|g' \
    -e 's|/run/%{pkg_name}|/run/%{name}|g' \
    %{buildroot}%{haproxy_confdir}/%{pkg_name}.cfg

sed -i \
    -e 's|%{_root_localstatedir}/log|%{_localstatedir}/log|g' \
    %{buildroot}%{_root_sysconfdir}/logrotate.d/%{name}

%scl_syspaths_install_wrapper -n haproxy -m link %{haproxy_confdir}/%{pkg_name}.cfg %{_root_sysconfdir}/haproxy/%{pkg_name}.cfg
%scl_syspaths_install_wrapper -n haproxy -m link %{_unitdir}/%{name}.service %{_unitdir}/%{pkg_name}.service

%endif

%pre
getent group %{haproxy_group} >/dev/null || groupadd -f -g 188 -r %{haproxy_group}
if ! getent passwd %{haproxy_user} >/dev/null ; then
    if ! getent passwd 188 >/dev/null ; then
        useradd -r -u 188 -g %{haproxy_group} -d %{haproxy_home} -s /sbin/nologin -c "haproxy" %{haproxy_user}
    else
        useradd -r -g %{haproxy_group} -d %{haproxy_home} -s /sbin/nologin -c "haproxy" %{haproxy_user}
    fi
fi

%post
%systemd_post %{name}.service
%if 0%{?scl:1}
semanage fcontext -d "%{_unitdir}/%{name}.service" >/dev/null 2>&1 || :
semanage fcontext -a -e "%{_unitdir}/%{pkg_name}.service" "%{_unitdir}/%{name}.service" >/dev/null 2>&1 || :
semanage fcontext -a -e /var/run/%{pkg_name}.sock /var/run/%{name}.sock
semanage fcontext -a -e /var/run/%{pkg_name}.stat /var/run/%{name}.stat
selinuxenabled && load_policy || :
restorecon -R "%{?_scl_root}/" >/dev/null 2>&1 || :
restorecon -R "%{_sysconfdir}" >/dev/null 2>&1 || :
restorecon -R "%{_localstatedir}" >/dev/null 2>&1 || :
restorecon "%{_unitdir}/%{name}.service" >/dev/null 2>&1 || :
%endif

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%defattr(-,root,root,-)
%doc doc/* examples/
%doc CHANGELOG LICENSE README ROADMAP VERSION
%dir %{haproxy_confdir}
%dir %{haproxy_datadir}
%{haproxy_datadir}/*
%config(noreplace) %{haproxy_confdir}/%{pkg_name}.cfg
%config(noreplace) %{_root_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_root_sysconfdir}/sysconfig/%{name}
%{_unitdir}/%{name}.service
%{_sbindir}/%{pkg_name}
%{_bindir}/halog
%{_bindir}/iprange
%{_mandir}/man1/*
%attr(-,%{haproxy_user},%{haproxy_group}) %dir %{haproxy_home}
%if 0%{?scl:1}
%attr(-,%{haproxy_user},%{haproxy_group}) %dir %{_localstatedir}/lib/%{pkg_name}
%endif

%if 0%{?scl:1}
%scl_syspaths_files -n %{pkg_name}
%endif

%changelog
* Thu Nov 28 2019 Julien Pivotto <roidelapluie@inuits.eu> - 2.1.0-7
- Use static LUA in epel7

* Wed Nov 27 2019 Julien Pivotto <roidelapluie@inuits.eu> - 2.1.0-6
- Use static LUA in epel7

* Wed Nov 27 2019 Julien Pivotto <roidelapluie@inuits.eu> - 2.1.0-5
- Use static LUA in epel7

* Wed Nov 27 2019 Julien Pivotto <roidelapluie@inuits.eu> - 2.1.0-4
- Cherry pick: h1: Don't test the host header during response parsing

* Tue Nov 26 2019 Julien Pivotto <roidelapluie@inuits.eu> - 2.1.0-3
- Enable LUA for el8 only

* Tue Nov 26 2019 Julien Pivotto <roidelapluie@inuits.eu> - 2.1.0-2
- Enable LUA

* Tue Nov 26 2019 Julien Pivotto <roidelapluie@inuits.eu> - 2.1.0-1
- Bump to 2.1.0

* Tue Nov 26 2019 Julien Pivotto <roidelapluie@inuits.eu> - 2.0.10-2
- Enable Prometheus

* Tue Nov 26 2019 Julien Pivotto <roidelapluie@inuits.eu> - 2.0.10-1
- Update to 2.0.10

* Wed Jan 09 2019 Ryan O'Hara <rohara@redhat.com> - 1.8.17-1
- Update to 1.8.17 (#1660514)
- Resolve CVE-2018-20615 (#1663084)

* Tue Dec 18 2018 Ryan O'Hara <rohara@redhat.com> - 1.8.15-1
- Update to 1.8.15 (#1660514)
- Build with new OpenSLL for ALPN support (#1595865)
- Fix seemless reloads for send-proxy/accept-proxy (#1649041)
- Resolve CVE-2018-11469 (#1584788)
- Resolve CVE-2018-20102 (#1659017)
- Resolve CVE-2018-20103 (#1659018)

* Wed Sep 19 2018 Ryan O'Hara <rohara@redhat.com> - 1.8.4-3
- Fix improper sign check on the header index value (#1630503)

* Tue May 01 2018 Ryan O'Hara <rohara@redhat.com> - 1.8.4-2
- Fix incorrect HTTP/2 frame length check (#1569808)

* Thu Nov 30 2017 Ryan O'Hara <rohara@redhat.com> - 1.8.4-1
- Initial packaging (#1536138)
