%global service		multifactor
%global maindir		/opt/multifactor
%global workdir		%{maindir}/ldap
%global mfauser		mfa
%global	debug_package	%{nil}
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-.*[[:space:]].*$!!g')

Name:		%{service}-ldap
Version:	%{hk_version}
Release:	%{hk_build}%{?dist}
Summary:	Multifactor LDAP-adapter server

Group:		Applications/System
License:	Proprietary
URL:		https://multifactor.ru
Source0:	%{name}.tar.gz

AutoReq:		no
AutoProv:		no
Requires:		aspnetcore-runtime-3.1 >= 3.1.23
BuildArch:		x86_64

%description
LDAP 2FA proxy for multifactor.ru server

%prep
curl -sL 'https://github.com/MultifactorLab/multifactor-ldap-adapter/releases/download/%{version}/release_linux_x64.zip' -o %{_sourcedir}/%{name}.zip
if [[ -d %{_builddir}/%{name} ]];then
	rm -rf %{_builddir}/%{name}
fi
mkdir %{_builddir}/%{name}
unzip %{_sourcedir}/%{name}.zip -d %{_builddir}/%{name}
cd %{_builddir}/%{name}
chmod 600 -R ./*
mkdir logs tls
chmod 700 logs tls
cat << EOF >> %{name}.service
[Unit]
Description=Multifactor Ldap Adapter

[Service]
WorkingDirectory=%{workdir}
ExecStart=/usr/bin/env dotnet %{workdir}/multifactor-ldap-adapter.dll
Restart=always
RestartSec=10
KillSignal=SIGINT
SyslogIdentifier=%{name}
User=%{mfauser}
Environment=ASPNETCORE_ENVIRONMENT=Production
Environment=DOTNET_PRINT_TELEMETRY_MESSAGE=false
TimeoutStopSec=30
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

%install
cd %{_builddir}/%{name}
install -dm750                                      %{buildroot}%{_sysconfdir}/%{service}
install -m650 multifactor-ldap-adapter.dll.config   %{buildroot}%{_sysconfdir}/%{service}/%{name}.conf
install -Dm644 %{name}.service                      %{buildroot}%{_prefix}/lib/systemd/system/%{name}.service
install -dm750                                      %{buildroot}/var/lib/%{name}
install -dm700                                      %{buildroot}%{workdir}
rm multifactor-ldap-adapter.dll.config %{name}.service
cp -rv ./* %{buildroot}%{workdir}/ 

%files
%config(noreplace) %{_sysconfdir}/%{service}/%{name}.conf
%config %{_prefix}/lib/systemd/system/%{name}.service
%{workdir}

%post
if [ $1 == 1 ];then
  if ! $(getent passwd %{mfauser} > /dev/null); then
        useradd -r -s /bin/false -m -d %{workdir} %{mfauser}
  fi
  ln -sf %{_sysconfdir}/%{service}/%{name}.conf %{workdir}/multifactor-ldap-adapter.dll.config
  chown -R %{mfauser} %{_sysconfdir}/%{service}
  chown -R %{mfauser}:%{mfauser} %{workdir}
  systemctl daemon-reload
elif [ $1 == 2 ];then
  ln -sf %{_sysconfdir}/%{service}/%{name}.conf %{workdir}/multifactor-ldap-adapter.dll.config
  chown -R %{mfauser}:%{mfauser} %{workdir}
  chown -R %{mfauser} %{_sysconfdir}/%{service}
  systemctl daemon-reload
  if $(systemctl is-active --quiet %{name}.service);then
    systemctl restart %{name}.service
  fi
fi

%preun
if [ $1 == 0 ];then
  if $(systemctl is-active --quiet %{name}.service);then
    systemctl daemon-reload
    systemctl stop %{name}.service
  fi
fi

%postun
if [ $1 == 0 ];then
  rm -rf %{workdir}
  rmdir --ignore-fail-on-non-empty %{maindir}
  userdel %{mfauser}
fi

%changelog
