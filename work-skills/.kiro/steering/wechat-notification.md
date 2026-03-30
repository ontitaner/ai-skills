---
inclusion: manual
---

# 企业微信通知规范

当 Redmine 任务完成（Resolved）后，自动推送通知到企业微信群。

## 通知模板

```
Redmine 任务已完成

任务ID：#<issue_id>
主题：<subject>
类型：<tracker>
状态：Resolved
测试Owner：<test_owner>
修改摘要：<fix_summary>
Wiki：<wiki_url>
```

## 发送方式

通过企业微信群机器人 Webhook 发送 Markdown 格式消息。

Webhook URL：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=91e5af55-b3a0-44a9-a3ac-7e1b364c296f`

注意：远程服务器无法访问外网，需通过本地 PowerShell 的 `Invoke-RestMethod` 发送，不能用 SSH curl。

## 字段说明

| 字段 | 来源 |
|------|------|
| issue_id | Redmine Issue ID |
| subject | Redmine Issue 主题 |
| tracker | Redmine Issue 跟踪器（Bug/Feature/Task） |
| test_owner | Redmine Issue 自定义字段或指派人 |
| fix_summary | 代码修改摘要（由 AI 生成） |
| wiki_url | Confluence Wiki 分析文档链接 |
