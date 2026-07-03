# 设计模式和最佳实践

> 存储常用的设计模式、架构决策、最佳实践。
> 条目格式遵循 D8 规范（铁律/指南/参考三级）。

## 铁律（≤5 条，无条件注入）

（待添加）

## 指南（≤20 条，会话启动注入摘要）

### 参数传递优于全局变量  `<!-- tier: guideline -->`

**原则**: 在嵌入式多任务系统中，使用参数传递而非全局变量来共享数据。

**做法**: 定义结构体作为上下文容器，每个任务函数接收自己需要的部分（最小权限原则），通过指针传递而非直接访问全局变量。

```c
// 好的做法：参数传递
static context_pack_t ctx = {
    .wheel_space = MOTOR_WHEEL_SPACING,
    .wheel_perimeter = MOTOR_WHEEL_CIRCLE,
};

void mpu6050_task(mpu6050_context_t *data) {
    mpu6050_get_raw_acce(data->sensor, &data->curr_acce);
}

// 调用
mpu6050_task(&ctx.mpu6050);
```

**适用**: `#C #嵌入式 #FreeRTOS #架构 #多任务`

<!-- type: pattern -->
<!-- created: 2026-07-03 -->
<!-- last-applied: 2026-07-03 -->

## 参考（无上限，按需检索）

（待添加）
