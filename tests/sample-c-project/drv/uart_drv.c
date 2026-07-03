/* UART Driver Layer */
#include "gd32f4xx_usart.h"
#include "gd32f4xx_gpio.h"

typedef struct {
    uint32_t usart_periph;
    uint32_t tx_pin;
    uint32_t rx_pin;
    uint32_t baudrate;
} uart_config_t;

typedef struct uart_dev uart_dev_t;

static volatile uint8_t tx_done_flag = 0;
static volatile uint8_t rx_ready_flag = 0;

void uart_drv_init(uart_config_t *cfg) {
    rcu_periph_clock_enable(RCU_GPIOA);
    rcu_periph_clock_enable(RCU_USART0);

    gpio_init(GPIOA, GPIO_MODE_AF_PP, GPIO_OSPEED_50MHZ, cfg->tx_pin);
    gpio_init(GPIOA, GPIO_MODE_IN_FLOATING, GPIO_OSPEED_50MHZ, cfg->rx_pin);

    usart_deinit(cfg->usart_periph);
    usart_baudrate_set(cfg->usart_periph, cfg->baudrate);
    usart_enable(cfg->usart_periph);
}

int uart_drv_send(uint8_t *data, uint16_t len) {
    if (data == NULL || len == 0) return -1;
    for (uint16_t i = 0; i < len; i++) {
        usart_data_transmit(USART0, data[i]);
        while (usart_flag_get(USART0, USART_FLAG_TBE) == RESET);
    }
    return 0;
}
