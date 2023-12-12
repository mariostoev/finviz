from distutils.core import setup

setup(
    name="finviz",
    packages=["finviz", "finviz.helper_functions"],
    version="1.4.6",
    license="MIT",
    description="Unofficial API for FinViz.com",
    author="Mario Stoev, James Bury",
    author_email="bg.mstoev@gmail.com, jabury@sympatico.ca",
    url="https://github.com/mariostoev/finviz",
    download_url="https://github.com/mariostoev/finviz/archive/v1.4.6.tar.gz",
    keywords=["finviz", "api", "screener", "finviz api", "charts", "scraper"],
    install_requires=[
        "lxml",
        "requests",
        "aiohttp",
        "urllib3",
        "cssselect",
        "user_agent",
        "beautifulsoup4",
        "tqdm",
        "tenacity",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
)
