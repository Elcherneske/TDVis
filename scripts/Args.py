import os
import configparser
import argparse
class Args:
    def __init__(self):
        self.config_path = './.streamlit/config.toml'
        if os.path.exists(self.config_path):
            self.config = configparser.ConfigParser()
            self.config.read(self.config_path)
        else:
            raise FileNotFoundError(f"配置文件 {self.config_path} 不存在")
    
    def get_config(self, section, option):
        if section in self.config and option in self.config[section]:
            value = self.config[section][option]
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
            try:
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value  # Return as string if conversion fails
        return None
    
    def save_config(self):
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

    def set_config(self, section, option, value, is_save = True):
        if section not in self.config:
            self.config.add_section(section)
        self.config[section][option] = str(value)
        if is_save:
            self.save_config()
    