#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import errno
import fnmatch
import shutil
import subprocess
import tarfile
import sys, os

"""
Building RMP and DEB packages.
"""

def copy(src, dest, ignored = []):
    """Recursive copy for directories and files."""
    try:
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(*ignored))
    except OSError as e:
        # If the error was caused because the source wasn't a directory
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
        else:
            raise RuntimeError('Directory not copied. Error: %s' % e)

def rfind(pathname, pattern):
    """Recursive find filenames."""
    matches = []
    for root, dirnames, filenames in os.walk(pathname):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    return matches

def dist_deb():
    # TODO
    pass

def dist_rpm(package, version, revision):
    """Create a RPM package."""
    if os.path.exists('rpm'):
        shutil.rmtree('rpm')
    os.makedirs('rpm/RPMBUILD/BUILD')
    os.makedirs('rpm/RPMBUILD/RPMS')
    os.makedirs('rpm/RPMBUILD/SOURCES')
    os.makedirs('rpm/RPMBUILD/SPECS')
    os.makedirs('rpm/RPMBUILD/SRPMS')
    basename = '-'.join([package, version])
    rpm_dir = os.path.join('rpm', basename)
    rpm_build_dir = '-'.join([rpm_dir, 'build'])
    subprocess.check_output(['make', '-f', 'Makefile', 'install', 'prefix={rpm_build_dir}'.format(**locals())])
    os.makedirs(rpm_dir)
    copy('Makefile', rpm_dir)
    copy('tmEditor', rpm_dir+'/tmEditor', ignored=['*.pyc', '*.pyo', '.svn'])
    copy('resource', rpm_dir+'/resource', ignored=['.svn'])
    copy('scripts', rpm_dir+'/scripts', ignored=['.svn'])
    copy('copyright', rpm_dir)
    copy('changelog', rpm_dir)
    tarballname = 'rpm/RPMBUILD/SOURCES/{basename}.tar.gz'.format(**locals())
    if os.path.exists(tarballname):
        os.remove(tarballname)
    tar = tarfile.open(tarballname, "w:gz")
    tar.add(rpm_dir, basename)
    tar.close()
    pwd = os.getcwd()
    print pwd
    spec = [
        "%define _topdir   {pwd}/rpm/RPMBUILD",
        "%define name      {package}",
        "%define release   {revision}",
        "%define version   {version}",
        "%define buildroot %{{_topdir}}/%{{name}}-%{{version}}-root",
        "",
        "BuildRoot: %{{buildroot}}",
        "Summary:   Level-1 Global Trigger Menu Editor",
        "License:   proprietary",
        "Name:      %{{name}}",
        "Version:   %{{version}}",
        "Release:   %{{release}}",
        "Source:    %{{name}}-%{{version}}.tar.gz",
        "Prefix:    /usr",
        "Group:     Development/Tools",
        "Requires:  python >= 2.6",
        "Requires:  python-argparse",
        "Requires:  PyQt4 >= 4.6",
        "Requires:  glibc >= 2.4",
        "Requires:  libxerces-c-3_1 >= 3.1",
        "Requires:  gnome-icon-theme",
        "",
        "%description",
        "Trigger Menu Editor",
        " Graphical editor for editing Level-1 trigger menu XML files.",
        "",
        "%prep",
        "%setup -q",
        "",
        "%build",
        "make rootdir={pwd}/..",
        "",
        "%install",
        "make install rootdir={pwd}/.. prefix=$RPM_BUILD_ROOT/usr",
        "",
        "%files",
        "%defattr(-,root,root)",
    ]
    os.chdir('rpm')
    for filename in rfind('.', '*'):
        spec.append("/usr/{filename}".format(**locals()))
        # Generating *.pyc and *.pyo file lists.
        if filename.endswith('.py'):
            spec.append("/usr/{filename}c".format(**locals()))
            spec.append("/usr/{filename}o".format(**locals()))
    os.chdir(pwd)
    # Write spec file.
    filename = os.path.join('rpm', 'RPMBUILD', 'SPECS', '{package}.spec'.format(**locals()))
    open(filename, 'w').write("\n".join(spec).format(**locals()))
    # subprocess.check_call(['rpmbuild', '-v', '-bb', os.path.join('rpm', 'RPMBUILD', 'SPECS', '{package}.spec'.format(**locals()))])

def dist_lxplus(self, package, version, revision):
    distdir = "_lxplusdist"
    basename = "{package}-{version}-{revision}".format(**locals())
    if os.path.exists(distdir):
        shutil.rmtree(distdir)
    os.makedirs(distdir)
    os.makedirs(os.path.join(distdir, "bin"))
    os.makedirs(os.path.join(distdir, "lib"))
    copy('tmEditor', rpm_dir+'/tmEditor', ignored=['*.pyc', '*.pyo', '.svn'])
    tarballname = "{basename}.tar.gz".format(**locals())
    tar = tarfile.open(tarballname, "w:gz")
    tar.add("_lxplus_dist", basename)
    tar.close()

def read_version():
    proc = subprocess.Popen(['python', 'tmEditor/version.py', '--version'], stdout=subprocess.PIPE)
    return proc.stdout.read().strip()

def read_revision():
    proc = subprocess.Popen(['python', 'tmEditor/version.py', '-r'], stdout=subprocess.PIPE)
    return proc.stdout.read().strip() # !

if __name__ == '__main__':
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('type', choices = ['rpm', 'lxplus'])
    args = parser.parse_args()
    # Attributes
    version = read_version()
    revision = read_revision()
    package = 'tm-editor'
    if args.type == 'rpm':
        dist_rpm(package, version, revision)
    if args.type == 'lxplus':
        dist_lxplus(package, version, revison)
    sys.exit()
