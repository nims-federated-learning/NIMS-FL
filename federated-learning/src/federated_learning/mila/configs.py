from dataclasses import dataclass
from pathlib import Path
import json
from typing import Literal, NamedTuple, List, Tuple, Any, Dict, Optional

from federated_learning.mila.factories import AbstractConfiguration

class ServerConfiguration(NamedTuple):

    task_configuration_file: str
    config_type: str
    executor_type: str

    aggregator_type: str
    aggregator_options: Dict[str, Any] = {}

    target: str = "localhost:8024"
    rounds_count: int = 10
    save_path: str = "data/logs/server/"
    start_point: Optional[str] = None

    workers: int = 2
    minimum_clients: int = 2
    maximum_clients: int = 100
    client_wait_time: int = 10
    heartbeat_timeout: int = 300

    use_secure_connection: bool = False
    ssl_private_key: str = "data/certificates/server.key"
    ssl_cert: str = "data/certificates/server.crt"
    ssl_root_cert: str = "data/certificates/rootCA.pem"
    options: List[Tuple[str, Any]] = [
        ("grpc.max_send_message_length", 1000000000),
        ("grpc.max_receive_message_length", 1000000000),
        ("grpc.ssl_target_name_override", "localhost"),
    ]

    blacklist: List[str] = []
    whitelist: List[str] = []
    use_whitelist: bool = False

    @classmethod
    def from_json(cls, file_path: str) -> "ServerConfiguration":
        with open(file_path) as read_handle:
            return cls(**json.load(read_handle))


class ClientConfiguration(NamedTuple):
    name: str
    config_type: str
    executor_type: str

    target: str = "localhost:8024"
    save_path: str = "data/logs/client/"

    seed: int = 42
    heartbeat_frequency: int = 60
    retry_timeout: int = 1
    model_overwrites: Dict[str, Any] = {"output_path": "data/logs/local/", "epochs": 5}

    options: List[Tuple[str, Any]] = [
        ("grpc.max_send_message_length", 1000000000),
        ("grpc.max_receive_message_length", 1000000000),
        ("grpc.ssl_target_name_override", "localhost"),
    ]

    use_secure_connection: bool = False
    ssl_private_key: str = "data/certificates/client.key"
    ssl_cert: str = "data/certificates/client.crt"
    ssl_root_cert: str = "data/certificates/rootCA.pem"

    @classmethod
    def from_json(cls, file_path: str) -> "ClientConfiguration":
        with open(file_path) as read_handle:
            return cls(**json.load(read_handle))

@dataclass
class CVConfiguration(AbstractConfiguration):
    num_folds: int
    seed: int = 42
    cfg_clients: List[str] = None
    cfg_server: str = ''
    cfg_dir: str = ''
    log_level: Literal['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'] = "INFO"
    save_results: bool = False

    def __post_init__(self):
        if self.cfg_dir != '':
            assert (self.cfg_server == '' and self.cfg_clients is None), \
            "Use either cfg_dir or cfg_server / cfg_client not both"
            self = self.find_cfg()
        else:
            assert (self.cfg_server != '' and self.cfg_clients is not None), \
                "You need to provide config for the client and server with \
                cfg_server / cfg_client or with cfg_dir who will contains both \
                client and server configs"

    def find_cfg(self):
        cfg_dir = Path(self.cfg_dir)
        assert cfg_dir.is_dir(), "Error: cfg_dir param is not a dir"
        self.cfg_clients = [str(cfg) for cfg in cfg_dir.glob("*client*.json")]
        server = list(cfg_dir.glob("*server*.json"))
        assert len(server) == 1, "Error: More than one server config in cfg_dict"
        self.cfg_server = str(server[0])
