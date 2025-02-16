from setuptools import setup, find_packages

setup(
    name="event-trigger",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "motor",
        "pytest",
        "pytest-asyncio",
        "httpx"
    ],
) 