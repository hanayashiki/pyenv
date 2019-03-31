import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="py-env",
    version="0.0.1",
    author="Chenyu Wang",
    author_email="wangchenyu2017@gmail.com",
    description="Provides persistent environment for Python 3 scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hanayashiki/pyenv",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux ",
    ],
)