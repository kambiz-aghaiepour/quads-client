#### NOTE: if building locally you may need to do the following:
####
#### yum install rpmdevtools -y
#### spectool -g -R rpm/quads-client.spec
####
#### At this point you can use rpmbuild -ba quads-client.spec
#### this is because our Source0 is a remote Github location
####
#### Our upstream repository is located here:
#### https://copr.fedorainfracloud.org/coprs/quadsdev/quads-client
####

%define name quads-client
%define reponame quads-client
%define branch main
%define version 0.8.7
%define build_timestamp %{lua: print(os.date("%Y%m%d"))}

Summary: QUADS Client TUI Shell for managing multiple QUADS server instances
Name: %{name}
Version: %{version}
Release: %{build_timestamp}
Source0: https://github.com/sadsfae/quads-client/archive/%{branch}.tar.gz#/%{name}-%{version}-%{release}.tar.gz
License: GPLv3
BuildRoot: %{_tmppath}/%{name}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: QUADS Project
Packager: QUADS Project
BuildRequires: python3-devel >= 3.13
BuildRequires: python3-setuptools
BuildRequires: desktop-file-utils
Requires: python3 >= 3.13
Requires: python3-cmd2 >= 2.0.0
Requires: quads-lib >= 0.1.9
Requires: python3-tabulate >= 0.9.0
Requires: python3-argcomplete >= 3.1.2
Requires: python3-PyYAML >= 6.0.0
Requires: python3-jwt >= 2.8.0
Requires: python3-rich >= 13.0.0
Requires: python3-requests >= 2.31.0
Requires: python3-urllib3 >= 2.0.0
Requires: bash-completion

AutoReq: no

Url: https://quads.dev

%description

QUADS Client is an interactive TUI (Text User Interface) shell for managing
multiple QUADS (QUADS Automated Deployment System) server instances.

Features include:
 * Multi-server connection management with bearer token authentication
 * Interactive cmd2-based shell with command history and tab completion
 * Self-scheduling mode (SSM) for non-admin users
 * Cloud management commands (list, create, delete)
 * Real-time provisioning progress tracking
 * SQLite-based persistent command history
 * Thin wrapper design with server-side authorization

QUADS Client requires Python 3.13 or later and communicates with QUADS
servers via the python-quads-lib API wrapper.

%prep
%autosetup -n %{reponame}-%{branch}

%build
%py3_build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_datadir}/doc/quads-client
%py3_install

# Install example configuration
install -m 0644 conf/quads-client.yml.example %{buildroot}%{_datadir}/doc/quads-client/

# Install GUI desktop file
desktop-file-install --dir=%{buildroot}%{_datadir}/applications desktop/quads-client-gui.desktop

# Install GUI icon
install -Dm 0644 desktop/icons/quads-client.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/quads-client.png

%clean
rm -rf %{buildroot}

%package gui-tk
Summary: Tkinter GUI for QUADS Client
Requires: %{name} = %{version}-%{release}
Requires: python3-tkinter >= 3.13
Provides: quads-client-gui
Conflicts: quads-client-gui-qt6

%description gui-tk
Graphical user interface for QUADS Client using tkinter/ttk.
Provides an intuitive GUI for managing QUADS servers, scheduling
hosts, and monitoring assignments. Requires X11/Wayland display.

This package installs the quads-client-gui-tk binary and a
quads-client-gui symlink pointing to it.

%package gui-qt6
Summary: Qt6 (PySide6) GUI for QUADS Client
Requires: %{name} = %{version}-%{release}
Requires: python3-pyside6
Provides: quads-client-gui
Conflicts: quads-client-gui-tk

%description gui-qt6
Graphical user interface for QUADS Client using PySide6 (Qt6).
Provides an intuitive GUI for managing QUADS servers, scheduling
hosts, and monitoring assignments. Requires X11/Wayland display.

Uses the Qt Fusion style for a consistent cross-platform look on
both Linux (Fedora/RHEL) and macOS. Supports dark and light themes.

This package installs the quads-client-gui-qt6 binary and a
quads-client-gui symlink pointing to it.

%files
%doc README.md
%license LICENSE
%{_bindir}/quads-client
%{python3_sitelib}/quads_client/
%exclude %{python3_sitelib}/quads_client/qt6/
%{python3_sitelib}/quads_client-*.egg-info/
%{_datadir}/doc/quads-client/

%files gui-tk
%{_bindir}/quads-client-gui-tk
%{_datadir}/applications/quads-client-gui.desktop
%{_datadir}/icons/hicolor/128x128/apps/quads-client.png

%files gui-qt6
%{_bindir}/quads-client-gui-qt6
%{python3_sitelib}/quads_client/qt6/
%{_datadir}/applications/quads-client-gui.desktop
%{_datadir}/icons/hicolor/128x128/apps/quads-client.png

%post
# Enable bash completion globally if available
if [ -x /usr/bin/activate-global-python-argcomplete3 ]; then
    /usr/bin/activate-global-python-argcomplete3 2>/dev/null || true
fi

# First time installation message
if [ "$1" -eq 1 ]; then
echo "======================================================="
echo " QUADS Client installed successfully                   "
echo "======================================================="
echo "                                                       "
echo " To get started:                                       "
echo " Use the interactive add-quads-server command:         "
echo "  quads-client                                         "
echo "  add-quads-server                                     "
echo "  (follow prompts)                                     "
echo "  connect <server_name>                                "
echo "  register your.email@example.com YourPassword123      "
echo "======================================================="
fi
:;

%post gui-tk
ln -sf %{_bindir}/quads-client-gui-tk %{_bindir}/quads-client-gui
if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database %{_datadir}/applications &> /dev/null || :
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :
fi
if [ "$1" -eq 1 ]; then
echo "======================================================="
echo " QUADS Client GUI (Tk) installed successfully          "
echo "======================================================="
echo " Launch with: quads-client-gui  (or quads-client-gui-tk)"
echo " Or find it in your Applications menu                  "
echo "======================================================="
fi
:;

%preun gui-tk
if [ "$1" -eq 0 ]; then
    rm -f %{_bindir}/quads-client-gui
fi
:;

%postun gui-tk
if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database %{_datadir}/applications &> /dev/null || :
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :
fi
:;

%post gui-qt6
ln -sf %{_bindir}/quads-client-gui-qt6 %{_bindir}/quads-client-gui
if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database %{_datadir}/applications &> /dev/null || :
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :
fi
if [ "$1" -eq 1 ]; then
echo "======================================================="
echo " QUADS Client GUI (Qt6) installed successfully         "
echo "======================================================="
echo " Launch with: quads-client-gui  (or quads-client-gui-qt6)"
echo " Or find it in your Applications menu                  "
echo "======================================================="
fi
:;

%preun gui-qt6
if [ "$1" -eq 0 ]; then
    rm -f %{_bindir}/quads-client-gui
fi
:;

%postun gui-qt6
if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database %{_datadir}/applications &> /dev/null || :
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :
fi
:;

%preun
:;

%postun
find %{python3_sitelib}/quads_client 2>/dev/null | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf 2>/dev/null || true
:;

%changelog

* Wed Apr 30 2026 Will Foster <wfoster@redhat.com>
- 1.0.0 initial release
- TUI shell with multi-server support
- Thin wrapper design with server-side authorization
- Self-scheduling mode (SSM) for non-admin users
- Real-time provisioning progress tracking
- SQLite-based persistent command history
- Python 3.13+ requirement
- Removed PyJWT dependency (server handles token validation)
- Black formatted code (line-length 119)
- Comprehensive test suite (44 tests, 61%% coverage)
- Cloud management commands (list, create, delete)
- Connection management (connect, disconnect, status)
- Bearer token authentication via python-quads-lib
