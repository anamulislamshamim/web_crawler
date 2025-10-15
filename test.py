from datetime import datetime, timezone, timedelta

today = datetime.now(timezone.utc).date()
start = datetime.combine(today, datetime.min.time())
end = datetime.combine(today + timedelta(days=1), datetime.min.time())

print(today)
print(start)
print(end)