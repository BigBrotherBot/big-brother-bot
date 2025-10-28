# Excerpt from pstats.py rev 1.0  4/1/94 (from python v2.6) which define this class only when it's the entry point (main), so it is here copied to avoid compatibility issues with the next python's releases.

from __future__ import absolute_import
from __future__ import print_function
from pstats import *

import cmd
import six
from six.moves import filter
try:
    import readline
except ImportError:
    pass

class ProfileBrowser(cmd.Cmd):
    def __init__(self, profile=None):
        cmd.Cmd.__init__(self)
        self.prompt = "% "
        if profile is not None:
            self.stats = Stats(profile)
            self.stream = self.stats.stream
        else:
            self.stats = None
            self.stream = sys.stdout

    def generic(self, fn, line):
        args = line.split()
        processed = []
        for term in args:
            try:
                processed.append(int(term))
                continue
            except ValueError:
                pass
            try:
                frac = float(term)
                if frac > 1 or frac < 0:
                    print("Fraction argument must be in [0, 1]", file=self.stream)
                    continue
                processed.append(frac)
                continue
            except ValueError:
                pass
            processed.append(term)
        if self.stats:
            getattr(self.stats, fn)(*processed)
        else:
            print("No statistics object is loaded.", file=self.stream)
        return 0
    def generic_help(self):
        print("Arguments may be:", file=self.stream)
        print("* An integer maximum number of entries to print.", file=self.stream)
        print("* A decimal fractional number between 0 and 1, controlling", file=self.stream)
        print("  what fraction of selected entries to print.", file=self.stream)
        print("* A regular expression; only entries with function names", file=self.stream)
        print("  that match it are printed.", file=self.stream)

    def do_add(self, line):
        self.stats.add(line)
        return 0
    def help_add(self):
        print("Add profile info from given file to current statistics object.", file=self.stream)

    def do_callees(self, line):
        return self.generic('print_callees', line)
    def help_callees(self):
        print("Print callees statistics from the current stat object.", file=self.stream)
        self.generic_help()

    def do_callers(self, line):
        return self.generic('print_callers', line)
    def help_callers(self):
        print("Print callers statistics from the current stat object.", file=self.stream)
        self.generic_help()

    def do_EOF(self, line):
        print("", file=self.stream)
        return 1
    def help_EOF(self):
        print("Leave the profile brower.", file=self.stream)

    def do_quit(self, line):
        return 1
    def help_quit(self):
        print("Leave the profile brower.", file=self.stream)

    def do_read(self, line):
        if line:
            try:
                self.stats = Stats(line)
            except IOError as args:
                print(args[1], file=self.stream)
                return
            self.prompt = line + "% "
        elif len(self.prompt) > 2:
            line = self.prompt[-2:]
        else:
            print("No statistics object is current -- cannot reload.", file=self.stream)
        return 0
    def help_read(self):
        print("Read in profile data from a specified file.", file=self.stream)

    def do_reverse(self, line):
        self.stats.reverse_order()
        return 0
    def help_reverse(self):
        print("Reverse the sort order of the profiling report.", file=self.stream)

    def do_sort(self, line):
        abbrevs = self.stats.get_sort_arg_defs()
        if line and not list(filter(lambda x,a=abbrevs: x not in a,line.split())):
            self.stats.sort_stats(*line.split())
        else:
            print("Valid sort keys (unique prefixes are accepted):", file=self.stream)
            for (key, value) in six.iteritems(Stats.sort_arg_dict_default):
                print("%s -- %s" % (key, value[1]), file=self.stream)
        return 0
    def help_sort(self):
        print("Sort profile data according to specified keys.", file=self.stream)
        print("(Typing `sort' without arguments lists valid keys.)", file=self.stream)
    def complete_sort(self, text, *args):
        return [a for a in Stats.sort_arg_dict_default if a.startswith(text)]

    def do_stats(self, line):
        return self.generic('print_stats', line)
    def help_stats(self):
        print("Print statistics from the current stat object.", file=self.stream)
        self.generic_help()

    def do_strip(self, line):
        self.stats.strip_dirs()
        return 0
    def help_strip(self):
        print("Strip leading path information from filenames in the report.", file=self.stream)

    def postcmd(self, stop, line):
        if stop:
            return stop
        return None