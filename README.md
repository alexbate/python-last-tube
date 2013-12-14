This quickly hacked together python takes the TXC xml from TFL's time table feed. It then attemtps to build a timetable for every tube journey in London (be patient there are a lot and this wasn't designed to be efficient).

The API then provides the 3 nearest tube stations and the last tubes for each line at that station. Don't trust this data! There are some assumptions, see the code!

When installed try:
http://localhost:5000/get/\<latitude\>/\<longitude\>
or http://localhost:5000/test.html
