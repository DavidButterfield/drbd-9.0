# "uname -r" output of the kernel to build for, the running one
# if none was specified with "--define 'kernelversion <uname -r>'"
# PLEASE: provide both (correctly) or none!!
%{!?kernelversion: %{expand: %%define kernelversion %(uname -r)}}
%{!?kdir: %{expand: %%define kdir /lib/modules/%(uname -r)/build}}

# encode - to _ to be able to include that in a package name or release "number"
%global krelver  %(echo %{kernelversion} | tr -s '-' '_')

Name: drbd-km
Summary: DRBD driver for Linux
Version: 8.4.5rc1
Release: 1
Source: http://oss.linbit.com/%{name}/8.4/drbd-%{version}.tar.gz
License: GPLv2+
ExclusiveOS: linux
Group: System Environment/Kernel
URL: http://www.drbd.org/
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildRequires: gcc, @RPM_BUILDREQ_KM@

%description
DRBD mirrors a block device over the network to another machine.
Think of it as networked raid 1. It is a building block for
setting up high availability (HA) clusters.

# I choose to have the kernelversion as part of the package name!
# drbd-km is prepended...
%package %{krelver}
Summary: Kernel driver for DRBD.
Group: System Environment/Kernel
Conflicts: @RPM_CONFLICTS_KM@
# always require a suitable userland and depmod.
Requires: drbd-utils = %{version}, /sbin/depmod
# to be able to override from build scripts which flavor of kernel we are building against.
Requires: %{expand: %(echo ${DRBD_KMOD_REQUIRES:-kernel})}
# TODO: break up this generic .spec file into per distribution ones,
# and use the distribution specific naming and build conventions for kernel modules.

%description %{krelver}
This module is the kernel-dependent driver for DRBD.  This is split out so
that multiple kernel driver versions can be installed, one for each
installed kernel.

%files %{krelver}
%defattr(-,root,root)
/lib/modules/%{kernelversion}/
%doc COPYING
%doc ChangeLog
%doc drbd/k-config-%{kernelversion}.gz

%prep
%setup -q -n drbd-%{version}
test -d %{kdir}/.
test "$(KDIR=%{kdir} scripts/get_uts_release.sh)" = %{kernelversion}

%build
%configure \
    --without-utils \
    --with-km \
    --without-udev \
    --without-xen \
    --without-pacemaker \
    --without-heartbeat \
    --without-rgmanager \
    --without-bashcompletion
echo kernelversion=%{kernelversion}
echo kversion=%{kversion}
echo krelver=%{krelver}
make %{_smp_mflags} module KDIR=%{kdir}


%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
cd drbd
mv .kernel.config.gz k-config-%{kernelversion}.gz

%clean
rm -rf %{buildroot}

%preun %{krelver}
lsmod | grep drbd > /dev/null 2>&1
if [ $? -eq 0 ]; then
    rmmod drbd
fi

%post %{krelver}
# hack for distribution kernel packages,
# which already contain some (probably outdated) drbd module
EXTRA_DRBD_KO=/lib/modules/%{kernelversion}/extra/drbd.ko
if test -e $EXTRA_DRBD_KO; then
    mv $EXTRA_DRBD_KO $EXTRA_DRBD_KO.orig
fi
uname -r | grep BOOT ||
/sbin/depmod -a -F /boot/System.map-%{kernelversion} %{kernelversion} >/dev/null 2>&1 || true

%postun %{krelver}
/sbin/depmod -a -F /boot/System.map-%{kernelversion} %{kernelversion} >/dev/null 2>&1 || true


%changelog
* Tue May  6 2014 Philipp Reisner <phil@linbit.com> - 8.4.5rc1-1
- New upstream release.

* Thu Feb 27 2014 Lars Ellenberg <lars@linbit.com> - 8.4.4-7
- fix potential BUG_ON in mempool_alloc for older kernels (<2.6.23)

* Tue Feb 11 2014 Lars Ellenberg <lars@linbit.com> - 8.4.4-6
- fix spurious detach/disconnect: don't announce WRITE_SAME
- fix NULL pointer deref in blk_add_request_payload
  (DISCARD/TRIM handling in sd)
- fix resync-finished detection
- fix drbd_ldev_destroy to run exactly once and in worker context
- Regression fixes
  - fix regression: potential NULL pointer dereference
  - fix regression: potential list corruption

* Thu Nov 14 2013 Lars Ellenberg <lars@linbit.com> - 8.4.4-4
- Regression fixes
  - fix for potential deadlock in adm functions (drbdsetup)
  - fix for init script and /sbin vs /usr/sbin

* Fri Oct 11 2013 Philipp Reisner <phil@linbit.com> - 8.4.4-1
- New upstream release.

* Tue Feb  5 2013 Philipp Reisner <phil@linbit.com> - 8.4.3-1
- New upstream release.

* Thu Sep  6 2012 Philipp Reisner <phil@linbit.com> - 8.4.2-1
- New upstream release.

* Tue Feb 21 2012 Lars Ellenberg <lars@linbit.com> - 8.4.1-2
- Build fix for RHEL 6 and ubuntu lucid

* Tue Dec 20 2011 Philipp Reisner <phil@linbit.com> - 8.4.1-1
- New upstream release.

* Mon Jul 18 2011 Philipp Reisner <phil@linbit.com> - 8.4.0-1
- New upstream release.

* Fri Jan 28 2011 Philipp Reisner <phil@linbit.com> - 8.3.10-1
- New upstream release.

* Fri Oct 22 2010 Philipp Reisner <phil@linbit.com> - 8.3.9-1
- New upstream release.

* Wed Jun  2 2010 Philipp Reisner <phil@linbit.com> - 8.3.8-1
- New upstream release.

* Wed Jan 13 2010 Philipp Reisner <phil@linbit.com> - 8.3.7-1
- New upstream release.

* Sun Nov  8 2009 Philipp Reisner <phil@linbit.com> - 8.3.6-1
- New upstream release.

* Tue Oct 27 2009 Philipp Reisner <phil@linbit.com> - 8.3.5-1
- New upstream release.

* Wed Oct 21 2009 Florian Haas <florian@linbit.com> - 8.3.4-12
- Packaging makeover.

* Tue Oct  6 2009 Philipp Reisner <phil@linbit.com> - 8.3.4-1
- New upstream release.

* Mon Oct  5 2009 Philipp Reisner <phil@linbit.com> - 8.3.3-1
- New upstream release.

* Fri Jul  3 2009 Philipp Reisner <phil@linbit.com> - 8.3.2-1
- New upstream release.

* Fri Mar 27 2009 Philipp Reisner <phil@linbit.com> - 8.3.1-1
- New upstream release.

* Thu Dec 18 2008 Philipp Reisner <phil@linbit.com> - 8.3.0-1
- New upstream release.

* Wed Nov 12 2008 Philipp Reisner <phil@linbit.com> - 8.2.7-1
- New upstream release.

* Fri May 30 2008 Philipp Reisner <phil@linbit.com> - 8.2.6-1
- New upstream release.

* Tue Feb 12 2008 Philipp Reisner <phil@linbit.com> - 8.2.5-1
- New upstream release.

* Fri Jan 11 2008 Philipp Reisner <phil@linbit.com> - 8.2.4-1
- New upstream release.

* Wed Jan  9 2008 Philipp Reisner <phil@linbit.com> - 8.2.3-1
- New upstream release.

* Fri Nov  2 2007 Philipp Reisner <phil@linbit.com> - 8.2.1-1
- New upstream release.

* Fri Sep 28 2007 Philipp Reisner <phil@linbit.com> - 8.2.0-1
- New upstream release.

* Mon Sep  3 2007 Philipp Reisner <phil@linbit.com> - 8.0.6-1
- New upstream release.

* Fri Aug  3 2007 Philipp Reisner <phil@linbit.com> - 8.0.5-1
- New upstream release.

* Wed Jun 27 2007 Philipp Reisner <phil@linbit.com> - 8.0.4-1
- New upstream release.

* Mon May 7 2007 Philipp Reisner <phil@linbit.com> - 8.0.3-1
- New upstream release.

* Fri Apr 6 2007 Philipp Reisner <phil@linbit.com> - 8.0.2-1
- New upstream release.

* Mon Mar  5 2007 Philipp Reisner <phil@linbit.com> - 8.0.1-1
- New upstream release.

* Wed Jan 24 2007 Philipp Reisner <phil@linbit.com>  - 8.0.0-1
- New upstream release.
