from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fig-editor",
    version="1.0.4",
    author="Qichen Liu",
    author_email="",
    description="A simple and usable GIF editor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Q1CHENL/fig",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Multimedia :: Graphics :: Editors",
    ],
    python_requires=">=3.6",
    install_requires=[
        "PyGObject>=3.42.0",  # For GTK4 support
        "Pillow>=8.0.0",      # For GIF processing
    ],
    package_data={
        'fig': ['style/*.css'],  # Include CSS files
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'fig=fig.fig:main',
        ],
    },
) 