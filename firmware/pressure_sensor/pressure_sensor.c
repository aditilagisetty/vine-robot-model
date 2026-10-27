#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include <stdlib.h>
#define OFFSET_SAMPLES 101

// bus = pointer to the I2C hardware on pi
// addr = I2C address

typedef struct
{
    i2c_inst_t *controller; // which controller? i2c0 or i2c1
    uint8_t addr;           // i2c address
    uint8_t mux_channel;    // which multiplexer output (for later)
    float p_min;            // minimum pressure; 1638 counts
    float p_max;            // maximum pressure; 14745 counts
    float offset;           // zero offset, measured @ startup
} pressure_sensor_t;

// creates a pressure sensor struct for the test sensor
pressure_sensor_t test_sensor = {
    .controller = i2c0,
    .addr = 0x28,
    .mux_channel = 0,
    .p_min = 0.0f,
    .p_max = 5.0f,
    .offset = 0.0f,
};

bool read_raw_count(const pressure_sensor_t *sensor, uint16_t *count)
{

    uint8_t buf[2];

    // Ask the sensor for 2 bytes; give up after 10 ms. put data into array buf
    int result = i2c_read_timeout_us(sensor->controller, sensor->addr, buf, 2, false, 10000);
    if (result != 2)
    {
        return false;
    }

    // Shift right 6: throws out the 6 pressure bits on the right,
    // leaving only the 2 status bits. e.g. 0000 0110 -> 0000 0000
    // status 00 = fresh, valid data
    uint8_t status = buf[0] >> 6;

    if (status != 0)
    {
        return false;
    }

    // used to remove status bits from the full num
    const uint8_t mask = 0x3F;

    // shifts the first 8 bits to the front; uses or to place second 8 bits
    *count = ((mask & buf[0]) << 8) | buf[1];

    return true;
}

int compare(const void *a, const void *b)
{
    uint16_t x = *(const uint16_t *)a;
    uint16_t y = *(const uint16_t *)b;
    return (int)x - (int)y;
}

bool offset_calc(const pressure_sensor_t *sensor, float *offset_amount)
{

    // result num
    uint16_t pressure_num;
    // num that only increments if data is good
    int good = 0;

    float median;

    // array of all result nums
    uint16_t pressure_num_list[OFFSET_SAMPLES];

    for (int i = 0; i < OFFSET_SAMPLES; i++)
    {
        // checks to see if read_pressure returned a value, if it did add it to the num_list
        if (read_raw_count(sensor, &pressure_num))
        {
            pressure_num_list[good] = pressure_num;
            good++;
        }
        else
        {
            printf("Reading Failed\n");
        }
        sleep_ms(10);
    }

    if (good < OFFSET_SAMPLES / 2)
    {
        printf("Too many failed readings\n");
        return false;
    }

    qsort(pressure_num_list, good, sizeof(uint16_t), compare);
    if (good % 2 == 0)
    {
        median = (pressure_num_list[good / 2 - 1] + pressure_num_list[good / 2]) / 2.0;
    }
    else
    {
        median = pressure_num_list[good / 2];
    }

    *offset_amount = median;

    return true;
}

float transfer_func(float offset_amount, uint16_t counts)
{

    float output = (float)counts;
    float pressure = ((output - offset_amount) / 13107.0f) * 5.0f + 0.0f;

    return pressure;
}

bool get_pressure(const pressure_sensor_t *sensor, float *pressure)
{
    uint16_t raw_count = 0;
    if (read_raw_count(sensor, &raw_count))
    {
        *pressure = transfer_func(sensor->offset, raw_count);
        return true;
    }
    else
    {
        printf("Can't get pressure \n");
        return false;
    }
}

int main(void)
{
    stdio_init_all();

    // Set up I2C0 at 100 kHz on GP4 (SDA) and GP5 (SCL)
    i2c_init(i2c0, 100 * 1000);
    gpio_set_function(4, GPIO_FUNC_I2C);
    gpio_set_function(5, GPIO_FUNC_I2C);

    sleep_ms(2000);

    offset_calc(&test_sensor, &test_sensor.offset);

    float pressure = 0;

    while (true)
    {

        if (get_pressure(&test_sensor, &pressure))
        {
            printf(">pressure:%.3f\n", pressure);
        }

        sleep_ms(100);
    }
}