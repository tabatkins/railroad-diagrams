from setuptools import setup, find_packages

with open("README-py.md", "r") as fh:
    long_description = fh.read()
with open("semver.txt", "r") as fh:
    semver = fh.read().strip()

setup(
    name='railroad-diagrams',
    py_modules=['railroad'],
    version=semver,
    description='Generate SVG railroad syntax diagrams, like on JSON.org.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    author='Tab Atkins',
    author_email='jackalmage@gmail.com',
    url='https://github.com/tabatkins/railroad-diagrams',
    keywords=['diagrams', 'syntax', 'grammar', 'railroad diagrams'],
    python_requires=">= 3.7",
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
)
