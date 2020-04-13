import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="musdl",
    version="1.1.0",
    author="Ong Yong Xin",
    author_email="ongyongxin.offical@gmail.com",
    description="Musescore downloader written in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/onyxware/musdl",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    py_modules=["musdl"],
    entry_points="""
        [console_scripts]
        musdl=musdl:main
    """,
    python_requires='>=3.5',
)
