/* Ring Buffer Utility */
#ifndef RINGBUF_H
#define RINGBUF_H

#include <stdint.h>
#include <stdbool.h>

typedef struct {
    uint8_t *buffer;
    uint16_t capacity;
    uint16_t head;
    uint16_t tail;
    volatile uint8_t ready;
} ringbuf_t;

void ringbuf_init(ringbuf_t *rb, uint16_t capacity);
bool ringbuf_put(ringbuf_t *rb, uint8_t byte);
bool ringbuf_get(ringbuf_t *rb, uint8_t *byte);
uint16_t ringbuf_available(ringbuf_t *rb);

#endif /* RINGBUF_H */
