# Excerpt from pstats.py rev 1.0  4/1/94 (from python v2.6) which define this class only when it's the entry point (main), so it is here copied to avoid compatibility issues with the next python's releases.

from pstats import *

import cmd
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
                    print >> self.stream, "Fraction argument must be in [0, 1]"
                    continue
                processed.append(frac)
                continue
            except ValueError:
                pass
            processed.append(term)
        if self.stats:
            getattr(self.stats, fn)(*processed)
        else:
            print >> self.stream, "No statistics object is loaded."
        return 0
    def generic_help(self):
        print >> self.stream, "Arguments may be:"
        print >> self.stream, "* An integer maximum number of entries to print."
        print >> self.stream, "* A decimal fractional number between 0 and 1, controlling"
        print >> self.stream, "  what fraction of selected entries to print."
        print >> self.stream, "* A regular expression; only entries with function names"
        print >> self.stream, "  that match it are printed."

    def do_add(self, line):
        self.stats.add(line)
        return 0
    def help_add(self):
        print >> self.stream, "Add profile info from given file to current statistics object."

    def do_callees(self, line):
        return self.generic('print_callees', line)
    def help_callees(self):
        print >> self.stream, "Print callees statistics from the current stat object."
        self.generic_help()

    def do_callers(self, line):
        return self.generic('print_callers', line)
    def help_callers(self):
        print >> self.stream, "Print callers statistics from the current stat object."
        self.generic_help()

    def do_EOF(self, line):
        print >> self.stream, ""
        return 1
    def help_EOF(self):
        print >> self.stream, "Leave the profile brower."

    def do_quit(self, line):
        return 1
    def help_quit(self):
        print >> self.stream, "Leave the profile brower."

    def do_read(self, line):
        if line:
            try:
                self.stats = Stats(line)
            except IOError, args:
                print >> self.stream, args[1]
                return
            self.prompt = line + "% "
        elif len(self.prompt) > 2:
            line = self.prompt[-2:]
        else:
            print >> self.stream, "No statistics object is current -- cannot reload."
        return 0
    def help_read(self):
        print >> self.stream, "Read in profile data from a specified file."

    def do_reverse(self, line):
        self.stats.reverse_order()
        return 0
    def help_reverse(self):
        print >> self.stream, "Reverse the sort order of the profiling report."

    def do_sort(self, line):
        abbrevs = self.stats.get_sort_arg_defs()
        if line and not filter(lambda x,a=abbrevs: x not in a,line.split()):
            self.stats.sort_stats(*line.split())
        else:
            print >> self.stream, "Valid sort keys (unique prefixes are accepted):"
            for (key, value) in Stats.sort_arg_dict_default.iteritems():
                print >> self.stream, "%s -- %s" % (key, value[1])
        return 0
    def help_sort(self):
        print >> self.stream, "Sort profile data according to specified keys."
        print >> self.stream, "(Typing `sort' without arguments lists valid keys.)"
    def complete_sort(self, text, *args):
        return [a for a in Stats.sort_arg_dict_default if a.startswith(text)]

    def do_stats(self, line):
        return self.generic('print_stats', line)
    def help_stats(self):
        print >> self.stream, "Print statistics from the current stat object."
        self.generic_help()

    def do_strip(self, line):
        self.stats.strip_dirs()
        return 0
    def help_strip(self):
        print >> self.stream, "Strip leading path information from filenames in the report."

    def postcmd(self, stop, line):
        if stop:
            return stop
        return None