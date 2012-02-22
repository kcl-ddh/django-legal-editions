# $Id: core.py 677 2012-01-12 17:46:11Z gnoel $
import datetime
import calendar
import re
from enum import Enum

modifiers = Enum()
modifiers.addElement('DEFAULT', {'symbol': ''})
modifiers.addElement('CIRCA', {'symbol': 'c. '})
modifiers.addElement('UNCERTAIN', {'symbol': '?'})

# date1 <= date <= date2 
# represents an approximate date into an inclusive date range
# Please run the regression test after modifying the code to make sure it is bug-free
# See tester.py
#
# Todo:
#    comparison
#    support 196* or 12** format
#    notes
#    before X
#    after X
#    BC
#    less than 4 digits for the year
#
class FuzzyDate(object):
    dates = [datetime.date.today(), datetime.date.today()]
    modifier = modifiers.DEFAULT
    lastError = u''
    # if False the format is iso-8109
    ukFormat = True
    
    def isUndefined(self):
        return (self.dates[0] == None)

    # day, month and year fields are required by django to display the field on the list screen
    def _getMonth(self):
        ret = self.getDateFrom()
        if ret == None:
            return 1
        return ret.month
        
    month = property(_getMonth)
    
    def _getDay(self):
        ret = self.getDateFrom()
        if ret == None:
            return 1
        return ret.day
        
    day = property(_getDay)

    def _getYear(self):
        ret = self.getDateFrom()
        if ret == None:
            return 2050
        return ret.year
        
    year = property(_getYear)

    def __new__(cls, date_from=None, date_to=None, modifier=modifiers.DEFAULT):
        self = object.__new__(cls)
        self.modifier = modifier
        if (date_from == None):
            date_from = datetime.date.today()
        if (date_to == None):
            date_to = date_from
        self.dates = [date_from, date_to]
        return self
    
    def getDateTo(self):
        return self.dates[1]
        
    def getDateFrom(self):
        return self.dates[0]
    
    def getModifier(self):
        return self.modifier
    
    def setModifier(self, modifier):
        self.modifer = modifier
    
    def setAsString(self, datestr):
        if (datestr == None or datestr == ''): 
            self.dates[0] = None
            self.dates[1] = None
            return True
        # trim left and right
        datestr = re.sub(r'(^\s*)|(\s*$)', '', datestr)
        self.modifier = modifiers.DEFAULT
        # get the modifier
        if (re.search(r'^c\.', datestr)):
            datestr = re.sub(r'^c\.\s*', '', datestr)
            self.modifier = modifiers.CIRCA
        if (re.search(r'^\?\s*', datestr)):
            datestr = re.sub(r'^\?\s*', '', datestr)
            self.modifier = modifiers.UNCERTAIN
        # split the range: '-' or 'to'
        dates = re.split('\s+to\s+|\s+-\s+|\s*,\s+|\s+', datestr)
        if (not(len(dates) in (1, 2))):
            return self.setLastError('invalid date format')
        # validate each date in the range
        for date in dates:
            if (not self.isFormatValid(date)):
                return self.setLastError('invalid date format')
        # expand both dates (express them with the month and day)
        try:
            if (len(dates) == 2):
                dates[1] = self.getMaxDateFromStr(dates[1])
            else:
                dates.append(self.getMaxDateFromStr(dates[0]))
            dates[0] = self.getMinDateFromStr(dates[0])
        except ValueError, e:
            self.setLastError(e.__str__())
            return False
            
        self.dates = dates
        
        return True
    
    def setLastError(self, message):
        self.lastError = message
        return len(message) == 0
    
    def getLastError(self):
        return self.lastError
    
    def __repr__(self):
        # only used for showing internal representation of the object
        if (self.dates[0] == None): return repr(self.dates[0])
        format = 'ISO'
        if self.ukFormat: format = 'UK'
        return "%s[%s, %s] (%s)" % (self.modifier.symbol, self.dates[0], self.dates[1], format)
    
    def __str__(self):
        # important to define this function as it is used by django to display the date in the admin
        return self.getAsString()
    
    def __unicode__(self):
        # important to define this function as it is used by django to display the date in the admin
        return self.getAsString()

    def getAsString(self, simplified_dates=None):
        if self.dates[0] == None: return ''
        dates = []
        # 1. reduce each date
        for date in self.dates:
            # reduce each end of the interval
            # remove the day, the month if they correspond to the beginning/end of a month or a year
            adate = date.__str__()
            while True:
                reduced_date = re.sub(r'-\d+$', '', adate)
                if (reduced_date == adate or # ??? 
                    (len(dates) == 0 and self.getMinDateFromStr(reduced_date, False) != date) or 
                    (len(dates) == 1 and self.getMaxDateFromStr(reduced_date, False) != date)):
                    break
                adate = reduced_date
            dates.append(adate)
        # 2. reduce both dates to the same unit of time
        # if date[0]=2009 and date[1]=2009-11 then chop = 1
        chop = 2 - max(dates[0].count('-'), dates[1].count('-'))
        dates = [self.dates[0].__str__(), self.dates[1].__str__()]
        while chop:
            for i in (0, 1):
                dates[i] = re.sub(r'-\d+$', '', dates[i])
            chop = chop - 1
        # 3. simplification if both dates are identical
        if (self.ukFormat):
            for i in (0, 1):
                dates[i] = self.reverseDateFormat(dates[i])
        if simplified_dates is not None: simplified_dates.append(dates[0])
        if (dates[0] == dates[1]): 
            return "%s%s" % (self.modifier.symbol, dates[0])
        else:
            if simplified_dates is not None: simplified_dates.append(dates[1]) 
            return "%s%s to %s" % (self.modifier.symbol, dates[0], dates[1])
    
    # 2009 -> 2009-01-01
    def getMinDateFromStr(self, datestr, ukFormat=None):
        ''' datestr:    a string representing a date in ISO-8601
            return :    a datetime object
        '''
        date = re.split('[/-]', datestr)
        # converts the date from uk to iso
        if ukFormat is None: ukFormat = self.ukFormat
        if (ukFormat): date.reverse()
        while (len(date) < 3):
            date.append('01')
        self.raiseErrorIfDateNotValid(int(date[0]), int(date[1]), int(date[2]))
        ret = datetime.date(int(date[0]), int(date[1]), int(date[2]))
        return ret
        
    # 2009 -> 2009-12-31
    def getMaxDateFromStr(self, datestr, ukFormat=None):
        ''' datestr:    a string representing a date
            return :    a datetime object
        '''
        date = re.split('[/-]', datestr)
        # converts the date from uk to iso
        if ukFormat is None: ukFormat = self.ukFormat
        if (ukFormat): date.reverse()
        if (len(date) == 1):
            date.append(12)
        if (len(date) == 2):
            self.raiseErrorIfDateNotValid(int(date[0]), int(date[1]), 1)
            date.append(calendar.monthrange(int(date[0]), int(date[1]))[1])
        self.raiseErrorIfDateNotValid(int(date[0]), int(date[1]), int(date[2]))
        ret = datetime.date(int(date[0]), int(date[1]), int(date[2]))
        return ret

    def raiseErrorIfDateNotValid(self, year, month, day):
        datetime.date(year, month, day)
    
    def isFormatValid(self, datestr):
        if (self.ukFormat):
            return re.match('^(\d{1,2}[/-]){0,1}(\d{1,2}[/-]){0,1}(\d{1,4})$', datestr)
        else:
            return re.match('^(\d{1,4})([/-]\d{1,2}){0,1}([/-]\d{1,2}){0,1}$', datestr)
    
    def reverseDateFormat(self, datestr):
        ''' returns a 'the uk format from iso and vice versa'''
        date = re.split('[/-]', datestr)
        for i in range(len(date)):
            date[i] = re.sub('^0+', '', date[i])
            if date[i] == '': date[i] = '0'
        date.reverse()
        return '-'.join(date)

    def getWebFormat(self):
        import re
        # 31-12-2010 -> 21 December 2010
        dates = []
        month_name = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        ret = self.getAsString(dates)
        for i in range(0, len(dates)):
            d_parts = re.split('[/-]', dates[i])
            if len(d_parts) > 1: d_parts[len(d_parts) - 2] = month_name[int(d_parts[len(d_parts) - 2]) - 1]
            if len(d_parts) == 3: d_parts[0] = '%d' % int(d_parts[0])
            dates[i] = ' '.join(d_parts)
        # special cases
        if len(dates) == 2: 
            if self.modifier == modifiers.UNCERTAIN:
                ret = 'sometime between %s and %s' % (dates[0], dates[1])
            elif self.modifier == modifiers.CIRCA:
                ret = 'from c. %s to c. %s' % (dates[0], dates[1])
            else:
                ret = 'from %s to %s' % (dates[0], dates[1])
        else:
            if self.modifier == modifiers.CIRCA:
                ret = 'c. ' + dates[0]
            elif self.modifier == modifiers.UNCERTAIN:
                ret = '?' + dates[0]
            else:
                ret = dates[0]
            
        return ret

    def getShortWebFormat(self):
        # Only keep the year: 31-12-2010 -> 2010
        # Compact and generic format for date ranges: (?)31-12-2010 - 31-12-2020 -> 2010-2020
        if self.isUndefined():
            return u'?'
        date = [self.getDateFrom().year, self.getDateTo().year]
        if date[0] == date[1]:
            ret = u'%s' % date[0]
        else:
            ret = u'%s-%s' % (date[0], date[1])
        if self.modifier == modifiers.CIRCA:
            ret = u'c.%s' % ret
        return ret

#    from ootw.cch.fuzzydate.core import FuzzyDate
#    if date is not None:
#        if date.__class__.__name__ == 'FuzzyDate' and date.getDateTo() is not None:
#            return u'%s' % date.getDateTo().year
#        return date
#    return '?'

# FORMATTING FUZZY DATES CORRECTLY IN THE ADMIN INTERFACE
from django.utils import dateformat

def dateformat_format(value, format_string):
    ''' Another nasty hack to work around rigidity in Django's design.
        Problem: FuzzyDate Fields (extends from DateField) are represented as 1st Jan 1970 on the change list view. When the value actually is '1970'
        The reason for this issue is found in admin_list.py:items_for_result() which is called to format the fields
            of all the records in the result set.
        This method calls django.utils.dateformat.format() to format the field and therefore only takes the start of the date range.
        The solution is to override this method, detect the FuzzyDates and delegate their representation.
        TODO: Note that this solution is not perfect as we should actually format the FuzzyDate according to the desired syntax (e.g. Month in letters, etc) 
    '''
    if value is not None and isinstance(value, FuzzyDate):
        return value.getAsString()
    else:
        df = dateformat.DateFormat(value)
        return df.format(format_string)

dateformat.format = dateformat_format
