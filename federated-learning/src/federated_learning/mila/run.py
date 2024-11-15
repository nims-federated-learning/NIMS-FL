import logging
from argparse import ArgumentParser
import torch
import numpy as np

from federated_learning.mila.configs import CVConfiguration, ServerConfiguration, ClientConfiguration
from federated_learning.mila.services import CrossValidation, Server, Client, DefaultServicer

logging.basicConfig(format="", level=logging.INFO)


class Executor:
    def __init__(self, config_path: str):
        self._config_path = config_path

    def run(self, job: str):
        if not hasattr(self, job):
            raise ValueError("Unknown job requested: {}".format(job))

        getattr(self, job)()

    def server(self) -> None:
        config: ServerConfiguration = ServerConfiguration.from_json(self._config_path)

        server = Server(config=config)
        servicer = DefaultServicer(config=config)

        server.run(servicer=servicer)

    def client(self) -> None:
        config: ClientConfiguration = ClientConfiguration.from_json(self._config_path)

        client = Client(config=config)
        client.run()

    def mean_cv(self) -> None:
        config: CVConfiguration = CVConfiguration.from_json(self._config_path)
        logging.getLogger().setLevel(config.log_level)
        torch.manual_seed(config.seed)
        np.random.seed(config.seed)
        cv = CrossValidation(config=config)
        cv.run()

def main():
    parser = ArgumentParser()
    parser.add_argument("job")
    parser.add_argument("config")
    args = parser.parse_args()

    Executor(args.config).run(args.job)

if __name__ == "__main__":
    main()