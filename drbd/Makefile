# makefile for drbd for linux 2.4 // 2.6
#
# By Lars Ellenberg.
#
# drbd is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# drbd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with drbd; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#

# usage: make [ KDIR=/path/to/kernel/source ]
#
# this file is read twice:
# the first invocation calls out to the toplevel Makefile in the
# kernel source tree, which then in turn will call this file again
# as subdir Makefile, with all appropriate vars and macros set.
#
# note: if you get strange make errors when ARCH=um, you
# probably need to "make mrproper" in the KDIR first...

# The destination "root" directory. Meant to be overridden by
# packaging scripts.
DESTDIR ?= /

# Do not:
# o  use make's built-in rules and variables
#    (this increases performance and avoids hard-to-debug behaviour);
# o  print "Entering directory ...";
MAKEFLAGS += -rR --no-print-directory

# since 2.6.16, KERNELRELEASE may be empty,
# e.g. when building against some (broken?) linux-header package.
# Lets test on PATCHLEVEL, that won't change too soon...

ifneq ($(PATCHLEVEL),)
 # suffifiently new kernel will include Kbuild directly
 ifneq ($(VERSION),3)
  ifneq ($(VERSION),2)
    $(error "won't compile with this kernel version")
  endif
  ifneq ($(PATCHLEVEL),6)
    $(error "won't compile with this kernel version")
  endif
 endif

  CONFIG_BLK_DEV_DRBD := m

  include $(src)/Kbuild

else
  # called from command line in current directory

  # for some reason some of the commands below only work correctly in bash,
  # and not in e.g. dash. I'm too lazy to fix it to be compatible.
  SHELL=/bin/bash

  DRBDSRC := $(shell pwd)

  # to be overridden on command line:
  PREFIX := /
  ifneq ($(wildcard ../build-for-uml),)
    #### for Philipp's convenience :)
    ARCH_UM := "ARCH=um"
    KDIR := /usr/src/linux-um
  else
    ifeq ($(wildcard /lib/modules/$(shell uname -r)/source),)
      KDIR := /lib/modules/$(shell uname -r)/build
    else
      KDIR := /lib/modules/$(shell uname -r)/source
      ifneq ("$(origin KDIR)", "command line")
        ifneq ($(wildcard /lib/modules/$(shell uname -r)/build),)
          O := /lib/modules/$(shell uname -r)/build
        endif
      endif
    endif
  endif

  .PHONY: drbd.o default all greeting clean kbuild install dep tags unpatch compat

  drbd.o: greeting kbuild
  default: drbd.o
  all:     drbd.o

  greeting:
	@echo "" ;\
	echo "    Calling toplevel makefile of kernel source tree, which I believe is in" ;\
	echo "    KDIR=$(KDIR)" ; \
	echo "";
	@if ! test -e $(KDIR)/Makefile ; then \
		echo -e "    SORRY, kernel makefile not found. You need to tell me a correct KDIR!\n" ;\
		false;\
	fi

  unpatch:
	@if test -e .compat_patches_applied; then \
	    echo "Removing compat patches"; \
	    patch -R -p0 --batch < .compat_patches_applied; \
	    rm -f .compat_patches_applied; \
	fi

  # compat.h is built by Kbuild; I think the most easy way to trigger that
  # without trying to re-implement all the Kbuild magic badly, is to simply
  # tell it to compile our smallest, least complex .c file which still
  # has a dependency on our compat.h
  .PHONY: compat.h
  compat.h:
	@touch dummy-for-compat-h.c
	$(MAKE) -C $(KDIR)  $(if $(O),O=$(O),) M=$(DRBDSRC) $(ARCH_UM) dummy-for-compat-h.o

  kbuild:
	@rm -f .drbd_kernelrelease*
	$(MAKE) -C $(KDIR)  $(if $(O),O=$(O),) M=$(DRBDSRC) $(ARCH_UM) modules
	-mv .drbd_kernelrelease.new .drbd_kernelrelease
	@echo -n "Memorizing module configuration ... "
	@config=$$( (for x in $(KDIR)/.config $(O)/.config ; do \
	       if test -e $$x ; then echo $$x ; exit 0; fi ; \
	       done; echo $(KDIR)/.config) | sed -e 's,//,/,g') ; \
	{ echo -e "#\n# drbd.o was compiled with"          ; \
	  echo "#  `gcc -v 2>&1 | tail -1`"                 ; \
	  echo "# against this kernelrelease:"              ; \
	  sed 's/^/#  /' .drbd_kernelrelease                ; \
	  echo    "# kernel .config from"                   ; \
	  echo -n "#  $$config"                      ; \
	  test -L "$${config%/.config}" && echo "	alias"   &&           \
	  echo "#  $$(readlink $${config%/.config})/.config" || echo "" ; \
	  echo -e "# follows\n#\n"                          ; \
	  cat $$config ; } | gzip > .kernel.config.gz
	@echo "done."

  clean: unpatch
	rm -rf .tmp_versions Module.markers Module.symvers modules.order
	rm -f *.[oas] *.ko .*.cmd .*.d .*.tmp *.mod.c .*.flags .depend .kernel*
	rm -f dummy-for-compat-h.c
	rm -f drbd-kernel-compat/*.[oas] drbd-kernel-compat/.*.cmd
	rm -f drbd-kernel-compat/compat.patch drbd-kernel-compat/.compat.cocci
	rm -rf .compat_test.* .cache.mk

  distclean: clean
	@if git show HEAD:drbd/linux/drbd_config.h > linux/drbd_config.h.tmp \
	&& ! diff -s -U0 linux/drbd_config.h.tmp linux/drbd_config.h ; then \
		mv linux/drbd_config.h.tmp linux/drbd_config.h ; \
	else \
		rm -f linux/drbd_config.h.tmp ; \
	fi
	rm -f drbd_buildtag.c .config*.timestamp compat*.h

  tags:
	( git ls-files ;						\
	  git submodule foreach -q --recursive				\
		'git ls-files | sed -e "s,^,$$displaypath/,"' ) |	\
		ctags -L -						\
		-I __initdata,__exitdata,__acquires,__releases		\
		-I __must_hold,__protected_by,__protected_read_by	\
		-I __protected_write_by,BIO_ENDIO_ARGS

  compat_headers := $(wildcard drbd-kernel-compat/cocci_cache/*/compat.h)
  compat_patches := $(patsubst %.h,%.patch,$(compat_headers))

  sources := $(filter-out drbd_strings.c drbd_buildtag.c,$(wildcard *.c))
  sources += $(wildcard drbd-headers/linux/*.h)

  $(compat_patches): $(sources)
	$(eval incdir := $(subst /compat.patch,,$@))
	$(eval chksum := $(subst drbd-kernel-compat/cocci_cache/,,$(incdir)))
	@if test -e .compat_patches_applied; then \
	    echo "Removing compat patches"; \
	    patch -R -p0 --batch < .compat_patches_applied; \
	    rm -f .compat_patches_applied; \
	fi
	@K=$$(cat $(incdir)/kernelrelease.txt); echo "  GENPATCHNAMES   $$K"
	@gcc -I $(incdir) -o $(incdir)/gen_patch_names -std=c99 drbd-kernel-compat/gen_patch_names.c
	@$(incdir)/gen_patch_names > $(incdir)/applied_cocci_files.txt
	@rm $(incdir)/gen_patch_names
	@rm -f $(incdir)/.compat.cocci
	@rm -f $(incdir)/.compat.patch
	@for F in $$(cat $(incdir)/applied_cocci_files.txt); do \
	    if [ -e drbd-kernel-compat/cocci/$$F.cocci ] ; then				\
		cat drbd-kernel-compat/cocci/$$F.cocci >> $(incdir)/.compat.cocci; \
	    else							\
		cat drbd-kernel-compat/patches/$$F.patch >> $(incdir)/.compat.patch; \
	    fi; \
	    sed -e "s:@""COMPAT_PATCH_NAME@:$$F:g" \
		drbd-kernel-compat/cocci/debugfs_compat_template.cocci.in \
		>> $(incdir)/.compat.cocci; \
	done
	@if hash spatch; then \
	    echo "  SPATCH   $(chksum)"; \
	else \
	    echo "  ERROR: spatch not found in \$$PATH. Install package 'coccinelle'!"; \
	fi
	@spatch --sp-file $(incdir)/.compat.cocci \
	    $(sources) \
	    --macro-file drbd-kernel-compat/cocci_macros.h > $@.tmp 2> $(incdir)/.spatch.stderr
	@if [ -e $(incdir)/.compat.patch ]; then \
		cat $(incdir)/.compat.patch >> $@.tmp; \
	fi
	@mv $@.tmp $@
	@rm -f $(incdir)/.compat.cocci
	@rm -f $(incdir)/.compat.patch

  compat: $(compat_patches)

  ifneq ($(wildcard .drbd_kernelrelease),)
    # for VERSION, PATCHLEVEL, SUBLEVEL, EXTRAVERSION, KERNELRELEASE
    include .drbd_kernelrelease
    MODOBJS := drbd.ko drbd_transport_tcp.ko
    MODSUBDIR := updates
    LINUX := $(wildcard /lib/modules/$(KERNELRELEASE)/build)

    install:
	@if ! [ -e $(MODOBJ) ] ; then \
	  echo "No $(MODOBJ): nothing to install??"; false ; \
	fi
	install -d $(DESTDIR)/lib/modules/$(KERNELRELEASE)/$(MODSUBDIR)
	set -e ; for ko in $(MODOBJS); do \
		install -m 644 $$ko $(DESTDIR)/lib/modules/$(KERNELRELEASE)/$(MODSUBDIR); \
	done
    ifeq ($(DESTDIR),/)
      ifeq ($(shell uname -r),$(KERNELRELEASE))
		/sbin/depmod -a || :
      else
		@echo "Don't forget to depmod."
      endif
    endif
  else
    install:
	@echo "No .drbd_kernelrelease found. Do you need to 'make' the module first?"
	@false
  endif
endif

uninstall:

spell:
	for f in $(wildcard *.c); do \
	 	aspell --save-repl --dont-backup --personal=./../documentation/aspell.en.per check $$f; \
	done

