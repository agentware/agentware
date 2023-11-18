from setuptools import setup, find_packages

with open("../README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='agentware',
    version='1.2.0',
    description='A framework that can be used to easily build agents that has memory and knowledgebase',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='darthjaja',
    author_email='your-email@example.com',
    packages=find_packages(),
    package_data={
        'agentware': ['base_agent_configs/*.json']
    },
    install_requires=[
        "tiktoken==0.3.3",
        "openai==0.27.2",
        "jwt==1.3.1",
        "colorlog==6.7.0",
        "python-dotenv==1.0.0",
        "pystache==0.6.0",
        "ultralytics==8.0.158",
        "img2vec-pytorch==1.0.1"
    ],
)
