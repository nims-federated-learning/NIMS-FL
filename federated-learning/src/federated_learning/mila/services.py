import importlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import uuid
from concurrent import futures
from dataclasses import dataclass, field
from glob import glob
from threading import Thread, Lock
from time import time, sleep
from typing import Dict, Callable, Any, List, Type, Optional
from multiprocessing import get_context
from functools import partial

import grpc
from google.protobuf.empty_pb2 import Empty as EmptyResponse
import numpy as np
import torch
from tqdm import tqdm
from federated_learning.lib.data.streamers import CrossValidationStreamer
from federated_learning.lib.model.executors import Evaluator
from federated_learning.lib.model.metrics import CsvLogger
from federated_learning.run import Executor
from federated_learning.lib.core.config import Config
from federated_learning.lib.core.helpers import ConfidenceInterval, Namespace
import pickle

from federated_learning.mila.configs import CVConfiguration, ServerConfiguration, ClientConfiguration
from federated_learning.mila.exceptions import InvalidNameError, ClientAuthenticationError
from federated_learning.mila.factories import AbstractConfiguration, AbstractExecutor, AbstractAggregator
from federated_learning.mila.protocol_buffers import mila_pb2, mila_pb2_grpc


class IOManager:

    def _read_file(self, file_path: str) -> bytes:
        with open(file_path, "rb") as read_buffer:
            return read_buffer.read()

    def _reflect(self, object_path: str) -> Callable:
        module, class_name = object_path.rsplit(".", 1)
        try:
            return getattr(importlib.import_module(module), class_name)
        except:
            module = "federated_learning." + module
            return getattr(importlib.import_module(module), class_name)


@dataclass
class Participant:
    name: str
    ip_address: str

    token: str = field(default_factory=lambda: str(uuid.uuid4()))
    round: int = 0
    awaiting_response: bool = False

    __last_heartbeat: float = field(default_factory=time)

    def register_heartbeat(self) -> None:
        self.__last_heartbeat = time()

    def is_alive(self, heartbeat_timeout: float) -> bool:
        return time() - self.__last_heartbeat < heartbeat_timeout

    def __eq__(self, other: "Participant") -> bool:
        return self.name == other.name and self.ip_address == other.ip_address

    def __str__(self) -> str:
        return "{}|{}".format(self.name, self.ip_address)


class ServerManager(IOManager):

    def __init__(self, config: ServerConfiguration) -> None:
        self._config = config
        self._registry: Dict[str, Participant] = {}

        self._current_round = 1
        self._latest_checkpoint = self._config.start_point
        self._last_registration_time = 0
        self._is_registration_closed = False

        if not os.path.exists(self._config.save_path):
            os.makedirs(self._config.save_path)

    def verify_ip(self, ip_address: str) -> bool:
        if ip_address in self._config.blacklist:
            return False

        if self._config.use_whitelist and ip_address not in self._config.whitelist:
            return False

        return True

    def register_client(self, name: str, ip_address: str) -> str:
        client = Participant(name=name, ip_address=ip_address)
        for entry in self._registry.values():
            if client == entry:
                return entry.token

        if not self.should_wait_for_additional_clients():
            raise ClientAuthenticationError("Authentication failed... Registration is closed.")

        self._registry[client.token] = client
        self._last_registration_time = time()

        logging.info("[{}] Successfully authenticated (clients={})".format(client, self.get_clients_count()))
        return client.token

    def verify_token(self, token: str, ip_address: str) -> bool:
        return (
            token in self._registry
            and self._registry[token].ip_address == ip_address
            and self._registry[token].is_alive(self._config.heartbeat_timeout)
        )

    def register_heartbeat(self, token: str) -> None:
        client = self._registry[token]

        client.register_heartbeat()
        logging.debug("[{}] Heartbeat registered".format(client))

    def close_connection(self, token: str) -> None:
        client = self._registry[token]

        self._registry.pop(token)
        logging.info("[{}] Disconnected (clients={})".format(client, self.get_clients_count()))

    def save_checkpoint(self, token: str, content: bytes) -> None:
        client = self._registry[token]
        save_path = self.get_client_filename_for_current_round(client)

        with open(save_path, "wb") as write_buffer:
            write_buffer.write(content)

        logging.info("[{}] Checkpoint Received".format(client))

    def get_configuration(self) -> bytes:
        return self._read_file(self._config.task_configuration_file)

    def get_latest_checkpoint(self) -> bytes:
        if self._latest_checkpoint is None:
            return b""

        return self._read_file(self._latest_checkpoint)

    def close_registration(self) -> None:
        self._is_registration_closed = True

    def should_wait_for_additional_clients(self) -> bool:
        if self._is_registration_closed:
            return False

        clients_count = self.get_clients_count()

        return (
            clients_count < self._config.minimum_clients
            or (
                clients_count < self._config.maximum_clients
                and time() - self._last_registration_time < self._config.client_wait_time
            )
        )

    def are_more_rounds_required(self) -> bool:
        return self._current_round <= self._config.rounds_count

    def set_client_status_to_awaiting_response(self, token: str) -> bool:
        client = self._registry[token]
        if client.round >= self._current_round:
            return False

        client.round = self._current_round
        client.awaiting_response = True
        return True

    def set_client_status_to_available(self, token: str) -> None:
        self._registry[token].awaiting_response = False

    def are_all_updates_received(self) -> bool:
        for client in self._registry.values():
            if client.awaiting_response or client.round != self._current_round:
                return False

        return True

    def aggregate(self) -> None:
        logging.info("Start aggregation (round={})".format(self._current_round))

        checkpoint_paths = self.get_clients_model_path_for_current_round()
        save_path = "{}/{}.aggregate".format(self._config.save_path, self._current_round)

        aggregator: Type[AbstractAggregator] = self._reflect(self._config.aggregator_type)
        aggregator(**self._config.aggregator_options).run(checkpoint_paths=checkpoint_paths, save_path=save_path)

        logging.info("Aggregate model saved: [{}]".format(save_path))
        self._latest_checkpoint = save_path

    def enable_next_round(self) -> None:
        self._current_round += 1
        if self._current_round <= self._config.rounds_count:
            logging.info("Starting round [{}]".format(self._current_round))

    def get_clients_count(self) -> int:
        return sum(1 for client in self._registry.values() if client.is_alive(self._config.heartbeat_timeout))

    def get_clients_model_path_for_current_round(self):
        return [
            self.get_client_filename_for_current_round(client)
            for client in self._registry.values()
        ]

    def get_client_filename_for_current_round(self, client: Participant):
        return "{}/{}.{}.{}.remote".format(
            self._config.save_path,
            client.name,
            client.ip_address.replace(".", "_"),
            self._current_round
        )


class DefaultServicer(ServerManager, mila_pb2_grpc.MilaServicer):

    def __init__(self, config: ServerConfiguration) -> None:
        super().__init__(config=config)
        self.__lock = Lock()

    def _validate_token(self, token: str, context) -> bool:
        if not self.verify_token(token=token, ip_address=self._get_ip(context)):
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Access Denied... Token is invalid...")

        return True

    def _get_ip(self, context) -> str:
        return context.peer().split(':')[1]

    def Authenticate(self, request: grpc, context) -> str:
        client_ip = self._get_ip(context)
        if not self.verify_ip(client_ip):
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Access Denied... IP Address is not whitelisted.")

        try:
            token = self.register_client(request.name, client_ip)
            return mila_pb2.Token(token=token)
        except ClientAuthenticationError as e:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))

    def Heartbeat(self, request, context) -> EmptyResponse:
        if self._validate_token(request.token, context):
            self.register_heartbeat(request.token)

            context.set_code(grpc.StatusCode.OK)
            return EmptyResponse()

    def Close(self, request, context) -> EmptyResponse:
        if self._validate_token(request.token, context):
            self.close_connection(request.token)

            context.set_code(grpc.StatusCode.OK)
            return EmptyResponse()

    def RequestModel(self, request, context) -> mila_pb2.Model:
        if self._validate_token(request.token, context):

            if self.should_wait_for_additional_clients():
                context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, "Waiting for more clients to join.")

            self.close_registration()
            if not self.are_more_rounds_required():
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "All rounds have been completed. Closing session.")

            if not self.set_client_status_to_awaiting_response(request.token):
                context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, "Next round is not available yet.")

            client = self._registry[request.token]
            logging.info("[{}] Sending Model (round={})".format(client, client.round))

            return mila_pb2.Model(
                json_configuration=self.get_configuration(),
                latest_checkpoint=self.get_latest_checkpoint()
            )

    def SendCheckpoint(self, request, context) -> EmptyResponse:
        if self._validate_token(request.token, context):
            with self.__lock:
                self.save_checkpoint(token=request.token, content=request.content)
                self.set_client_status_to_available(request.token)

                if self.are_all_updates_received():
                    self.aggregate()
                    self.enable_next_round()

            context.set_code(grpc.StatusCode.OK)
            return EmptyResponse()


class Server(IOManager):

    def __init__(self, config: ServerConfiguration) -> None:
        self._config = config

    def _get_credentials(self) -> grpc.ServerCredentials:
        private_key = self._read_file(self._config.ssl_private_key)
        certificate_chain = self._read_file(self._config.ssl_cert)
        root_certificate = self._read_file(self._config.ssl_root_cert)

        return grpc.ssl_server_credentials(
            ((private_key, certificate_chain),),
            root_certificates=root_certificate,
            require_client_auth=True
        )

    def run(self, servicer: mila_pb2_grpc.MilaServicer) -> None:
        workers_count = max(self._config.workers, self._config.minimum_clients)

        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=workers_count), options=self._config.options)
        mila_pb2_grpc.add_MilaServicer_to_server(servicer, self._server)

        if self._config.use_secure_connection:
            credentials = self._get_credentials()
            self._server.add_secure_port(self._config.target, credentials)
        else:
            self._server.add_insecure_port(self._config.target)
            logging.warning("[CAUTION] Connection is insecure!")

        logging.info("Starting server at: [{}]".format(self._config.target))

        self._server.start()
        self._server.wait_for_termination()


class Client(IOManager):

    def __init__(self, config: ClientConfiguration) -> None:
        self._config = config
        self._token = None

        if not os.path.exists(self._config.save_path):
            os.makedirs(self._config.save_path)

        self._validate()

    def _validate(self) -> None:
        if not re.match(r"^[\w]+$", self._config.name):
            raise InvalidNameError(
                "[ERROR] The client name can only contain alphanumeric characters and underscores."
            )

    def _get_credentials(self) -> grpc.ServerCredentials:
        private_key = self._read_file(self._config.ssl_private_key)
        certificate_chain = self._read_file(self._config.ssl_cert)
        root_certificate = self._read_file(self._config.ssl_root_cert)

        return grpc.ssl_channel_credentials(
            certificate_chain=certificate_chain,
            private_key=private_key,
            root_certificates=root_certificate
        )

    def _connect(self) -> grpc.Channel:
        if self._config.use_secure_connection:
            credentials = self._get_credentials()
            return grpc.secure_channel(
                target=self._config.target, credentials=credentials, options=self._config.options
            )
        else:
            logging.warning("[CAUTION] Connection is insecure!")
            return grpc.insecure_channel(self._config.target, options=self._config.options)

    def _store_checkpoint(self, checkpoint: bytes) -> str:
        checkpoint_path = "{}/checkpoint.latest".format(self._config.save_path)
        with open(checkpoint_path, "wb") as write_buffer:
            write_buffer.write(checkpoint)

        return checkpoint_path

    def _create_configuration(self, received_configuration: bytes, checkpoint_path: Optional[str]) -> str:
        configuration = json.loads(received_configuration.decode("utf-8"))

        configuration = {**configuration, **self._config.model_overwrites}  # overwrite values based on settings
        configuration["checkpoint_path"] = checkpoint_path

        configuration_path = "{}/config.latest".format(self._config.save_path)
        with open(configuration_path, "w") as write_buffer:
            json.dump(configuration, write_buffer)

        return configuration_path

    def _retrieve_latest_file(self, folder_path: str) -> str:
        files = glob("{}/*".format(folder_path))
        return max(files, key=os.path.getctime)

    def _train(self, configuration_path: str) -> str:
        config: Type[AbstractConfiguration] = self._reflect(self._config.config_type)
        config = config.from_json(configuration_path)

        runner: Type[AbstractExecutor] = self._reflect(self._config.executor_type)
        runner = runner(config=config)
        runner.train()

        return self._retrieve_latest_file(config.output_path)

    def _invoke(self, method: Callable, *args, **kwargs) -> Any:
        with self._connect() as channel:
            while True:
                try:
                    stub = mila_pb2_grpc.MilaStub(channel)
                    kwargs["stub"] = stub

                    return method(*args, **kwargs)

                except grpc.RpcError as e:
                    if grpc.StatusCode.RESOURCE_EXHAUSTED == e.code():
                        sleep(self._config.retry_timeout)
                        continue

                    raise e

    def _heartbeat_daemon(self) -> None:
        while True:

            if not self._token:
                break

            self._invoke(self.heartbeat)
            sleep(self._config.heartbeat_frequency)

    def authenticate(self, stub: mila_pb2_grpc.MilaStub) -> str:
        package = mila_pb2.Client(name=self._config.name)
        response = stub.Authenticate(package)

        return response.token

    def heartbeat(self, stub: mila_pb2_grpc.MilaStub) -> None:
        package = mila_pb2.Token(token=self._token)
        stub.Heartbeat(package)

    def close(self, stub: mila_pb2_grpc.MilaStub) -> None:
        package = mila_pb2.Token(token=self._token)
        stub.Close(package)

        self._token = None

    def set_seed(self, seed):
        torch.manual_seed(seed)
        np.random.seed(seed)

    def request_model(self, stub: mila_pb2_grpc.MilaStub) -> str:
        package = mila_pb2.Token(token=self._token)
        response = stub.RequestModel(package)

        checkpoint_path = None
        if response.latest_checkpoint:
            checkpoint_path = self._store_checkpoint(response.latest_checkpoint)

        return self._create_configuration(response.json_configuration, checkpoint_path)

    def send_checkpoint(self, checkpoint_path: str, stub: mila_pb2_grpc.MilaStub) -> None:
        with open(checkpoint_path, "rb") as read_buffer:
            content = read_buffer.read()

        package = mila_pb2.Checkpoint(token=self._token, content=content)
        stub.SendCheckpoint(package)

    def run(self) -> None:
        try:
            self.set_seed(self._config.seed)
        except:
            pass
        try:
            self._token = self._invoke(self.authenticate)

            self.heartbeat_worker = Thread(target=self._heartbeat_daemon)
            self.heartbeat_worker.daemon = True
            self.heartbeat_worker.start()

            while True:
                configuration_path = self._invoke(self.request_model)
                checkpoint_path = self._train(configuration_path)
                self._invoke(self.send_checkpoint, checkpoint_path=checkpoint_path)

        except grpc.RpcError as e:
            logging.info("[{}] {}".format(e.code(), e.details()))
            if e.code() not in (grpc.StatusCode.PERMISSION_DENIED, grpc.StatusCode.UNAVAILABLE):
                self._invoke(self.close)

        except KeyboardInterrupt:
            logging.info("Stopping gracefully...")
            self._invoke(self.close)

        except Exception as e:
            logging.error("[internal error] {}".format(e))
            self._invoke(self.close)

class CrossValidation(IOManager):

    def __init__(self, config: CVConfiguration):
        self._config = config
        self._cfg_server = ServerConfiguration.from_json(self._config.cfg_server)
        self._cfg_clients = [ClientConfiguration.from_json(c) for c in self._config.cfg_clients]
        self._cfg_model = self.init_model_cfg()
        self.streamer = self.get_validation_streamer()
        self.mp_context = get_context('spawn')

    def init_model_cfg(self):
        _cfg_model = Config.from_json(self._cfg_server.task_configuration_file)
        update = dict()
        update["splitter"] = _cfg_model.splitter
        update["splitter"]["seed"] = self._config.seed
        update["cross_validation_folds"] = self._config.num_folds
        return _cfg_model.cloned_update(**update)

    def get_validation_streamer(self):
        update = {
            "splitter": {
                "type": "Random",
                "seed": self._config.seed
            }
        }
        return CrossValidationStreamer(config=self._cfg_model.cloned_update(**update))


    def run(self):
        """
        We can directly run cross validation with mila. So we are first updating a
        parameter which enable us to train on the right dataset part.
        Then we run each experiment seperatly and concatenate the results.
        """
        result_log = []
        result = {k:[] for k in self._cfg_model.loader["target_column_names"]}
        for id_fold in tqdm(range(self._config.num_folds)):
            self.delete_logs()
            fold_result = self.launch_and_evaluate(id_fold)
            result_log.append(fold_result)
            for i, values in enumerate(vars(fold_result)[self._cfg_model.target_metric]):
                key = self._cfg_model.loader["target_column_names"][i]
                result[key].append(abs(values))
        for k, v in result.items():
            logging.info(f"[{k}]  mean_cv {np.mean(v)} ± {np.std(v)}")

        self.log_result(Namespace.reduce(result_log, ConfidenceInterval.compute))
        self.save_results(result)
        return result


    def update_client_config(self, id_fold: int = None):
        """
        Set an id_fold in each client config. Since the seed is set the folds will be the same
        """
        cfg_clients = []
        for cfg_client in self._cfg_clients:
            cfg_client = cfg_client._asdict()
            cfg_client["model_overwrites"]["subset"]["id_fold"] = id_fold
            cfg_client["seed"] = self._config.seed
            try:
                cfg_client["model_overwrites"]["cross_validation_folds"] = self._config.num_folds
                cfg_client["model_overwrites"]["splitter"] = self._cfg_model.splitter
                cfg_client["model_overwrites"]["splitter"]["id_fold_mila"] = id_fold
                cfg_client["model_overwrites"]["splitter"]["client_distribution"] = cfg_client["model_overwrites"]["subset"]["distribution"]
            except:
                pass
            cfg_clients.append(ClientConfiguration(**cfg_client))

        return cfg_clients


    def launch_and_evaluate(self, id_fold) -> Namespace:
        """
        Wrap the few function necessary to run and evaluate a training.
        :param: id_fold: id of the fold to run
        """
        # Update all client config
        cfg_clients = self.update_client_config(id_fold)

        # Launch experiment
        self.launch_training(cfg_clients)

        # Evaluate experiment
        results = self.evaluate_all(id_fold)
        return results


    def launch_training(self, cfg_clients: List[ClientConfiguration]):
        """
        Launch a server and the right number of workers based on the configuration
        file provided.
        :param: cfg_clients: Config of different client which have been updated
        """
        torch.manual_seed(self._config.seed)
        np.random.seed(self._config.seed)
        # Server launch
        server = Server(config=self._cfg_server)
        servicer = DefaultServicer(config=self._cfg_server)
        server_thread = Thread(target=server.run, args=(servicer, ))
        server_thread.start()
        sleep(5)
        # Clients launch
        clients = [Client(config=config) for config in cfg_clients]
        client_threads = [self.mp_context.Process(target=client.run) for client in clients]
        for t in client_threads:
            t.start()
        for t in client_threads:
            t.join()

        server._server.stop(grace=None)

        if sum([t.exitcode for t in client_threads]) != 0:
            raise Exception("One of the client finish with an error")


    def evaluate_all(self, id_fold):
        """
        Evaluate all aggregate of the server and return the best metrics.
        """
        torch.manual_seed(self._config.seed)
        np.random.seed(self._config.seed)
        results = []

        for _round in range(1, self._cfg_server.rounds_count + 1):
            file_to_evaluate = f"{self._cfg_server.save_path}{_round}.aggregate"
            cfg_model = self.update_model_config(file_to_evaluate, id_fold)
            data_loader = self.streamer.get(
                    split_name=self.streamer.get_fold_name(id_fold),
                    mode=CrossValidationStreamer.Mode.TEST,
                    batch_size=self._cfg_model.batch_size,
                    shuffle=False,
                )
            results.append(Evaluator(config=cfg_model).run(data_loader=data_loader))

        if self._config.save_results:
            best_round = Namespace.reduce(results, partial(np.argmax, axis=0)).__getattribute__(self._cfg_model.target_metric)[0]
            best_file = f"{self._cfg_server.save_path}{best_round}.aggregate"
            cfg_best_model = self.update_model_config(best_file, id_fold)
            Executor(cfg_best_model).predict()
            shutil.copy(best_file, Path(self._config.output_path) / f"run_{id_fold}")

        return Namespace.max(results)


    def update_model_config(self, file_to_evaluate: str, id_fold: int):
        """
        Update the model config with the right id_fold and filepath
        """
        def get_fold_name(fold: int) -> str:
            return "fold_{}".format(fold)

        update = {}
        # Change checkpoint_path
        split_ratio = 1 / self._config.num_folds
        splits = {
            get_fold_name(fold) if fold != id_fold else "test": split_ratio
            for fold in range(self._config.num_folds)
        }
        update["splitter"] =  {
                "type": "Random",
                "seed": self._config.seed,
                "splits": splits
            }
        update["checkpoint_path"] = file_to_evaluate
        update["output_path"] = str(Path(self._config.output_path) / f"run_{id_fold}")
        return self._cfg_model.cloned_update(**update)

    def delete_logs(self):
        """
        Delete all client and server logs
        """
        for _dir in [c.save_path for c in self._cfg_clients] + [self._cfg_server.save_path]:
            if os.path.isdir(_dir):
                shutil.rmtree(_dir)


    def save_results(self, result):
        """
        Save final aggregation of result in a pickle file.
        """
        if not os.path.exists(self._config.output_path):
            os.makedirs(self._config.output_path)
        with open(Path(f"{self._config.output_path}") / 'result_pickle.pkl', "wb") as file:
            pickle.dump(result, file, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"Results saved at {self._config.output_path}")


    def log_result(self, results):
        logger = CsvLogger()
        logger.log_header(self.streamer.labels)
        logger.log_content(results)