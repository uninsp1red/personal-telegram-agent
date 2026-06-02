# Database Schema

## DBML

```dbml
Table users {
  id integer [primary key]
  telegram_id bigint [unique, not null]
  username varchar
  created_at timestamp
}

Table tasks {
  task_id integer [primary key]
  user_id integer [ref: > users.id]
  task_name varchar
  task_description text
  status varchar [note: 'pending/done/skipped']
  deadline timestamp
  created_at timestamp
}

Table message_schedule {
  id integer [primary key]
  user_id integer [ref: > users.id]
  task_id integer [ref: > tasks.task_id]
  title varchar
  description text
  status varchar [note: 'pending/sent/cancelled']
  time_to_send timestamp
}

Table receipts {
  id integer [primary key]
  user_id integer [ref: > users.id]
  raw_text text
  created_at timestamp
}

Table spendings {
  id integer [primary key]
  user_id integer [ref: > users.id]
  receipt_id integer [ref: > receipts.id]
  spending_name varchar
  spending_category varchar
  amount numeric
  created_at timestamp
}

Table conversation_history {
  id integer [primary key]
  user_id integer [ref: > users.id]
  role varchar [note: 'user/assistant']
  content text
  created_at timestamp
}
```

## Tables

- **users** — пользователи бота
- **tasks** — задачи с дедлайнами
- **message_schedule** — запланированные напоминания
- **receipts** — сырые данные чеков
- **spendings** — расходы
- **conversation_history** — память агента