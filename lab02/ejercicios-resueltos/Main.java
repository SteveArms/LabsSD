import java.util.Random;

class LamportClock {
    private int clock;

    public LamportClock() {
        this.clock = 0;
    }

    public synchronized int tick() {
        clock++;
        return clock;
    }

    public synchronized void update(int receivedTime) {
        clock = Math.max(clock, receivedTime) + 1;
    }

    public int getTime() {
        return clock;
    }
}

class Process extends Thread {
    private int id;
    private LamportClock clock;
    private Process otherProcess;
    private Random random = new Random();

    public Process(int id) {
        this.id = id;
        this.clock = new LamportClock();
    }

    public void setOtherProcess(Process other) {
        this.otherProcess = other;
    }

    public void sendMessage() {
        int time = clock.tick();
        System.out.println("Proceso " + id + " ENVÍA mensaje con tiempo " + time);

        // Simular envío al otro proceso
        otherProcess.receiveMessage(time);
    }

    public void receiveMessage(int receivedTime) {
        clock.update(receivedTime);
        System.out.println("Proceso " + id + " RECIBE mensaje y ajusta reloj a " + clock.getTime());
    }

    @Override
    public void run() {
        try {
            // Evento interno
            int t = clock.tick();
            System.out.println("Proceso " + id + " evento interno con tiempo " + t);

            Thread.sleep(random.nextInt(500));

            // Enviar mensaje
            sendMessage();

            Thread.sleep(random.nextInt(500));

            // Otro evento interno
            t = clock.tick();
            System.out.println("Proceso " + id + " evento interno con tiempo " + t);

        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}

public class Main {
    public static void main(String[] args) {

        Process p1 = new Process(1);
        Process p2 = new Process(2);

        // Conectar procesos (simular red)
        p1.setOtherProcess(p2);
        p2.setOtherProcess(p1);

        p1.start();
        p2.start();
    }
}