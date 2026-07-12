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

# ---------------------------------------------------------------------------
# Meta package: installs the Tkinter GUI by default; Qt GUI is opt-in
# ---------------------------------------------------------------------------
%package gui
Summary: Graphical interface for QUADS Client (installs Tkinter GUI by default)
Requires: %{name}-gui-tk = %{version}-%{release}

%description gui
Meta package that pulls in the Tkinter GUI for QUADS Client by default.
Installing this package gives you quads-client-gui-tk and the desktop
launcher entry.

To also install or switch to the Qt GUI, install quads-client-gui-qt in
addition to or instead of this package. Use
  update-alternatives --config quads-client-gui
to choose which GUI /usr/bin/quads-client-gui points to.

# ---------------------------------------------------------------------------
# Tkinter GUI subpackage
# ---------------------------------------------------------------------------
%package gui-tk
Summary: Tkinter GUI for QUADS Client
Requires: %{name} = %{version}-%{release}
Requires: python3-tkinter >= 3.13
Provides: quads-client-gui

%description gui-tk
Graphical user interface for QUADS Client using tkinter/ttk.
Provides an intuitive GUI for managing QUADS servers, scheduling
hosts, and monitoring assignments. Requires X11/Wayland display.

This package installs the quads-client-gui-tk binary. The generic
quads-client-gui command is managed via update-alternatives; install
quads-client-gui-qt alongside this package if you want to switch
between toolkits.

# ---------------------------------------------------------------------------
# Qt (PySide6) GUI subpackage
# ---------------------------------------------------------------------------
%package gui-qt
Summary: Qt (PySide6) GUI for QUADS Client
Requires: %{name} = %{version}-%{release}
Requires: python3-pyside6
Provides: quads-client-gui

%description gui-qt
Graphical user interface for QUADS Client using PySide6 (Qt6).
Provides an intuitive GUI for managing QUADS servers, scheduling
hosts, and monitoring assignments. Requires X11/Wayland display.

Uses the Qt Fusion style for a consistent cross-platform look on
both Linux (Fedora/RHEL) and macOS. Supports dark and light themes.

This package installs the quads-client-gui-qt binary. The generic
quads-client-gui command is managed via update-alternatives; it can
coexist with quads-client-gui-tk.

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

# ---------------------------------------------------------------------------
# File lists
# ---------------------------------------------------------------------------
%files
%doc README.md
%license LICENSE
%{_bindir}/quads-client
%{python3_sitelib}/quads_client/
%exclude %{python3_sitelib}/quads_client/qt6/
%{python3_sitelib}/quads_client-*.egg-info/
%{_datadir}/doc/quads-client/

%files gui
%{_datadir}/applications/quads-client-gui.desktop
%{_datadir}/icons/hicolor/128x128/apps/quads-client.png

%files gui-tk
%{_bindir}/quads-client-gui-tk

%files gui-qt
%{_bindir}/quads-client-gui-qt
%{python3_sitelib}/quads_client/qt6/

# ---------------------------------------------------------------------------
# Base package scriptlets
# ---------------------------------------------------------------------------
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

%preun
:;

%postun
find %{python3_sitelib}/quads_client 2>/dev/null | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf 2>/dev/null || true
:;

# ---------------------------------------------------------------------------
# Meta GUI package scriptlets (owns desktop/icon files)
# ---------------------------------------------------------------------------
%post gui
if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database %{_datadir}/applications &> /dev/null || :
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :
fi
:;

%postun gui
if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database %{_datadir}/applications &> /dev/null || :
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :
fi
:;

# ---------------------------------------------------------------------------
# Tkinter GUI scriptlets
# ---------------------------------------------------------------------------
%post gui-tk
update-alternatives --install %{_bindir}/quads-client-gui quads-client-gui \
    %{_bindir}/quads-client-gui-tk 30
update-alternatives --set quads-client-gui %{_bindir}/quads-client-gui-tk
if [ "$1" -eq 1 ]; then
echo "======================================================="
echo " QUADS Client GUI (Tk) installed successfully          "
echo "======================================================="
echo " Launch with: quads-client-gui  (or quads-client-gui-tk)"
echo " Or find it in your Applications menu                  "
echo " Switch GUI: update-alternatives --config quads-client-gui"
echo "======================================================="
fi
:;

%preun gui-tk
if [ "$1" -eq 0 ]; then
    update-alternatives --remove quads-client-gui %{_bindir}/quads-client-gui-tk
fi
:;

# ---------------------------------------------------------------------------
# Qt GUI scriptlets
# ---------------------------------------------------------------------------
%post gui-qt
update-alternatives --install %{_bindir}/quads-client-gui quads-client-gui \
    %{_bindir}/quads-client-gui-qt 30
update-alternatives --set quads-client-gui %{_bindir}/quads-client-gui-qt
if [ "$1" -eq 1 ]; then
echo "======================================================="
echo " QUADS Client GUI (Qt) installed successfully          "
echo "======================================================="
echo " Launch with: quads-client-gui  (or quads-client-gui-qt)"
echo " Or find it in your Applications menu                  "
echo " Switch GUI: update-alternatives --config quads-client-gui"
echo "======================================================="
fi
:;

%preun gui-qt
if [ "$1" -eq 0 ]; then
    update-alternatives --remove quads-client-gui %{_bindir}/quads-client-gui-qt
fi
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
