This quickly hacked together python takes the TXC xml from TFL's time table feed. It then attemtps to build a timetable for every tube journey in London (be patient there are a lot and this wasn't designed to be efficient).

The API then provides the 3 nearest tube stations and the last tubes for each line at that station. Don't trust this data! There are some assumptions, see the code!

When installed try:
http://localhost:5000/get/\<latitude\>/\<longitude\>

or http://localhost:5000/test.html

You should get some JSON like...
    [{'direction': 'N',
      'last': ['00:23:00', "Queen's Park"],
      'line': 'Bakerloo',
      'station': 'Elephant & Castle'},
     {'direction': 'N',
      'last': ['00:26:00', 'High Barnet'],
      'line': 'Northern',
      'station': 'Elephant & Castle'},
     {'direction': 'S',
      'last': ['00:44:00', 'Morden'],
      'line': 'Northern',
      'station': 'Elephant & Castle'},
     {'direction': 'S',
      'last': ['00:40:00', 'Elephant & Castle'],
      'line': 'Bakerloo',
      'station': 'Lambeth North'},
     {'direction': 'N',
      'last': ['00:25:00', "Queen's Park"],
      'line': 'Bakerloo',
      'station': 'Lambeth North'},
     {'direction': 'N',
      'last': ['00:32:00', 'Edgware'],
      'line': 'Northern',
      'station': 'Kennington Station'},
     {'direction': 'S',
      'last': ['00:46:30', 'Morden'],
      'line': 'Northern',
      'station': 'Kennington Station'}]
