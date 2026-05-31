# Битые картинки в блоге — прогресс

Блог: https://blog-archive.arutyunov.info/

**Что считаем проблемой:** внешние URL в `<img src>` внутри тела записи (`e2-note-text`), которые не отдают картинку (в т.ч. `http://` на HTTPS-странице / mixed content в браузере).

**Проверка одной записи:** `python3 scripts/check-post-images.py <url-записи>`

---

## Сводная таблица по записям

Пока проверена **одна** запись (учебная). Остальные — в очереди (`—`).

| Запись | Проверено | Ошибки | Исправлено |
|--------|-----------|--------|------------|
| [vospriyatie — Восприятие](https://blog-archive.arutyunov.info/all/vospriyatie/) | да | да (25 битых, 1 ок) | нет |
| *остальные ~208 записей* | — | — | — |

> Полный список URL для обхода: все `https://blog-archive.arutyunov.info/all/<slug>/`, включая ссылки с главной вида `/?go=all/<slug>/`. Добавлю строки в таблицу по мере проверки.

---

## Детали: записи с найденными проблемами

### Восприятие — https://blog-archive.arutyunov.info/all/vospriyatie/

- Проверено: **да** (2026-05-31)
- Внешних `<img>`: **26**, битых: **25**, рабочих: **1**
- Исправлено: **нет**

| Статус | URL в разметке | Примечание |
|--------|----------------|------------|
| ок | `https://intuition.news/images/principles/principle-img1.svg` | отдаёт 200 |
| битая | `http://bvz.name/img/principles/gestalt1-1.svg` | HTTP 436 / редирект Namecheap, https не отдаёт файл |
| битая | `http://bvz.name/img/principles/gestalt1-2.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-3.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-4.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-4-2.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-5.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-6.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-7.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-8.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-9.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-10.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-11.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt1-12.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt2-1.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt2-2.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt2-3.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt2-4.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt3-1.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt3-4.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt3-5.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt4-1.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt4-2.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt5-1.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt5-2.svg` | то же |
| битая | `http://bvz.name/img/principles/gestalt5-3.svg` | то же |

---

## Почему автоматический обход сначала не видел эту запись

1. Смотрели «первые 10» с ленты / RSS — там нет «Восприятия» (оно закреплено отдельной ссылкой `/?go=all/vospriyatie/`).
2. Regex для `src` требовал закрывающую кавычку; в разметке: `src="http://bvz.name/...svg">` — парсер отрабатывает, но старый вариант — нет.
3. В консоли Chrome это **Mixed Content** (`http://` картинки на `https://` странице) — визуально битые, даже если домен ещё жив.
