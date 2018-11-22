from distutils.core import setup
setup(
  name = 'finviz',
  packages = ['finviz'],
  version = '1.1',
  license='MIT',
  description = 'Unofficial API for finviz.com',
  author = 'Mario Stoev',
  author_email = 'bg.mstoev@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/mariostoev/finviz',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',    # I explain this later on
  keywords = ['finviz', 'api', 'screener', 'finviz api', 'charts', 'scraper'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'lxml',
          'requests',
          'aiohttp',
          'urllib3'
      ],
  classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.6',
  ],
)