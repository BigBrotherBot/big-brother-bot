#! /usr/bin/python
"""The main script for the RunSnakeRun profile viewer"""
import wx, sys, os, logging
try:
    from wx.py import editor
except ImportError, err:
    editor = None
from gettext import gettext as _
import pstats
import squaremap
import pstatsloader

if sys.platform == 'win32':
    windows = True
else:
    windows = False

log = logging.getLogger('runsnake.main')


ID_OPEN = wx.NewId()
ID_EXIT = wx.NewId()
ID_PACKAGE_VIEW = wx.NewId()
ID_PERCENTAGE_VIEW = wx.NewId()
ID_ROOT_VIEW = wx.NewId()
ID_BACK_VIEW = wx.NewId()
ID_UP_VIEW = wx.NewId()
ID_DEEPER_VIEW = wx.NewId()
ID_SHALLOWER_VIEW = wx.NewId()


class PStatsAdapter(squaremap.DefaultAdapter):

    percentageView = False
    total = 0

    def value(self, node, parent=None):
        if isinstance(parent, pstatsloader.PStatGroup):
            if parent.cummulative:
                return node.cummulative / parent.cummulative
            else:
                return 0
        return parent.child_cumulative_time(node)

    def label(self, node):
        if isinstance(node, pstatsloader.PStatGroup):
            return '%s / %s' % (node.filename, node.directory)
        if self.percentageView and self.total:
            time = '%0.2f%%' % round(node.cummulative * 100.0 / self.total, 2)
        else:
            time = '%0.3fs' % round(node.cummulative, 3)
        return '%s@%s:%s [%s]' % (node.name, node.filename, node.lineno, time)

    def empty(self, node):
        if node.cummulative:
            return node.local / float(node.cummulative)
        return 0.0

    def parents(self, node):
        return getattr(node, 'parents', [])

    color_mapping = None

    def background_color(self, node, depth):
        """Create a (unique-ish) background color for each node"""
        if self.color_mapping is None:
            self.color_mapping = {}
        color = self.color_mapping.get(node.key)
        if color is None:
            depth = len(self.color_mapping)
            red = (depth * 10) % 255
            green = 200 - ((depth * 5) % 200)
            blue = (depth * 25) % 200
            self.color_mapping[node.key] = color = wx.Color(red, green, blue)
        return color

    def SetPercentage(self, percent, total):
        """Set whether to display percentage values (and total for doing so)"""
        self.percentageView = percent
        self.total = total



class DirectoryViewAdapter(PStatsAdapter):
    """Provides a directory-view-only adapter for PStats objects"""

    def children(self, node):
        if isinstance(node, pstatsloader.PStatGroup):
            return node.children
        return []


class ColumnDefinition(object):
    """Definition of a given column for display"""

    index = None
    name = None
    attribute = None
    sortOn = None
    format = None
    defaultOrder = False
    percentPossible = False
    targetWidth = None

    def __init__(self, **named):
        for key, value in named.items():
            setattr(self, key, value)

    def get(self, function):
        """Get the value for this column from the function"""
        return getattr(function, self.attribute, '')

class ProfileView(wx.ListCtrl):
    """A sortable profile list control"""

    indicated = -1
    total = 0
    percentageView = False
    activated_node = None
    selected_node = None
    indicated_node = None

    def __init__(
        self, parent,
        id=-1,
        pos=wx.DefaultPosition, size=wx.DefaultSize,
        style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_VRULES|wx.LC_SINGLE_SEL,
        validator=wx.DefaultValidator,
        columns=None,
        name=_("ProfileView"),
    ):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style, validator,
                             name)
        if columns is not None:
            self.columns = columns
        self.sortOrder = [ (self.columns[5].defaultOrder, self.columns[5]), ]
        self.sorted = []
        self.CreateControls()

    def SetPercentage(self, percent, total):
        """Set whether to display percentage values (and total for doing so)"""
        self.percentageView = percent
        self.total = total
        self.Refresh()

    def CreateControls(self):
        """Create our sub-controls"""
        wx.EVT_LIST_COL_CLICK(self, self.GetId(), self.OnReorder)
        wx.EVT_LIST_ITEM_SELECTED(self, self.GetId(), self.OnNodeSelected)
        wx.EVT_MOTION(self, self.OnMouseMove)
        wx.EVT_LIST_ITEM_ACTIVATED(self, self.GetId(), self.OnNodeActivated)
        for i, column in enumerate(self.columns):
            column.index = i
            self.InsertColumn(i, column.name)
            if not windows or column.targetWidth is None:
                self.SetColumnWidth(i, wx.LIST_AUTOSIZE)
            else:
                self.SetColumnWidth(i, column.targetWidth)
        self.SetItemCount(0)

    def OnNodeActivated(self, event):
        """We have double-clicked for hit enter on a node refocus squaremap to this node"""
        try:
            node = self.sorted[event.GetIndex()]
        except IndexError, err:
            log.warn(_('Invalid index in node activated: %(index)s'),
                     index=event.GetIndex())
        else:
            wx.PostEvent(
                self,
                squaremap.SquareActivationEvent(node=node, point=None,
                                                map=None)
            )

    def OnNodeSelected(self, event):
        """We have selected a node with the list control, tell the world"""
        try:
            node = self.sorted[event.GetIndex()]
        except IndexError, err:
            log.warn(_('Invalid index in node selected: %(index)s'),
                     index=event.GetIndex())
        else:
            if node is not self.selected_node:
                wx.PostEvent(
                    self,
                    squaremap.SquareSelectionEvent(node=node, point=None,
                                                   map=None)
                )

    def OnMouseMove(self, event):
        point = event.GetPosition()
        item, where = self.HitTest(point)
        if item > -1:
            try:
                node = self.sorted[item]
            except IndexError, err:
                log.warn(_('Invalid index in mouse move: %(index)s'),
                         index=event.GetIndex())
            else:
                wx.PostEvent(
                    self,
                    squaremap.SquareHighlightEvent(node=node, point=point,
                                                   map=None)
                )

    def SetIndicated(self, node):
        """Set this node to indicated status"""
        self.indicated_node = node
        self.indicated = self.NodeToIndex(node)
        self.Refresh(False)
        return self.indicated

    def SetSelected(self, node):
        """Set our selected node"""
        self.selected_node = node
        index = self.NodeToIndex(node)
        if index != -1:
            self.Focus(index)
            self.Select(index, True)
        return index

    def NodeToIndex(self, node):
        for i, n in enumerate(self.sorted):
            if n is node:
                return i
        return -1

    def columnByAttribute(self, name):
        for column in self.columns:
            if column.attribute == name:
                return column
        return None

    def OnReorder(self, event):
        """Given a request to reorder, tell us to reorder"""
        column = self.columns[event.GetColumn()]
        if column.sortOn:
            # multiple sorts for the click...
            columns = [self.columnByAttribute(attr) for attr in column.sortOn]
            diff = [(a, b) for a, b in zip(self.sortOrder, columns)
                    if b is not a[1]]
            if not diff:
                self.sortOrder[0] = (not self.sortOrder[0][0], column)
            else:
                self.sortOrder = [
                    (c.defaultOrder, c) for c in columns
                ] + [(a, b) for (a, b) in self.sortOrder if b not in columns]
        else:
            if column is self.sortOrder[0][1]:
                # reverse current major order
                self.sortOrder[0] = (not self.sortOrder[0][0], column)
            else:
                self.sortOrder = [(column.defaultOrder, column)] + [
                    (a, b)
                    for (a, b) in self.sortOrder if b is not column
                ]
        # TODO: store current selection and re-select after sorting...
        self.reorder()
        self.Refresh()

    def reorder(self):
        """Force a reorder of the displayed items"""
        self.sorted.sort(self.compareFunction)

    def compareFunction(self, first, second):
        """Compare two functions according to our current sort order"""
        for ascending, column in self.sortOrder:
            aValue, bValue = column.get(first), column.get(second)
            diff = cmp(aValue, bValue)
            if diff:
                if not ascending:
                    return -diff
                else:
                    return diff
        return 0

    def integrateRecords(self, functions):
        """Integrate records from the loader"""
        self.SetItemCount(len(functions))
        self.sorted = functions[:]
        self.reorder()
        self.Refresh()

    indicated_attribute = wx.ListItemAttr()
    indicated_attribute.SetBackgroundColour('#00ff00')

    def OnGetItemAttr(self, item):
        """Retrieve ListItemAttr for the given item (index)"""
        if self.indicated > -1 and item == self.indicated:
            return self.indicated_attribute
        return None

    def OnGetItemText(self, item, col):
        """Retrieve text for the item and column respectively"""
        # TODO: need to format for rjust and the like...
        try:
            column = self.columns[col]
            value = column.get(self.sorted[item])
        except IndexError, err:
            return None
        else:
            if column.percentPossible and self.percentageView and self.total:
                value = value / float(self.total) * 100.00
            if column.format:
                try:
                    return column.format % (value,)
                except Exception, err:
                    log.warn('Column %s could not format %r value: %s',
                        column.name, type(value), value
                    )
                    return str(value)
            else:
                return str(value)

    columns = [
        ColumnDefinition(
            name = _('Name'),
            attribute = 'name',
            defaultOrder = True,
            targetWidth = 50,
        ),
        ColumnDefinition(
            name = _('Calls'),
            attribute = 'calls',
            targetWidth = 50,
        ),
        ColumnDefinition(
            name = _('RCalls'),
            attribute = 'recursive',
            targetWidth = 40,
        ),
        ColumnDefinition(
            name = _('Local'),
            attribute = 'local',
            format = '%0.5f',
            percentPossible = True,
            targetWidth = 50,
        ),
        ColumnDefinition(
            name = _('/Call'),
            attribute = 'localPer',
            format = '%0.5f',
            targetWidth = 50,
        ),
        ColumnDefinition(
            name = _('Cum'),
            attribute = 'cummulative',
            format = '%0.5f',
            percentPossible = True,
            targetWidth = 50,
        ),
        ColumnDefinition(
            name = _('/Call'),
            attribute = 'cummulativePer',
            format = '%0.5f',
            targetWidth = 50,
        ),
        ColumnDefinition(
            name = _('File'),
            attribute = 'filename',
            sortOn = ('filename', 'lineno', 'directory',),
            defaultOrder = True,
            targetWidth = 70,
        ),
        ColumnDefinition(
            name = _('Line'),
            attribute = 'lineno',
            sortOn = ('filename', 'lineno', 'directory'),
            defaultOrder = True,
            targetWidth = 30,
        ),
        ColumnDefinition(
            name = _('Directory'),
            attribute = 'directory',
            sortOn = ('directory', 'filename', 'lineno'),
            defaultOrder = True,
            targetWidth = 90,
        ),
    ]


class MainFrame(wx.Frame):
    """The root frame for the display of a single data-set"""

    loader = None
    percentageView = False
    directoryView = False
    historyIndex = -1
    activated_node = None
    selected_node = None
    TBFLAGS = (
        wx.TB_HORIZONTAL
        #| wx.NO_BORDER
        | wx.TB_FLAT
    )

    def __init__(
        self, parent=None, id=-1,
        title=_("Run Snake Run"),
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.DEFAULT_FRAME_STYLE|wx.CLIP_CHILDREN,
        name= _("RunSnakeRun"),
    ):
        """Initialise the Frame"""
        wx.Frame.__init__(self, parent, id, title, pos, size, style, name)
        # TODO: toolbar for back, up, root, directory-view, percentage view
        self.adapter = PStatsAdapter()
        self.CreateControls()
        self.history = [] # set of (activated_node, selected_node) pairs...

    def CreateControls(self):
        """Create our sub-controls"""
        self.CreateMenuBar()
        self.SetupToolBar()
        self.CreateStatusBar()
        self.leftSplitter = wx.SplitterWindow(
            self
        )
        self.rightSplitter = wx.SplitterWindow(
            self.leftSplitter
        )
        self.listControl = ProfileView(
            self.leftSplitter,
        )
        self.squareMap = squaremap.SquareMap(
            self.rightSplitter,
            padding = 6,
            labels = True,
            adapter = self.adapter,
        )
        self.tabs = wx.Notebook(
            self.rightSplitter,
        )

        self.calleeListControl = ProfileView(
            self.tabs,
        )
        self.allCalleeListControl = ProfileView(
            self.tabs,
        )
        self.allCallerListControl = ProfileView(
            self.tabs,
        )
        self.callerListControl = ProfileView(
            self.tabs,
        )
        self.CreateSourceWindow(self.tabs)
        self.ProfileListControls = [
            self.listControl,
            self.calleeListControl,
            self.allCalleeListControl,
            self.callerListControl,
            self.allCallerListControl,
        ]
        self.tabs.AddPage(self.calleeListControl, _('Callees'), True)
        self.tabs.AddPage(self.allCalleeListControl, _('All Callees'), False)
        self.tabs.AddPage(self.callerListControl, _('Callers'), False)
        self.tabs.AddPage(self.allCallerListControl, _('All Callers'), False)
        if editor:
            self.tabs.AddPage(self.sourceCodeControl, _('Source Code'), False)
        self.rightSplitter.SetSashSize(10)
        self.Maximize(True)
        # calculate size as proportional value for initial display...
        width, height = wx.GetDisplaySize()
        rightsplit = 2 * (height // 3)
        leftsplit = width // 3
        self.rightSplitter.SplitHorizontally(self.squareMap, self.tabs,
                                             rightsplit)
        self.leftSplitter.SplitVertically(self.listControl, self.rightSplitter,
                                          leftsplit)
        squaremap.EVT_SQUARE_HIGHLIGHTED(self.squareMap,
                                         self.OnSquareHighlightedMap)
        squaremap.EVT_SQUARE_SELECTED(self.listControl,
                                      self.OnSquareSelectedList)
        squaremap.EVT_SQUARE_SELECTED(self.squareMap, self.OnSquareSelectedMap)
        squaremap.EVT_SQUARE_ACTIVATED(self.squareMap, self.OnNodeActivated)
        for control in self.ProfileListControls:
            squaremap.EVT_SQUARE_ACTIVATED(control, self.OnNodeActivated)
            squaremap.EVT_SQUARE_HIGHLIGHTED(control,
                                             self.OnSquareHighlightedList)
        # TODO: create toolbar
        # TODO: create keyboard accelerators

    def CreateMenuBar(self):
        """Create our menu-bar for triggering operations"""
        menubar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append(ID_OPEN, _('&Open'), _('Open a new profile file'))
        menu.AppendSeparator()
        menu.Append(ID_EXIT, _('&Close'), _('Close this RunSnakeRun window'))
        menubar.Append(menu, _('&File'))
        menu = wx.Menu()
        self.packageMenuItem = menu.AppendCheckItem(
            ID_PACKAGE_VIEW, _('&File View'),
            _('View time spent by package/module')
        )
        self.percentageMenuItem = menu.AppendCheckItem(
            ID_PERCENTAGE_VIEW, _('&Percentage View'),
            _('View time spent as percent of overall time')
        )
        self.rootViewItem = menu.Append(
            ID_ROOT_VIEW, _('&Root View (Home)'),
            _('View the root of the tree')
        )
        self.backViewItem = menu.Append(
            ID_BACK_VIEW, _('&Back'), _('Go back in your viewing history')
        )
        self.upViewItem = menu.Append(
            ID_UP_VIEW, _('&Up'),
            _('Go "up" to the parent of this node with the largest cummulative total')
        )

        # This stuff isn't really all that useful for profiling,
        # it's more about how to generate graphics to describe profiling...
#        self.deeperViewItem = menu.Append(
#            ID_DEEPER_VIEW, _('&Deeper'), _('View deeper squaremap views')
#        )
#        self.shallowerViewItem = menu.Append(
#            ID_SHALLOWER_VIEW, _('&Shallower'), _('View shallower squaremap views')
#        )
#        wx.ToolTip.Enable(True)
        menubar.Append(menu, _('&View'))
        self.SetMenuBar(menubar)

        wx.EVT_MENU(self, ID_EXIT, lambda evt: self.Close(True))
        wx.EVT_MENU(self, ID_OPEN, self.OnOpenFile)
        wx.EVT_MENU(self, ID_PACKAGE_VIEW, self.OnPackageView)
        wx.EVT_MENU(self, ID_PERCENTAGE_VIEW, self.OnPercentageView)
        wx.EVT_MENU(self, ID_UP_VIEW, self.OnUpView)
        wx.EVT_MENU(self, ID_DEEPER_VIEW, self.OnDeeperView)
        wx.EVT_MENU(self, ID_SHALLOWER_VIEW, self.OnShallowerView)
        wx.EVT_MENU(self, ID_ROOT_VIEW, self.OnRootView)
        wx.EVT_MENU(self, ID_BACK_VIEW, self.OnBackView)

    def CreateSourceWindow(self, tabs):
        """Create our source-view window for tabs"""
        if editor:
            self.sourceEditor = wx.py.editor.Editor(self.tabs)
            self.sourceCodeControl = wx.py.editor.EditWindow(
                self.sourceEditor, self.tabs, -1
            )
            self.sourceCodeControl.SetText(u"")
            self.sourceFileShown = None
            self.sourceCodeControl.setDisplayLineNumbers(True)

    def SetupToolBar(self):
        """Create the toolbar for common actions"""
        tb = self.CreateToolBar(self.TBFLAGS)
        tsize = (24, 24)
        tb.ToolBitmapSize = tsize
        open_bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR,
                                            tsize)
        tb.AddLabelTool(ID_OPEN, "Open", open_bmp, shortHelp="Open",
                        longHelp="Open a (c)Profile trace file")
        tb.AddSeparator()
#        self.Bind(wx.EVT_TOOL, self.OnOpenFile, id=ID_OPEN)
        self.rootViewTool = tb.AddLabelTool(
            ID_ROOT_VIEW, _("Root View"),
            wx.ArtProvider.GetBitmap(wx.ART_GO_HOME, wx.ART_TOOLBAR, tsize),
            shortHelp=_("Display the root of the current view tree (home view)")
        )
        self.rootViewTool = tb.AddLabelTool(
            ID_BACK_VIEW, _("Back"),
            wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR, tsize),
            shortHelp=_("Back to the previously activated node in the call tree")
        )
        self.upViewTool = tb.AddLabelTool(
            ID_UP_VIEW, _("Up"),
            wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_TOOLBAR, tsize),
            shortHelp=_("Go one level up the call tree (highest-percentage parent)")
        )
        tb.AddSeparator()
        # TODO: figure out why the control is sizing the label incorrectly on Linux
        self.percentageViewTool = wx.CheckBox(tb, -1, _("Percent    "))
        self.percentageViewTool.SetToolTip(wx.ToolTip(
            _("Toggle display of percentages in list views")))
        tb.AddControl(self.percentageViewTool)
        wx.EVT_CHECKBOX(self.percentageViewTool,
                        self.percentageViewTool.GetId(), self.OnPercentageView)

        self.packageViewTool = wx.CheckBox(tb, -1, _("File View    "))
        self.packageViewTool.SetToolTip(wx.ToolTip(
            _("Switch between call-hierarchy and package/module/function hierarchy")))
        tb.AddControl(self.packageViewTool)
        wx.EVT_CHECKBOX(self.packageViewTool, self.packageViewTool.GetId(),
                        self.OnPackageView)
        tb.Realize()

    def OnOpenFile(self, event):
        """Request to open a new profile file"""
        dialog = wx.FileDialog(self, style=wx.OPEN|wx.FD_MULTIPLE)
        if dialog.ShowModal() == wx.ID_OK:
            paths = dialog.GetPaths()
            if self.loader:
                # we've already got a displayed data-set, open new window...
                frame = MainFrame()
                frame.Show(True)
                frame.load(*paths)
            else:
                self.load(*paths)

    def OnShallowerView(self, event):
        if not self.squareMap.max_depth:
            new_depth = self.squareMap.max_depth_seen or 0 - 5
        else:
            new_depth = self.squareMap.max_depth - 5
        self.squareMap.max_depth = max((1, new_depth))
        self.squareMap.Refresh()

    def OnDeeperView(self, event):
        if not self.squareMap.max_depth:
            new_depth = 5
        else:
            new_depth = self.squareMap.max_depth + 5
        self.squareMap.max_depth = max((self.squareMap.max_depth_seen or 0,
                                        new_depth))
        self.squareMap.Refresh()

    def OnPackageView(self, event):
        self.SetPackageView(not self.directoryView)

    def SetPackageView(self, directoryView):
        """Set whether to use directory/package based view"""
        self.directoryView = not self.directoryView
        self.packageMenuItem.Check(self.directoryView)
        self.packageViewTool.SetValue(self.directoryView)
        if self.loader:
            self.SetModel(self.loader)
        self.RecordHistory()

    def OnPercentageView(self, event):
        """Handle percentage-view event from menu/toolbar"""
        self.SetPercentageView(not self.percentageView)

    def SetPercentageView(self, percentageView):
        """Set whether to display percentage or absolute values"""
        self.percentageView = percentageView
        self.percentageMenuItem.Check(self.percentageView)
        self.percentageViewTool.SetValue(self.percentageView)
        total = self.loader.tree.cummulative
        for control in self.ProfileListControls:
            control.SetPercentage(self.percentageView, total)
        self.adapter.SetPercentage(self.percentageView, total)

    def OnUpView(self, event):
        """Request to move up the hierarchy to highest-weight parent"""
        node = self.activated_node
        if node:
            if self.directoryView:
                tree = pstatsloader.TREE_FILES
            else:
                tree = pstatsloader.TREE_CALLS
            parents = [
                parent for parent in
                self.adapter.parents(node)
                if getattr(parent, 'tree', pstatsloader.TREE_CALLS) == tree
            ]
            if parents:
                parents.sort(lambda a, b: cmp(self.adapter.value(node, a),
                                              self.adapter.value(node, b)))
                class event:
                    node = parents[-1]
                self.OnNodeActivated(event)
            else:
                self.SetStatusText(_('No parents for the currently selected node: %(node_name)s')
                                   % dict(node_name=self.adapter.label(node)))
        else:
            self.SetStatusText(_('No currently selected node'))

    def OnBackView(self, event):
        """Request to move backward in the history"""
        self.historyIndex -= 1
        try:
            self.RestoreHistory(self.history[self.historyIndex])
        except IndexError, err:
            self.SetStatusText(_('No further history available'))

    def OnRootView(self, event):
        """Reset view to the root of the tree"""
        self.adapter, tree, rows = self.RootNode()
        self.squareMap.SetModel(tree, self.adapter)
        self.RecordHistory()

    def OnNodeActivated(self, event):
        """Double-click or enter on a node in some control..."""
        self.activated_node = self.selected_node = event.node
        self.squareMap.SetModel(event.node, self.adapter)
        if editor:
            if self.SourceShowFile(event.node):
                if hasattr(event.node,'lineno'):
                    self.sourceCodeControl.GotoLine(event.node.lineno)
        self.RecordHistory()

    def SourceShowFile(self, node):
        """Show the given file in the source-code view (attempt it anyway)"""
        if not node.directory:
            # TODO: any cases other than built-ins?
            return None
        if node.filename == '~':
            # TODO: look up C/Cython/whatever source???
            return None
        path = os.path.join(node.directory, node.filename)
        if self.sourceFileShown != path:
            try:
                data = open(path).read()
            except Exception, err:
                # TODO: load from zips/eggs? What about .pyc issues?
                return None
            else:
                self.sourceCodeControl.SetText(data)
        return path

    def OnSquareHighlightedMap(self, event):
        self.SetStatusText(self.adapter.label(event.node))
        self.listControl.SetIndicated(event.node)
        text = self.squareMap.adapter.label(event.node)
        self.squareMap.SetToolTipString(text)
        self.SetStatusText(text)

    def OnSquareHighlightedList(self, event):
        self.SetStatusText(self.adapter.label(event.node))
        self.squareMap.SetHighlight(event.node, propagate=False)

    def OnSquareSelectedList(self, event):
        self.SetStatusText(self.adapter.label(event.node))
        self.squareMap.SetSelected(event.node)
        self.OnSquareSelected(event)
        self.RecordHistory()

    def OnSquareSelectedMap(self, event):
        self.listControl.SetSelected(event.node)
        self.OnSquareSelected(event)
        self.RecordHistory()

    def OnSquareSelected(self, event):
        """Update all views to show selection children/parents"""
        self.selected_node = event.node
        self.calleeListControl.integrateRecords(event.node.children)
        self.callerListControl.integrateRecords(event.node.parents)
        self.allCalleeListControl.integrateRecords(event.node.descendants())
        self.allCallerListControl.integrateRecords(event.node.ancestors())

    restoringHistory = False

    def RecordHistory(self):
        """Add the given node to the history-set"""
        if not self.restoringHistory:
            record = self.activated_node
            if self.historyIndex < -1:
                try:
                    del self.history[self.historyIndex+1:]
                except AttributeError, err:
                    pass
            if (not self.history) or record != self.history[-1]:
                self.history.append(record)
            del self.history[:-200]
            self.historyIndex = -1

    def RestoreHistory(self, record):
        self.restoringHistory = True
        try:
            activated = record
            class activated_event:
                node = activated

            if activated:
                self.OnNodeActivated(activated_event)
                self.squareMap.SetSelected(activated_event.node)
                self.listControl.SetSelected(activated_event.node)
        finally:
            self.restoringHistory = False

    def load(self, *filenames):
        """Load our hotshot dataset (iteratively)"""
        try:
            self.SetModel(pstatsloader.PStatsLoader(*filenames))
            self.SetTitle(_("Run Snake Run: %(filenames)s")
                          % {'filenames': ', '.join(filenames)[:120]})
        except (IOError, OSError, ValueError), err:
            self.SetStatusText(
                _('Failure during load of %(filenames)s: %(err)s'
            ) % dict(
                filenames=" ".join([repr(x) for x in filenames]),
                err=err
            ))

    def SetModel(self, loader):
        """Set our overall model (a loader object) and populate sub-controls"""
        self.loader = loader
        self.adapter, tree, rows = self.RootNode()
        self.listControl.integrateRecords(rows.values())
        self.activated_node = tree
        self.squareMap.SetModel(tree, self.adapter)
        self.RecordHistory()

    def RootNode(self):
        """Return our current root node and appropriate adapter for it"""
        if self.directoryView:
            adapter = DirectoryViewAdapter()
            tree = self.loader.location_tree
            rows = self.loader.location_rows
        else:
            adapter = PStatsAdapter()
            tree = self.loader.tree
            rows = self.loader.rows
        adapter.SetPercentage(self.percentageView, self.loader.tree.cummulative)
        return adapter, tree, rows


class RunSnakeRunApp(wx.App):
    """Basic application for holding the viewing Frame"""

    def OnInit(self, file=None):
        """Initialise the application"""
        wx.InitAllImageHandlers()
        frame = MainFrame()
        frame.Show(True)
        self.SetTopWindow(frame)
        if file is not None:
            wx.CallAfter(frame.load, file)
        elif sys.argv[1:]:
            wx.CallAfter(frame.load, *sys.argv[1:])
        return True


usage = """runsnake.py profilefile

profilefile -- a file generated by a HotShot profile run from Python
"""

def main():
    """Mainloop for the application"""
    app = RunSnakeRunApp(0)
    #app.OnInit(r'C:\b3\some.profile')
    app.MainLoop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
