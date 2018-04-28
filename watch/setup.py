
from distutils.core import setup

setup(name="watch",
      version="1.0",
      maintainer="Skip Montanaro",
      maintainer_email="skip@pobox.com",
      description="Typing Watcher",
      url="http://sourceforge.net/projects/watch",
      py_modules=['collector'],
      scripts=['watch.py', 'watch-server.py'],
      )
