from pathlib import Path
from json import load

class Reddit:
    def __init__(self, reddit: dict) -> None:
        self.client_id = reddit["client_id"]
        self.client_secret = reddit["client_secret"]
        self.user_agent = reddit["user_agent"]

class ConfigManager():
    # Should't be changed
    config: dict
    token: str
    prefix: str

    def __init__(self, path: Path) -> None:
        with open(path, 'r') as fp:
            self.config = load(fp)
            self.token = self.config['token']
            self.prefix = self.config['prefix']
            self.reddit = Reddit(self.config['reddit'])