import datetime
import dateutil.parser
import dateutil.relativedelta
import copy


class FtDate:
    APPROX = "~"
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    def __init__(self, s):
        self.fromString(s)

    def fromString(self, s):
        s = s.strip()
        if s.startswith(self.APPROX):
            self.approx = True
            s = s[1:]
        else:
            self.approx = False

        # Do 2 date conversions to determine what date fields have been specified
        # For the default date fields, pick the year mid-point
        def1 = datetime.datetime(day=15, month=6, year=1)
        self.date = dateutil.parser.parse(s, default = def1)
        
        # For def2, make sure each field is different from self.date
        def2 = self.makeDef2(self.date)
        date2 = dateutil.parser.parse(s, default = def2)

        self.yearDef = (self.date.year == date2.year)
        self.monthDef = (self.date.month == date2.month)
        self.dayDef = (self.date.day == date2.day)
        
        return self

    def makeDef2(self, def1):
        day = month = year = 1
        if def1.day == day:
            day += 1
        if def1.month == month:
            month += 1
        return datetime.datetime(day=day, month=month, year=year)
        
    def toYearString(self):
        dateStr = str(self.date.year)
        if self.approx:
            dateStr = self.APPROX + dateStr
        return dateStr

    def __str__(self):
        if self.approx:
            return self.toYearString()

        # DD MMM YYYY
        s = []
        if self.dayDef:
            s.append(str(self.date.day))
        if self.monthDef:
            s.append(self.MONTHS[self.date.month -1])
        if self.yearDef:
            s.append(str(self.date.year))
        return " ".join(s)

    def __sub__(self, intNum):
        d = copy.deepcopy(self)
        d.date = d.date + dateutil.relativedelta.relativedelta(years=-intNum)
        return d
