/* Application Layer - Main Entry */
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "../drv/uart_drv.h"
#include "../util/ringbuf.h"

#define APP_TASK_STACK_SIZE  512
#define APP_QUEUE_LENGTH      10
#define LED_TOGGLE_MS        500

static void app_led_task(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    for (;;) {
        gpio_bit_toggle(LED_PORT, LED_PIN);
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(LED_TOGGLE_MS));
    }
}

static void app_uart_task(void *pvParameters) {
    ringbuf_t rx_ring;
    ringbuf_init(&rx_ring, 256);

    uint8_t rx_byte;
    for (;;) {
        if (xQueueReceive(uart_rx_queue, &rx_byte, portMAX_DELAY) == pdPASS) {
            ringbuf_put(&rx_ring, rx_byte);
            if (rx_byte == '\n') {
                app_process_command(&rx_ring);
            }
        }
    }
}

int main(void) {
    uart_config_t uart_cfg = {
        .usart_periph = USART0,
        .tx_pin = GPIO_PIN_9,
        .rx_pin = GPIO_PIN_10,
        .baudrate = 115200,
    };
    uart_drv_init(&uart_cfg);

    xTaskCreate(app_led_task, "led", APP_TASK_STACK_SIZE, NULL, 1, NULL);
    xTaskCreate(app_uart_task, "uart", APP_TASK_STACK_SIZE, NULL, 2, NULL);

    vTaskStartScheduler();
    return 0;
}
