package com.grpc;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;

public class CalculatorServer {

    static class CalculatorService
            extends CalculatorGrpc.CalculatorImplBase {

        @Override
        public void sum(
                Request req,
                StreamObserver<Response> responseObserver) {

            int result = req.getA() + req.getB();

            Response response =
                    Response.newBuilder()
                            .setResult(result)
                            .build();

            responseObserver.onNext(response);

            responseObserver.onCompleted();
        }
    }

    public static void main(String[] args) throws Exception {

        Server server = ServerBuilder
                .forPort(50051)
                .addService(new CalculatorService())
                .build();

        server.start();

        System.out.println(
                "Servidor gRPC iniciado..."
        );

        server.awaitTermination();
    }
}