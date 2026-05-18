package com.lab05.grpc;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.StatusRuntimeException;

import com.lab05.grpc.ConverterProto.ConvertRequest;
import com.lab05.grpc.ConverterProto.ConvertResponse;
import com.lab05.grpc.ConverterProto.ConversionType;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.TimeUnit;

public class ConverterClient {

    private static final String HOST = "localhost";
    private static final int    PORT = 50052;

    static void log(String level, String message) {
        String ts = LocalDateTime.now()
                .format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        System.out.println("[" + ts + "] [" + level + "] " + message);
    }

    public static void main(String[] args) throws InterruptedException {

        ManagedChannel channel = ManagedChannelBuilder
                .forAddress(HOST, PORT)
                .usePlaintext()
                .build();

        ConverterGrpc.ConverterBlockingStub stub = ConverterGrpc.newBlockingStub(channel);

        log("INFO", "Cliente conectado a " + HOST + ":" + PORT);
        log("INFO", "Iniciando bateria de pruebas...");
        System.out.println();

        String sep = "============================================================";

        // ── TEMPERATURA ───────────────────────────────────────────────────────
        System.out.println(sep);
        System.out.println("  TEMPERATURA");
        System.out.println(sep);
        convert(stub,   0.0, ConversionType.CELSIUS_TO_FAHRENHEIT);   // -> 32 F
        convert(stub, 100.0, ConversionType.CELSIUS_TO_FAHRENHEIT);   // -> 212 F
        convert(stub, -40.0, ConversionType.CELSIUS_TO_FAHRENHEIT);   // -> -40 F
        convert(stub,  32.0, ConversionType.FAHRENHEIT_TO_CELSIUS);   // -> 0 C
        convert(stub,  98.6, ConversionType.FAHRENHEIT_TO_CELSIUS);   // -> 37 C

        System.out.println();
        log("INFO", ">> Prueba de validacion: temperatura imposible");
        convert(stub, -300.0, ConversionType.CELSIUS_TO_FAHRENHEIT);  // ERROR

        // ── MONEDA ────────────────────────────────────────────────────────────
        System.out.println();
        System.out.println(sep);
        System.out.println("  MONEDA  (1 USD ~ 3.724 PEN)");
        System.out.println(sep);
        convert(stub, 100.0, ConversionType.SOLES_TO_DOLARES);
        convert(stub,  50.0, ConversionType.SOLES_TO_DOLARES);
        convert(stub,   1.0, ConversionType.DOLARES_TO_SOLES);
        convert(stub,  20.0, ConversionType.DOLARES_TO_SOLES);

        System.out.println();
        log("INFO", ">> Prueba de validacion: monto negativo");
        convert(stub, -5.0, ConversionType.SOLES_TO_DOLARES);         // ERROR

        // ── DISTANCIA ─────────────────────────────────────────────────────────
        System.out.println();
        System.out.println(sep);
        System.out.println("  DISTANCIA");
        System.out.println(sep);
        convert(stub,  1.0,   ConversionType.KM_TO_MILLAS);
        convert(stub, 42.195, ConversionType.KM_TO_MILLAS);           // maraton
        convert(stub,  1.0,   ConversionType.MILLAS_TO_KM);
        convert(stub, 26.2,   ConversionType.MILLAS_TO_KM);           // maraton en millas

        System.out.println();
        log("INFO", ">> Prueba de validacion: distancia negativa");
        convert(stub, -10.0, ConversionType.KM_TO_MILLAS);            // ERROR

        // ── Cierre ────────────────────────────────────────────────────────────
        System.out.println();
        System.out.println(sep);
        log("INFO", "Todas las pruebas completadas.");
        channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
        log("INFO", "Canal cerrado. Fin del cliente.");
    }

    private static void convert(ConverterGrpc.ConverterBlockingStub stub,
                                 double value,
                                 ConversionType type) {
        try {
            ConvertRequest request = ConvertRequest.newBuilder()
                    .setValue(value)
                    .setType(type)
                    .build();

            ConvertResponse response = stub.convert(request);

            if (response.getSuccess()) {
                System.out.printf("  [OK]   %-25s  %9.4f  ->  %.4f %s%n",
                        type, value, response.getResult(), response.getUnitLabel());
            } else {
                System.out.printf("  [FAIL] %-25s  %9.4f  ->  ERROR: %s%n",
                        type, value, response.getErrorMessage());
            }

        } catch (StatusRuntimeException e) {
            log("ERROR", "Fallo de comunicacion gRPC: " + e.getStatus());
        }
    }
}
