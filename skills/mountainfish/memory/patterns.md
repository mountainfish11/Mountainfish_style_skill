# 设计模式和最佳实践

> 存储常用的设计模式、架构决策、最佳实践

## 架构模式

（待添加）

## 设计模式

### 参数传递优于全局变量

**规则**：在嵌入式项目中，优先使用参数传递而非全局变量来共享数据。

**优势**：
1. 封装性更好：函数不依赖外部变量名，更独立
2. 可移植性更强：同一函数可以处理多个实例
3. 可测试性更好：测试时直接传入测试数据，不污染全局状态
4. 复用性更高：函数更通用，可以操作任意实例
5. 线程安全更清晰：参数明确表示函数访问了什么

**好的做法（参数传递）**：
```c
// 定义结构体
static context_pack_t ctx = {
    .wheel_space = MOTOR_WHEEL_SPACING,
    .wheel_perimeter = MOTOR_WHEEL_CIRCLE,
};

// 函数定义带参数
void mpu6050_task(mpu6050_context_t *data) {
    mpu6050_get_raw_acce(data->sensor, &data->curr_acce);
}

void oled_show_task(context_pack_t *ctx) {
    int16_t gyro_z = ctx->mpu6050.curr_gyro.raw_gyro_z;
}

// 调用时传入地址
mpu6050_task(&ctx.mpu6050);
oled_show_task(&ctx);
```

**不推荐的做法（全局变量）**：
```c
// 全局变量
static context_pack_t ctx;

// 函数无参数，直接访问全局变量
void mpu6050_task(void) {
    mpu6050_get_raw_acce(ctx.mpu6050.sensor, &ctx.mpu6050.curr_acce);
}
```

**何时使用全局变量**：
- 真正的"全局"配置（如系统时钟）
- 单例模式（只有一个实例）
- 简单的小程序或原型开发

**何时使用参数传递**：
- 多个任务/函数共享数据
- 需要测试和复用的代码
- 正式的工程项目
- 嵌入式多任务系统

**最小权限原则**：
```c
// 只需要 MPU6050 部分，就只传那部分
mpu6050_task(&ctx.mpu6050);

// 需要访问多个部分，传整个结构体
oled_show_task(&ctx);
wifi_task(&ctx);
```

**适用场景**：
- FreeRTOS 多任务系统
- 嵌入式驱动开发
- 传感器数据采集与处理
- 任何需要数据共享的场景

## 最佳实践

（待添加）

## 示例

```python
# 在此添加体现你偏好的代码示例
```
