---
inclusion: fileMatch
fileMatchPattern: "*.cpp,*.h,*.hpp,*.c"
---

# C/C++ 编码规范

当修改或生成 C/C++ 代码时，遵循以下约束：

## 编译器约束
- C++ 标准：C++11（GCC 4.8.5 兼容）
- 禁止使用 C++14 及以上特性（如 `std::make_unique`、`std::optional`、结构化绑定等）

## 时区处理规范
- 禁止使用 `mktime` / `localtime` 等依赖系统时区的函数
- 时间转换必须使用项目提供的纯数学函数 `change_tm_2_time_t`
- 获取本地时间必须通过 `MultiTimeZone` 模块的 `GetLocalTmByTimeZone` 接口
- 使用 `gmtime` 替代 `localtime`

## AI 代码标注
- 所有 AI 生成的代码块必须使用 `@AI_GENERATED` 标记包裹
- 格式参考 aicodding.md steering 规则
