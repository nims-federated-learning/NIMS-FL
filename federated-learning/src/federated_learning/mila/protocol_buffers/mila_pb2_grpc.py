# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
import federated_learning.mila.protocol_buffers.mila_pb2 as mila__pb2


class MilaStub(object):
    pass

    def __init__(self, channel):
        """Constructor.

        Args:
          channel: A grpc.Channel.
        """
        self.Authenticate = channel.unary_unary(
            "/mila.Mila/Authenticate",
            request_serializer=mila__pb2.Client.SerializeToString,
            response_deserializer=mila__pb2.Token.FromString,
        )
        self.Heartbeat = channel.unary_unary(
            "/mila.Mila/Heartbeat",
            request_serializer=mila__pb2.Token.SerializeToString,
            response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
        )
        self.Close = channel.unary_unary(
            "/mila.Mila/Close",
            request_serializer=mila__pb2.Token.SerializeToString,
            response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
        )
        self.RequestModel = channel.unary_unary(
            "/mila.Mila/RequestModel",
            request_serializer=mila__pb2.Token.SerializeToString,
            response_deserializer=mila__pb2.Model.FromString,
        )
        self.SendCheckpoint = channel.unary_unary(
            "/mila.Mila/SendCheckpoint",
            request_serializer=mila__pb2.Checkpoint.SerializeToString,
            response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
        )


class MilaServicer(object):
    pass

    def Authenticate(self, request, context):
        pass
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Heartbeat(self, request, context):
        pass
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Close(self, request, context):
        pass
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def RequestModel(self, request, context):
        pass
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SendCheckpoint(self, request, context):
        pass
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_MilaServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Authenticate": grpc.unary_unary_rpc_method_handler(
            servicer.Authenticate,
            request_deserializer=mila__pb2.Client.FromString,
            response_serializer=mila__pb2.Token.SerializeToString,
        ),
        "Heartbeat": grpc.unary_unary_rpc_method_handler(
            servicer.Heartbeat,
            request_deserializer=mila__pb2.Token.FromString,
            response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
        ),
        "Close": grpc.unary_unary_rpc_method_handler(
            servicer.Close,
            request_deserializer=mila__pb2.Token.FromString,
            response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
        ),
        "RequestModel": grpc.unary_unary_rpc_method_handler(
            servicer.RequestModel,
            request_deserializer=mila__pb2.Token.FromString,
            response_serializer=mila__pb2.Model.SerializeToString,
        ),
        "SendCheckpoint": grpc.unary_unary_rpc_method_handler(
            servicer.SendCheckpoint,
            request_deserializer=mila__pb2.Checkpoint.FromString,
            response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "mila.Mila", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))
