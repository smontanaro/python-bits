import os
_dir = dir

def dir(o=globals()):
    contents = _dir(o)
    if hasattr(o, "__file__"):
        dname = os.path.dirname(o.__file__)
        # look for not-yet-imported modules within packages
        if "/__init__.py" in o.__file__:
            try:
                stuff = os.listdir(dname)
            except OSError:
                # Searching eggs lands here.  Introspect.
                import zipfile
                d = os.path.dirname(dname)
                if not zipfile.is_zipfile(d):
                    return sorted(contents)
                base = os.path.basename(dname)
                stuff = [f[len(base)+1:]
                             for f in zipfile.ZipFile(d).namelist()
                                 if f.startswith(base)]
            for p in stuff:
                m = os.path.splitext(p)[0]
                if (
                    # not already known
                    m not in contents and 
                    # isn't a package file
                    p != "__init__.py" and
                    # is a python or ...
                    (p.endswith(".py") or
                     # c module or ...
                     p.endswith(".so") or
                     # a subpackage
                     (os.path.isdir(os.path.join(dname, p)) and
                      os.path.exists(os.path.join(dname, p, "__init__.py"))))):
                    if os.path.isdir(os.path.join(dname, p)):
                        # tack on trailing / to distinguish packages from
                        # modules
                        m += "/"
                    # [...] shows it hasn't been imported yet
                    contents.append("[%s]" % m)
    return sorted(contents)
