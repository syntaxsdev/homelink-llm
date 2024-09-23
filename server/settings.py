from .models import VoiceSettings, LLMSettings, SettingsModel
from shared.utils import load_yaml
from dataclasses import dataclass
from shared.mixins import ResponseMixin
import os
from redis import Redis


@dataclass
class SettingsResponse(ResponseMixin):
    response: any  # Redefine response


class Settings:
    def __init__(self, settings_opt: str, settings: str, client: str, redis: Redis):
        self.redis = redis
        try:
            self.settings_opt: dict[str, str] = load_yaml(settings_opt)
        except Exception as ex:
            raise AttributeError("Error trying to load settings options.") from ex

        try:
            self.settings: dict[str, dict] = load_yaml(settings)
        except Exception as ex:
            raise AttributeError("Error trying to load runtime settings file") from ex
        
        # try:
        #     self.client: dict[str, str] = load_yaml(client)
        # except Exception as ex:
        #     raise AttributeError("Error trying to load client settings.") from ex

        self.ensure_options(self.settings)

        self.refresh_settings()

    def refresh_settings(self):
        """
        Refresh the models
        """
        self.llm = LLMSettings.model_validate(self.settings.get("llm"))
        self.voice = VoiceSettings.model_validate(self.settings.get("voice"))

    def ensure_options(self, settings: dict[str, dict]):
        """
        Ensure all the options for the Settings are within boundaries
        """
        for _, row in settings.items():
            for key, val in row.items():
                opts_for_key = self.settings_opt.get(f"{key}_options")

                if not opts_for_key:
                    continue

                if type(opts_for_key) is list:
                    if val not in opts_for_key:
                        raise AttributeError(f"Option: `{val}` is not a valid option")
                elif type(opts_for_key) is str:
                    if opts_for_key == "number!" and isinstance(val) is not int:
                        raise AttributeError(f"Option `{key}` must be number")
                    elif opts_for_key == "float!":
                        if not isinstance(val, (float, int)):
                            raise AttributeError(f"Option `{key}` must be float")
                    elif not opts_for_key.find(str(val)) >= 0:
                        raise AttributeError(f"Option: `{val}` is not a valid option")

    def get(self, key: str):
        """
        Get settings by key
        """
        data = self.settings.get(key)
        if not data:
            metadata = self.settings.keys()
            return SettingsResponse(
                response="Could not find setting.",
                retry=True,
                meta={"list_of_keys", metadata},
            )
        return SettingsResponse(response=self.settings.get(key), completed=True)

    def set(self, key: str, sub_key: str, value: str):
        """
        Set the key

        Args:
            key: the Settings Model
            sub_key: the subkey in that Settings Model
            value: the value to set
        """

        row = self.settings.get(key)
        if not row:
            return SettingsResponse(
                respone="Setting does not exist",
                retry=True,
                meta={"list_of_keys": self.settings.keys()},
            )

        field = row.get(sub_key)
        if not field:
            return SettingsResponse(
                response=f"This field does not exist within `{key}`",
                retry=True,
                meta={"list_of_fields": row.keys()},
            )

        settings_copy = self.settings.copy()
        settings_copy.get(key)[sub_key] = value
        self.redis.hset("homelink_settings", f"{key}_{sub_key}", value)

        try:
            self.ensure_options(settings_copy)
        except Exception as ex:
            return SettingsResponse(
                response="Incorrect value type", retry=True, meta=ex
            )

        self.settings = settings_copy
        return SettingsResponse(response="Updated settings", completed=True)
