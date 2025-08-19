from setuptools import setup, find_packages

setup(
    name="ai_tutor_platform",
    version="1.0.0",
    author="Gyan Thakur",
    description="An AI-powered tutoring platform using FastAPI, LangChain, and Mistral via LM Studio.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your_username/ai_tutor_platform",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "langchain",
        "pydantic",
        "python-multipart",
        "requests",
        "pymongo",
        "google-generativeai"
    ]
)
