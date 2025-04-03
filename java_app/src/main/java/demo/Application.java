package demo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class Application {

    private static final Logger logger = LoggerFactory.getLogger("java-workshop");

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);

        // 服務啟動時，先設定 MDC
        MDC.put("instance", "java-workshop-01");
        MDC.put("correlationId", "system-init");

        logger.info("Java app started on port 8080");

        // 清除 MDC，避免汙染其他後續執行緒或程式碼
        MDC.clear();
    }

    @GetMapping("/java-hello")
    public String hello(jakarta.servlet.http.HttpServletRequest request) {
        // 從 header 獲取 correlationId
        String correlationId = request.getHeader("X-Correlation-ID");
        if (correlationId == null || correlationId.isEmpty()) {
            correlationId = "unknown";
        }
        
        // 設置 MDC 上下文
        MDC.put("instance", "java-workshop-01");
        MDC.put("correlationId", correlationId);
        MDC.put("context", String.format("{\"headers\":{\"X-Correlation-ID\":\"%s\"}}", correlationId));

        logger.info("Received GET /java-hello request with correlationId: " + correlationId);

        MDC.clear(); // 清除 MDC，避免汙染其他請求

        return "Hello from Java App!";
    }
}
