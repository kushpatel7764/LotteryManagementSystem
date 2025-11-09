from setuptools import setup, find_packages

setup(
    name="lottery_app",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,  # Important to include non-Python files
    install_requires=[
        "beautifulsoup4==4.13.4",
        "decorator==5.1.1",
        "etelemetry==0.3.1",
        "Flask==3.0.3",
        "pandas",
        "pytest",
        "reportlab",
        "requests==2.31.0",
        "Gunicorn==21.2.0",
        "ruff",
        "simplejson",
        "urllib3",
        "util-functions"
    ],
    package_data={
        "lottery_app": ["templates/*.html", "static/*", "*.json","database/*.sql", "database/*.db"],  # include SQL files
    },
    entry_points={
        "console_scripts": [
            "lottery_app=lottery_app.app:main",  # optional CLI entry
        ],
    },
)
