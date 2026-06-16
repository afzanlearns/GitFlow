from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gitflow',
    version='1.0.0',
    description='Git commit analytics and tracking tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='GitFlow',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.10',
    install_requires=[
        'GitPython>=3.1.40',
        'click>=8.1.7',
        'rich>=13.7.0',
        'sqlalchemy>=2.0.25',
        'apscheduler>=3.10.4',
        'python-dotenv>=1.0.0',
        'pandas>=2.1.0',
        'numpy>=1.26.0',
    ],
    extras_require={
        'dashboard': [
            'fastapi>=0.109.0',
            'uvicorn>=0.27.0',
            'websockets>=12.0',
        ],
        'notifications': [
            'plyer>=2.1.0',
            'requests>=2.31.0',
        ],
        'all': [
            'fastapi>=0.109.0',
            'uvicorn>=0.27.0',
            'websockets>=12.0',
            'plyer>=2.1.0',
            'requests>=2.31.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'gitflow=gitflow.cli.main:cli',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
