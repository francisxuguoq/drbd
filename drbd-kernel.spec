Name: drbd-kernel
Summary: Kernel driver for DRBD
Version: 9.0.0
Release: 1%{?dist}

# always require a suitable userland
Requires: drbd-utils >= 8.9.3

Source: http://oss.linbit.com/drbd/drbd-%{version}.tar.gz
License: GPLv2+
Group: System Environment/Kernel
URL: http://www.drbd.org/
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
%if ! %{defined suse_version}
BuildRequires: redhat-rpm-config
%endif
%if %{defined kernel_module_package_buildreqs}
BuildRequires: %kernel_module_package_buildreqs
%endif

%description
This module is the kernel-dependent driver for DRBD.  This is split out so
that multiple kernel driver versions can be installed, one for each
installed kernel.

%prep
%setup -q -n drbd-%{version}

%if %{defined suse_kernel_module_package}
# Support also sles10, where kernel_module_package was not yet defined.
# In sles11, suse_k_m_p became a wrapper around k_m_p.

%if 0%{?suse_version} < 1110
# We need to exclude some flavours on sles10 etc,
# or we hit an rpm internal buffer limit.
%suse_kernel_module_package -n drbd -f filelist-suse kdump kdumppae vmi vmipae um
%else
%suse_kernel_module_package -n drbd -f filelist-suse
%endif
%else
# Concept stolen from sles kernel-module-subpackage:
# include the kernel version in the package version,
# so we can have more than one kmod-drbd.
# Needed, because even though kABI is still "compatible" in RHEL 6.0 to 6.1,
# the actual functionality differs very much: 6.1 does no longer do BARRIERS,
# but wants FLUSH/FUA instead.
# For convenience, we want both 6.0 and 6.1 in the same repository,
# and have yum/rpm figure out via dependencies, which kmod version should be installed.
# This is a dirty hack, non generic, and should probably be enclosed in some "if-on-rhel6".
%define _this_kmp_version %{version}_%(echo %kernel_version | sed -r 'y/-/_/; s/\.el.\.(x86_64|i.86)$//;')
%kernel_module_package -v %_this_kmp_version -n drbd -f filelist-redhat
%endif

%build
rm -rf obj
mkdir obj
ln -s ../drbd-headers obj/

for flavor in %flavors_to_build; do
    cp -r drbd obj/$flavor
    #make -C %{kernel_source $flavor} M=$PWD/obj/$flavor
    make -C obj/$flavor %{_smp_mflags} all KDIR=%{kernel_source $flavor}
done

%install
export INSTALL_MOD_PATH=$RPM_BUILD_ROOT

%if %{defined kernel_module_package_moddir}
export INSTALL_MOD_DIR=%{kernel_module_package_moddir drbd}
%else
%if %{defined suse_kernel_module_package}
export INSTALL_MOD_DIR=updates
%else
export INSTALL_MOD_DIR=extra/drbd
%endif
%endif

# Very likely kernel_module_package_moddir did ignore the parameter,
# so we just append it here. The weak-modules magic expects that location.
[ $INSTALL_MOD_DIR = extra ] && INSTALL_MOD_DIR=extra/drbd

for flavor in %flavors_to_build ; do
    make -C %{kernel_source $flavor} modules_install \
	M=$PWD/obj/$flavor
    kernelrelease=$(cat %{kernel_source $flavor}/include/config/kernel.release || make -s -C %{kernel_source $flavor} kernelrelease)
    mv obj/$flavor/.kernel.config.gz obj/k-config-$kernelrelease.gz
    cp obj/$flavor/Module.symvers ../../RPMS/Module-$flavor.symvers
done

%if %{defined suse_kernel_module_package}
# On SUSE, putting the modules into the default path determined by
# %kernel_module_package_moddir is enough to give them priority over
# shipped modules.
rm -f drbd.conf
%else
mkdir -p $RPM_BUILD_ROOT/etc/depmod.d
echo "override drbd * weak-updates" \
    > $RPM_BUILD_ROOT/etc/depmod.d/drbd.conf
%endif

%clean
rm -rf %{buildroot}

%changelog
* Tue Jun 16 2015 Philipp Reisner <phil@linbit.com> - 9.0.0-1
- New upstream release.

* Mon Jul 18 2011 Philipp Reisner <phil@linbit.com> - 8.4.0-1
- New upstream release.

* Fri Jan 28 2011 Philipp Reisner <phil@linbit.com> - 8.3.10-1
- New upstream release.

* Thu Nov 25 2010 Andreas Gruenbacher <agruen@linbit.com> - 8.3.9-1
- Convert to a Kernel Module Package.
