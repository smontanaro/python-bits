#
# CSV 0.17  8 June 1999    Copyright ©Laurence Tratt 1998 - 1999
# e-mail: tratt@dcs.kcl.ac.uk
# home-page: http://eh.org/~laurie/comp/python/csv/index.html
#
#
#
# CSV.py is copyright ©1998 - 1999 by Laurence Tratt
#
# All rights reserved
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted, provided that
# the above copyright notice appear in all copies and that both that copyright
# notice and this permission notice appear in supporting documentation.
#
# THE AUTHOR - LAURENCE TRATT - DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS
# SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN
# NO EVENT SHALL THE AUTHOR FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
# AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTUOUS ACTION, ARISING OUT OF OR
# IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

# Changes:
# 6/19/00 - skip@mojam.com - raise KeyError if named column title doesn't exist
# 6/16/00 - skip@mojam.com - reindented to use four space indents and wrapped
#                            lines to less than 80 columns
# 6/16/00 - skip@mojam.com - fixed bug in parsing of embedded quotes
# 6/16/00 - skip@mojam.com - renamed methods containing embedded __ to use
#                            just a single underscore
# 6/16/00 - skip@mojam.com - fixed output of titles to avoid blank line
# ???     - skip@mojam.com - pulled line__make out of output method

import re, string, types, UserList


####################################################################################
#
# CSV class
#


class CSV(UserList.UserList):

    """ Manage a CSV (comma separated values) file

    The data is held in a list.

    Methods:
        __init__()
        load()    load from file
        save()    save to file
        input()   input from string
        output()  save to string
        append()  appends one entry
        __str__() printable represenation
    """



    def __init__(self, separator = ','):

        """ Initialise CVS class instance.

        Arguments:
        separator    : The field delimiter. Defaults to ','
        """

        self.separator = separator

        self.data = []
        self.fields_title_have = self.fields_title = None



    def load(self, file_data_name, fields_title_have,
             convert_numbers=0, separator=None, comments=None):

        """ Load up a CSV file

        Arguments:
            file_data_name                : The name of the CSV file
            fields_title_have : 0         : file has no title fields
                                otherwise : file has title fields
            convert_numbers   : 0         : store everything as string's
                                otherwise : store fields that can be converted
                                            to ints or floats to that Python
                                            type defaults to 0
            separator                     : The field delimiter (optional)
            comments                      : A list of strings and regular expressions
                                            to remove comments
        """

        file_data = open(file_data_name, 'r')
        self.input(file_data.read(-1), fields_title_have, convert_numbers,
                   separator or self.separator, comments or ["#"])
        file_data.close()



    def save(self, file_data_name, separator = None, quote = 0,
         quote_numbers = 0):

        """ Save data to CSV file.

        Arguments:
            file_data_name : The name of the CSV file to save to
            separator      : The field delimiter (optional)
        """

        file_data = open(file_data_name, 'w')
        file_data.write(self.output(separator,quote,quote_numbers))
        file_data.close()



    def input(self, data, fields_title_have,
              convert_numbers=0, separator=None, comments=None):

        """ Take wodge of CSV data & convert it into internal format.

        Arguments:
            data                          : A string containing the CSV data
            fields_title_have : 0         : file has no title fields
                                otherwise : file has title fields
            convert_numbers   : 0         : store everything as string's
                                otherwise : store fields that can be
                                            converted to ints or
                                            floats to that Python type
                                            defaults to 0
            separator                     : The field delimiter (Optional)
            comments                      : A list of strings and regular expressions
                                            to remove comments (defaults to ['#'])
        """

        def line_process(line, convert_numbers, separator):

            fields = []
            line_pos = 0

            while line_pos < len(line):

                # Skip any space at the beginning of the field (if there
                # should be leading space, there should be a quotation mark
                # in the CSV file)

                while line_pos < len(line) and line[line_pos] == " ":
                    line_pos = line_pos + 1

                field = ""
                quotes_level = 0
                llen = len(line)
                while line_pos < llen:

                    # Skip space at the end of a field (if there is trailing
                    # space, it should be enclosed in quotation marks)

                    if quotes_level == 0 and line[line_pos] == " ":
                        line_pos_temp = line_pos
                        while line_pos_temp < llen and line[line_pos_temp] == " ":
                            line_pos_temp = line_pos_temp + 1
                        if line_pos_temp >= len(line):
                            break
                        elif line[line_pos_temp:line_pos_temp+len(separator)]==separator:
                            line_pos = line_pos_temp
                    if (quotes_level == 0 and
                        line[line_pos:line_pos+len(separator)]==separator):
                        break
                    elif line[line_pos] == '"':
                        if quotes_level == 0:
                            quotes_level = 1
                        elif line_pos+1 < llen and line[line_pos+1] == '"':
                            # found a doubled quote mark - save a single quote
                            field = field + '"'
                            line_pos = line_pos + 1
                        else:
                            quotes_level = 0
                    else:
                        field = field + line[line_pos]
                    line_pos = line_pos + 1
                line_pos = line_pos + len(separator)
                if convert_numbers:
                    for char in field:
                        if char not in "0123456789.-":
                            fields.append(field)
                            break
                    else:
                        try:
                            if "." not in field:
                                fields.append(int(field))
                            else:
                                fields.append(float(field))
                        except:
                            fields.append(field)
                else:
                    fields.append(field)
            if line[-len(separator)] == separator:
                fields.append(field)

            return fields


        separator = separator or self.separator
        comments = comments or ["#"]

        self.fields_title_have = fields_title_have

        # Remove comments from the input file

        comments_strings = []
        for comment in comments:
            if type(comment) == types.InstanceType:
                data = comment.sub("", data)
            elif type(comment) == types.StringType:
                comments_strings.append(comment)
            else:
                raise Exception("Invalid comment type '" + comment + "'")

        lines = map(string.strip, re.split("[\r\n]+", data))

        # Remove all comments that are of type string

        lines_pos = 0
        while lines_pos < len(lines):
            line = lines[lines_pos]
            line_pos = 0
            while line_pos < len(line) and line[line_pos] == " ":
                line_pos = line_pos + 1
            found_comment = 0
            for comment in comments_strings:
                if (line_pos + len(comment) < len(line) and
                    line[line_pos:line_pos+len(comment)] == comment):
                    found_comment = 1
                    break
            if found_comment:
                del lines[lines_pos]
            else:
                lines_pos = lines_pos + 1

        # Process the input data

        if fields_title_have:
            self.fields_title = line_process(lines[0], convert_numbers, separator)
            pos_start = 1
        else:
            self.fields_title = []
            pos_start = 0
        self.data = []
        for line in lines[pos_start : ]:
            if line != "":
                self.data.append(Entry(line_process(line, convert_numbers, separator),
                                       self.fields_title))


    def line_make(self, entry, separator = None,
           quote = 0, quote_numbers = 0):

        separator = separator or self.separator

        out = []
        done_any = 0
        for field in entry:
            if done_any:
                out.append(separator)
            else:
                done_any = 1
            tf = type(field)
            if type(field) != types.StringType:
                field = `field`
            # quote if directed or the field contains
            # the separator character or leading or
            # trailing whitespace
            if (quote or len(field) > 0 and
                (string.find(field, separator) != -1 or
                 (field[0] == " " or
                  field[-1] == " "))):
                if '"' in field:
                    field = string.replace(field,
                               '"',
                               '""')
                # quote numbers if directed
                if (tf == types.IntType or
                    tf == types.FloatType):
                    if quote_numbers:
                        out.append('"')
                    out.append(field)
                    if quote_numbers:
                        out.append('"')
                else:
                    out.append('"')
                    out.append(field)
                    out.append('"')
            else:
                out.append(field)

        return "%s\n" % string.join(out, "")


    def output(self, separator = None, quote = 0, quote_numbers = 0):

        """ Convert internal data into CSV string.

        Arguments:
            separator     : The field delimiter (optional)
            quote         : Whether to quote fields
            quote_numbers : If quoting, whether to quote numbers as well
        Returns:
            String containing CSV data
        """

        separator = separator or self.separator


        out = []

        if self.fields_title_have:
            out.append(self.line_make(self.fields_title,
                       separator, quote,
                       quote_numbers))

        for item in self.data:
            out.append(self.line_make(item, separator,
                       quote, quote_numbers))

        return string.join(out, "")



    def append(self, entry):

        """ Add an entry. """

        if self.fields_title:
            entry.fields_title = self.fields_title
        self.data.append(entry)



    def field_append(self, func, field_title = None):

        """ Append a field with values specified by a function

        Arguments:
            func        : Function to be called func(entry) to get the value of
                          the new field
            field_title : Name of new field (if applicable)
        """

        for data_pos in range(len(self)):
            entry = self.data[data_pos]
            entry.append(func(entry))
            self.data[data_pos] = entry

        if self.fields_title_have:
            self.fields_title.append(field_title)



    def duplicates_eliminate(self):

        """ Eliminate duplicates (this may result in a reordering of the entries) """

        # To eliminate duplicates, we first get Python to sort the list for us;
        # then all we have to do is to check to see whether consecutive elements are
        # the same, and delete them
        # This give us O(<sort>) + O(n) rather than the more obvious O(n * n) speed
        # algorithm

        # XXX Could be done more efficiently for multiple duplicates by deleting a
        # slice of similar elements rather than deleting them individually

        self.sort()
        data_pos = 1
        entry_last = self.data[0]
        while data_pos < len(self.data):
            if self.data[data_pos] == entry_last:
                del self.data[data_pos]
            else:
                entry_last = self.data[data_pos]
                data_pos = data_pos + 1



    def __str__(self):

        """ Construct a printable representation of the internal data. """

        columns_width = []

        # Work out the maximum width of each column

        for column in range(len(self.data[0])):
            if self.fields_title_have:
                width = len(`self.fields_title[column]`)
            else:
                width = 0
            for entry in self:
                width_possible = len(`entry.data[column]`)
                if width_possible > width:
                    width = width_possible
            columns_width.append(width)

        if self.fields_title_have:
            out = (string.join(map(string.ljust, self.fields_title, columns_width), "  ")
                   + "\n\n")
        else:
            out = ""
        for entry in self:
            out = (out +
                   string.join(map(string.ljust,
                                   map(lambda a:(type(a)==types.StringType and
                                                 [a] or [eval("`a`")])[0],
                                       entry.data), columns_width), "  ") + "\n")

        return out



#####################################################################################
#
# CSV data entry class
#
#


class Entry(UserList.UserList):

    """ CSV data entry, UserList subclass.

    Has the same properties as a list, but has a few dictionary
    like properties for easy access of fields if they have titles.

    Methods(Override):
        __init__
        __getitem__
        __setitem__
        __delitem__
    """



    def __init__(self, fields, fields_title = None):

        """ Initialise with fields data and field title.

        Arguments:
            fields       : a list containing the data for each field of this entry
            fields_title : a list with the titles of each field
                           (an empty list means there are no titles)
        """

        self.data = fields
        if fields_title != None:
            self.fields_title = fields_title
        else:
            self.fields_title = []



    def __getitem__(self, x):

        if type(x) == types.IntType:
            return self.data[x]
        else:
            try:
                return self.data[self.fields_title.index(x)]
            except IndexError:
                raise KeyError, "No column title named '%s'" % x



    def get(self, x, default=""):

        try:
            return self[x]
        except (ValueError, KeyError):
            return default


        
    def __setitem__(self, x, item):

        if type(x) == types.IntType:
            self.data[x] = item
        else:
            self.data[self.fields_title.index(x)] = item



    def __delitem__(self, x):

        if type(x) == types.IntType:
            del self.data[x]
        else:
            del self.data[self.fields_title.index(x)]



    def __str__(self):

        return `self.data`
