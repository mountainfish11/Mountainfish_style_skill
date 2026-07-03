# 代码风格规范

> 存储命名规范、代码格式、注释风格等。
> 条目格式遵循 D8 规范（铁律/指南/参考三级）。

## 铁律（≤5 条，无条件注入）

（待添加：当你项目中有一条"绝对不能违反"的命名/格式规则时，升级到这里）

## 指南（≤20 条，会话启动注入摘要）

### C 函数使用 snake_case 命名  `<!-- tier: guideline -->`

**原则**: C 函数名统一使用 `snake_case`（全小写+下划线），避免 PascalCase/camelCase。

**做法**: 函数名如 `mpu6050_get_raw_acce()`、`motor_set_speed()`。避免 `Mpu6050GetRawAcce()` 或 `mpu6050GetRawAcce()`。

**适用**: `#C #命名 #函数 #代码风格`

<!-- type: convention -->
<!-- tags: C, 命名, 函数 -->
<!-- created: 2026-07-03 -->
<!-- last-applied: 2026-07-03 -->

### #define 常量使用 UPPER_SNAKE_CASE 命名  `<!-- tier: guideline -->`

**原则**: 宏常量（`#define`）使用全大写+下划线命名，区分变量和常量。

**做法**: `#define MOTOR_MAX_SPEED 3000`，避免 `#define motor_max_speed 3000`。函数式宏（带参数的 `#define func(x)`）不受此约束。

**适用**: `#C #命名 #常量 #代码风格`

<!-- type: convention -->
<!-- tags: C, 命名, 常量 -->
<!-- created: 2026-07-03 -->
<!-- last-applied: 2026-07-03 -->

## 参考（无上限，按需检索）

（待添加）
