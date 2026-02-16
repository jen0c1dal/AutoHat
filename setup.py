from setuptools import setup
from pathlib import Path

README = Path(__file__).parent / "README.md"
long_description = README.read_text(encoding='utf-8') if README.exists() else ''

setup(
    name='autohat',
    version='1.0.0',
    description='Ultimate Frisbee check-in and team generator',
    long_description=long_description,
    py_modules=['GUI', 'main', 'hatFunctions'],
    install_requires=[
        'pandas>=1.1',
        'numpy>=1.19',
        'XlsxWriter>=3.0'
    ],
    python_requires='>=3.8',
)
