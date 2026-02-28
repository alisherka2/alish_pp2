import datetime

# Get 5 days ago date
x= datetime.datetime.now()-datetime.timedelta(days=5)
print(x.strftime("%d-%m-%Y"))

# Get yesterday, today and tomorrow's date
x = datetime.datetime.now()
yesterday = x - datetime.timedelta(days=1)
tomorrow = x + datetime.timedelta(days=1)
print(yesterday.strftime("%d-%m-%Y"), x.strftime("%d-%m-%Y"), tomorrow.strftime("%d-%m-%Y"))

# Get date without microseconds
x = datetime.datetime.now()
print(x.replace(microsecond=0))

# Get the difference of two dates in seconds
a= datetime.datetime.now()
b= datetime.datetime(2020, 5, 17)
c=a-b
print(c.total_seconds())