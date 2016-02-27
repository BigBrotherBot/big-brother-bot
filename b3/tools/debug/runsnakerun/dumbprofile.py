import pdb, sys, time, thread, threading

class CodeInfo( object ):
    """Code-object information for multiple calls of code"""
    def __init__( self, code ):
        """Open the frame"""
        self.local = 0
        self.cummulative = 0
        self.callcount = 0
        self.children = {}
        self.lines = {}
        if isinstance( code, (str,unicode)):
            self.filename = '~'
            self.firstline = 0
            self.name = code
        else:
            self.filename = code.co_filename
            self.firstline = code.co_firstlineno
            self.name = code.co_name 
        self.code = code
    def add_line( self, lineno, delta ):
        """Add line-number delta for line-profiling operations"""
        self.lines[lineno] = self.lines.get( lineno,0) + delta 
    def add_local( self, delta ):
        """Add local time to our counters"""
        self.local += delta
        self.callcount += 1
    def add_cummulative( self, delta, subframe ):
        """Add cummulative time to our counters"""
        self.cummulative += delta
        if subframe:
            current = self.children.get( subframe.code_info, 0 )
            self.children[ subframe.code_info ] = current + delta 
    def __repr__( self ):
        return '%s -> %s %s'%(
            (self.filename,self.firstline,self.name),
            (self.local, self.cummulative, self.callcount),
            self.lines
        )
    

class FrameInfo( object ):
    """Storage of frame information for a single frame"""
    def __init__( self, frame, profiler, current_time ):
        """Open the frame"""
        self.local = 0
        self.cummulative = 0
        self.code_info = profiler.code_info_for( frame.f_code )
        self.start_time = current_time
        self.lines = {}
        self.open_line = None
    def add_local( self, delta ):
        """Add local time to our counters"""
        self.code_info.add_local( delta )
    def add_cummulative( self, delta, subframe ):
        """Add cummulative time to our counters"""
        self.code_info.add_cummulative( delta, subframe )
    def start_line( self, lineno, start_time ):
        self.lines[lineno] = start_time
        self.open_line = lineno
    def add_line( self, lineno, stop_time ):
        """Add per-line timing to our counters"""
        if self.lines.has_key( lineno ):
            delta = stop_time - self.lines[lineno]
            print 'delta for lineno:', lineno, delta
            self.code_info.add_line( lineno, delta )

class SimpleProfiler( object ):
    def __init__( self ):
        self.frame_info = [None]*sys.getrecursionlimit()
        self.code_info = {}
        self.frame_depth = -1
        self.internal_time = 0
        self.last_time = None
    def describe( self, frame ):
        return frame.f_lineno,(frame.f_code.co_name, frame.f_code.co_firstlineno)
    def __call__( self, frame, event, arg):
        # Obviously this would need a real high-precision timer...
        t = time.time()
        if self.last_time:
            delta = t - self.last_time 
        else:
            delta = 0
        self.internal_time += delta 
        if event in ('call','c_call'):
            self.frame_depth += 1
            frame_info = FrameInfo( frame, self, self.internal_time )
            self.frame_info[ self.frame_depth ] = frame_info
        elif event in ('return','exception','c_return','c_exception'):
            frame_info = self.frame_info[ self.frame_depth ]
            if frame_info:
                if frame_info.open_line is not None:
                    frame_info.add_line( frame_info.open_line, self.internal_time )
                frame_delta = self.internal_time - frame_info.start_time
                for i in range( self.frame_depth ):
                    info = self.frame_info[i]
                    if i < len(self.frame_info):
                        other = self.frame_info[i+1]
                    else:
                        other = None
                    if info is None:
                        print i,self.frame_info[:i+1]
                    info.add_cummulative( frame_delta, other )
                frame_info.add_local( frame_delta )
            self.frame_info[ self.frame_depth ] = None
            self.frame_depth -= 1
            if self.frame_depth >= 0:
                frame_info = self.frame_info[ self.frame_depth ]
                if frame_info.open_line:
                    frame_info.add_line( frame_info.open_line, self.internal_time )
        elif event in ('line',):
            frame_info = self.frame_info[ self.frame_depth ]
            if frame_info:
                if frame_info.open_line is not None:
                    frame_info.add_line( frame_info.open_line, self.internal_time )
                frame_info.start_line( frame.f_lineno, self.internal_time )
        
        self.last_time = time.time()
        return self
    def do_line_time( self, frame ):
        frame_info.add_line( frame.f_lineno, line_delta )
    
    def code_info_for( self, code ):
        current = self.code_info.get(code)
        if current is None:
            self.code_info[code] = current = CodeInfo( code )
        return current

def test():
    23L**10000
    time.sleep( 3.0 )
    r()
    
def r( depth = 5 ):
    if depth < 0:
        return None 
    else:
        z = '22344'* 100000
        time.sleep( .5 )
        return r( depth - 1 )

if __name__ == "__main__":
    s = SimpleProfiler()
    sys.settrace( s )
    test()
    sys.settrace( None )
    for value in s.code_info.values():
        print value
    
