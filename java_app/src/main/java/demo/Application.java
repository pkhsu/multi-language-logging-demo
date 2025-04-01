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
        MDC.put("correlationId", "dummy-xyz-java");

        logger.info("Java app started on port 8080");

        // 清除 MDC，避免汙染其他後續執行緒或程式碼
        MDC.clear();
    }

    @GetMapping("/java-hello")
    public String hello() {
        // 收到 /java-hello 請求時，再帶上需要的 MDC 欄位
        MDC.put("instance", "java-workshop-01");
        MDC.put("correlationId", "dummy-xyz-java");
        MDC.put("context", "{\"foo\":\"bar\"}");

        logger.info("Received GET /java-hello request");

        MDC.clear(); // 清除 MDC，避免汙染其他請求

        return "Hello from Java App!";
    }
}
