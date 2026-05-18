package com.lab05.grpc;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;

import com.lab05.grpc.ConverterProto.ConvertRequest;
import com.lab05.grpc.ConverterProto.ConvertResponse;
import com.lab05.grpc.ConverterProto.ConversionType;

import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class ConverterServer {

    private static final int    PORT                = 50052;
    private static final double TIPO_CAMBIO_PEN_USD = 0.2685;

    public static void main(String[] args) throws IOException, InterruptedException {

        Server server = ServerBuilder
                .forPort(PORT)
                .addService(new ConverterServiceImpl())
                .build();

        log("INFO", "Servidor gRPC iniciado en el puerto " + PORT);
        log("INFO", "Conversiones: Celsius<->Fahrenheit | Soles<->Dolares | Km<->Millas");
        log("INFO", "Esperando peticiones...");
        System.out.println();

        server.start();

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            log("INFO", "Senal de apagado recibida. Deteniendo servidor...");
            server.shutdown();
            log("INFO", "Servidor detenido.");
        }));

        server.awaitTermination();
    }

    static void log(String level, String message) {
        String ts = LocalDateTime.now()
                .format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        System.out.println("[" + ts + "] [" + level + "] " + message);
    }

    // =========================================================================
    //  Implementacion del servicio
    // =========================================================================
    static class ConverterServiceImpl extends ConverterGrpc.ConverterImplBase {

        @Override
        public void convert(ConvertRequest req,
                            StreamObserver<ConvertResponse> responseObserver) {

            double         inputValue = req.getValue();
            ConversionType type       = req.getType();

            log("INFO", "Peticion recibida  | tipo=" + type + " | valor=" + inputValue);

            // 1. Validacion general
            if (Double.isNaN(inputValue) || Double.isInfinite(inputValue)) {
                sendError(responseObserver, "El valor de entrada no es un numero valido.");
                return;
            }

            // 2. Validaciones especificas
            String validationError = validateInput(inputValue, type);
            if (validationError != null) {
                sendError(responseObserver, validationError);
                return;
            }

            // 3. Calculo
            double result;
            String unitLabel;

            switch (type) {
                case CELSIUS_TO_FAHRENHEIT:
                    result    = inputValue * 1.8 + 32.0;
                    unitLabel = "F";
                    break;
                case FAHRENHEIT_TO_CELSIUS:
                    result    = (inputValue - 32.0) / 1.8;
                    unitLabel = "C";
                    break;
                case SOLES_TO_DOLARES:
                    result    = inputValue * TIPO_CAMBIO_PEN_USD;
                    unitLabel = "USD";
                    break;
                case DOLARES_TO_SOLES:
                    result    = inputValue / TIPO_CAMBIO_PEN_USD;
                    unitLabel = "PEN (S/.)";
                    break;
                case KM_TO_MILLAS:
                    result    = inputValue * 0.621371;
                    unitLabel = "millas";
                    break;
                case MILLAS_TO_KM:
                    result    = inputValue / 0.621371;
                    unitLabel = "km";
                    break;
                default:
                    sendError(responseObserver, "Tipo de conversion desconocido: " + type);
                    return;
            }

            // 4. Redondear a 4 decimales
            result = Math.round(result * 10_000.0) / 10_000.0;
            log("INFO", "Resultado          | " + result + " " + unitLabel);

            // 5. Respuesta exitosa
            ConvertResponse response = ConvertResponse.newBuilder()
                    .setResult(result)
                    .setUnitLabel(unitLabel)
                    .setSuccess(true)
                    .setErrorMessage("")
                    .build();

            responseObserver.onNext(response);
            responseObserver.onCompleted();
            log("INFO", "Respuesta enviada correctamente.");
            System.out.println();
        }

        private String validateInput(double value, ConversionType type) {
            switch (type) {
                case CELSIUS_TO_FAHRENHEIT:
                    if (value < -273.15)
                        return "Temperatura invalida: " + value + " C esta bajo el cero absoluto (-273.15 C).";
                    break;
                case FAHRENHEIT_TO_CELSIUS:
                    if (value < -459.67)
                        return "Temperatura invalida: " + value + " F esta bajo el cero absoluto (-459.67 F).";
                    break;
                case SOLES_TO_DOLARES:
                case DOLARES_TO_SOLES:
                    if (value < 0)
                        return "El monto monetario no puede ser negativo: " + value;
                    break;
                case KM_TO_MILLAS:
                case MILLAS_TO_KM:
                    if (value < 0)
                        return "La distancia no puede ser negativa: " + value;
                    break;
                default:
                    break;
            }
            return null;
        }

        private void sendError(StreamObserver<ConvertResponse> observer, String msg) {
            log("ERROR", "Validacion fallida | " + msg);
            ConvertResponse errorResponse = ConvertResponse.newBuilder()
                    .setResult(0)
                    .setUnitLabel("")
                    .setSuccess(false)
                    .setErrorMessage(msg)
                    .build();
            observer.onNext(errorResponse);
            observer.onCompleted();
            System.out.println();
        }
    }
}
