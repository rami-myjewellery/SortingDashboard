import os
import json

from google import auth
from google.cloud import secretmanager


class environment_variables_provider(object):
    def __init__(self):
        self._openai_api_key = None
        self._akeneo_access_token = None
        self._akeneo_base_url = None
        self._local_variables = {
        }

        self._env_json = {}
        self._env_json_path = os.path.dirname(os.path.realpath(__file__)) + "/../../.env.json"

        if (os.path.isfile(self._env_json_path)):
            _env_json = json.load(open(self._env_json_path))

        self.secret_manager_client = secretmanager.SecretManagerServiceClient()

        self._fs_credentials = None
        self._database_name = None
        self._db_credentials = None
        self._pubsub_info = None
        self._pubsub_translator_info = None
        self._throttle_value = None

    def get_variable(self, key: str):
        stage = os.environ.get("STAGE") or "dev"
        # key_for_stage = f'{key}_{stage}'
        key_for_stage = f'{key}'
        if stage == "dev" and (variable := self._env_json.get(key_for_stage)) is not None:
            return variable
        if (variable := self._local_variables.get(key_for_stage)) is not None:
            return variable
        if (variable := os.environ.get(key)) is not None:
            return variable
        return self._get_from_secret_manager(key_for_stage)

    def _get_from_secret_manager(self, key):
        _, project_id = auth.default()

        name = self.secret_manager_client.secret_version_path(project_id, key, "latest")

        secret = self.secret_manager_client.access_secret_version(name=name)
        return secret.payload.data.decode("UTF-8")

    def openai_api_key(self):
        if self._openai_api_key is None:
            openai_api_key = self.get_variable("openai_api_key")
            self._openai_api_key = openai_api_key
        return self._openai_api_key

environment_variables_provider = environment_variables_provider()

def get_environment_variables_provider():
    return environment_variables_provider