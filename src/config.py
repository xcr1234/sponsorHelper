import os.path
import random
import tomllib

from google import genai
from google.genai import types, Client

if not os.path.exists("project.toml"):
    raise Exception('找不到配置文件project.toml，请将文件project.example.toml复制一份，然后修改其中的配置！！')

with open("project.toml", "rb") as f:
    conf = tomllib.load(f)

gemini_conf = conf['gemini']
sponsor_conf = conf['sponsor']
running_conf = conf['running']

def gemini_client(api_key):
    options = types.HttpOptions(
        timeout=120000,
    )
    if gemini_conf['proxy']:
        options.client_args={'proxy': gemini_conf['proxy']}

    return genai.Client(api_key=api_key,http_options=options)


all_gemini_client = [gemini_client(x) for x in gemini_conf['api_key_list']]


def get_google_client() -> Client:
    return random.choice(all_gemini_client)