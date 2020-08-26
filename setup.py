import os

from setuptools import setup


def get_full_description():
    with open("README.md", encoding="utf8") as f:
        return f.read()


def get_packages(package):
    return [
        root
        for root, _, _ in os.walk(package)
        if os.path.exists(os.path.join(root, "__init__.py"))
    ]


setup(
    name="crax",
    version="0.1.5",
    python_requires=">=3.7",
    url="https://github.com/ephmann/crax",
    license="BSD",
    description="Python Asynchronous Web Development Switz Knife.",
    long_description=get_full_description(),
    long_description_content_type="text/markdown",
    author="Eugene Mercousheu",
    author_email="crax.info@gmail.com",
    packages=get_packages("crax"),
    install_requires=["aiofiles", "jinja2", "python-multipart", "itsdangerous"],
    extras_require={
        "postgresql": [
            "sqlalchemy",
            "databases",
            "alembic",
            "asyncpg",
            "psycopg2-binary",
        ],
        "mysql": ["sqlalchemy", "databases", "alembic", "aiomysql", "pymysql==0.9.2"],
        "sqlite": ["sqlalchemy", "databases", "alembic", "aiosqlite"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    zip_safe=False,
)
