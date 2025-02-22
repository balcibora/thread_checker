import java.util.concurrent.*;

public class ParallelExample {
    public static void main(String[] args) {
        ExecutorService executor = Executors.newFixedThreadPool(4);
        executor.execute(() -> System.out.println("Running in parallel"));
        executor.shutdown();
    }
}
