from setuptools import setuptools

setuptools.setup(
    name="watch",
    version="1.1",
    maintainer="Skip Montanaro",
    maintainer_email="skip.montanaro@gmail.com",
    description="Typing Watcher",
    url="https://github.com/smontanaro/python-bits/watch",
    packages=['watch'],
    scripts=['src/watch.py', 'src/watch-server.py'],
)
