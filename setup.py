from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

_ = setup(
    name="userchrome-loader",
    version="1.0.0",
    packages=find_packages(),
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'userchrome-loader=src.main:main',
        ],
    },
    author="orbi-tal",
    description="A tool to load UserChrome scripts for Zen Browser",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/orbi-tal/userchrome-loader",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
