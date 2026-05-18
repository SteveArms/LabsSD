package com.grpc;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;

public class CalculatorClient {

    public static void main(String[] args) {

        ManagedChannel channel =
                ManagedChannelBuilder
                        .forAddress("localhost", 50051)
                        .usePlaintext()
                        .build();

        CalculatorGrpc.CalculatorBlockingStub stub =
                CalculatorGrpc.newBlockingStub(channel);

        Request request =
                Request.newBuilder()
                        .setA(8)
                        .setB(4)
                        .build();

        Response response =
                stub.sum(request);

        System.out.println(
                "Resultado: "
                        + response.getResult()
        );

        channel.shutdown();
    }
}