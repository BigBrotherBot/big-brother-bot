#
# Sets of ranges of (integer) numbers.
"""Sets of (ranges of) integer numbers.

This module exports the Ranges class and the BadRange exception."""

# This is necessary to get 'yield' under Python 2.2.
# Since we still have Red Hat 7.3 machines (at least for a bit longer...)
from __future__ import generators

__all__ = ['BadRange', 'Ranges']

class BadRange(Exception):
	"""Raised if there is some problem with ranges.
	(Yes, this is non-specific.)"""
	pass

class Ranges:
	"""Represent a set of integer ranges.

	Ranges represent a set of ranges of numbers. A new range
	or a list of them may be added to or deleted from the set.
	Adjacent ranges are merged in the set to create the minimal
	set of ranges necessary to cover all included numbers.

	Range sets support addition and subtraction operations.
	Eg: Ranges(1,10) + Ranges(2,30) + Ranges(50,60) - Ranges(14,28)"""
	def __init__(self, *args):
		"""Optional START,END arguments become the initial range."""
		self._l = []
		if len(args) not in (0, 2):
			raise TypeError("Ranges() takes either 0 or 2 arguments.")
		if args:
			self._good(args[0], args[1])
			self._l.append([args[0],args[1]])

	def _good(self, start, end):
		if start > end:
			raise BadRange("start > end")

	# This much work for str() may be a bad plan.
	def _rel(self, val):
		return val
	def _rrange(self, r):
		if r[0] == r[1]:
			return str(self._rel(r[0]))
		else:
			return "%s-%s" % (self._rel(r[0]), self._rel(r[1]))
	def __str__(self):
		return "<Ranges: %s>" % (" ".join(map(self._rrange, self._l)),)

	# Find the point where start should occur in the list as the
	# lower boundary of a range. Since range starts are ordered
	# in ascending order, this is the first point where
	#	start <= range[i].start
	# (ie start <= self._l[i][0]) is true. If this is not true
	# for any spot on the list, we return one past the end of
	# the list.
	# We uses a binary search algorithm for speed on long
	# lists. The algorithm is taken from the bisect module.
	def _find(self, start):
		lo = 0; hi = len(self._l)
		while lo < hi:
			mid = (lo+hi)//2
			if self._l[mid][0] < start:	lo = mid+1
			else:				hi = mid
		return lo

	def _isprev(self, i):
		return not (i == 0)
	def _prev(self,i):
		return self._l[i-1]

	# We turn single-value adds and removals into the full range adds
	# and removes.
	def addnum(self, val):
		"""Add VALUE to the set."""
		self.addrange(val, val)
	def delnum(self, val):
		"Remove VALUE from the set."
		self.delrange(val, val)

	def addrange(self, start, end):
		"""And a range from START to END to the set."""
		self._good(start, end)
		# we store ranges sorted by start. find where it should go.
		i = self._find(start)
		# too large to fit:
		if i == len(self._l):
			self._l.append([start, end])
		else:
			r = self._l[i]
			# does it fit entirely inside an existing one?
			if start >= r[0] and end <= r[1]:
				return
			# glue it in in order; right now, ordered by start.
			self._l.insert(i, [start, end])
		# now we fix up the list by merging adjacent or overlapping
		# entries. We start from where we inserted, or 1 if we
		# inserted at 0, so we always have a previous entry.
		# if the list is length 1, this loop will do nothing.
		i = max(i, 1)
		while i < len(self._l):
			# attempt to merge with previous entry
			ro = self._l[i-1]
			r = self._l[i]
			# if front is adjacent or inside their back, we
			# are either inside them, or we are merging.
			if r[0]-1 <= ro[1]:
				# we must use max(), because we may be inside
				# them.
				ro[1] = max(r[1], ro[1])
				del self._l[i]
			elif r[0] == start and r[1] == end:
				# if we are currently looking at ourselves,
				# we need to look one afterwards too, in case
				# we are merging *up*. (I am not entirely sure
				# that this logic is still correct. See del.)
				i = i + 1
			else:
				# if we have done no work now, we will never
				# do any more.
				break

	def delrange(self, start, end):
		"""Remove the range START to END from the set."""
		self._good(start, end)
		i = self._find(start)
		# deal with the previous block.
		# the previous block axiomatically has something in it after
		# we're done, because it starts before the range.
		if self._isprev(i) and start <= self._prev(i)[1]:
			r = self._prev(i)
			oe = r[1]
			# this is always correct:
			r[1] = start-1
			# however, we may need to split it.
			if end < oe:
				self._l.insert(i, [end+1, oe])
		# we may need to delete forward:
		while i < len(self._l):
			r = self._l[i]
			if r[0] > end:
				break
			# the range may be entirely contained in what we're
			# removing, or it may be only partially included.
			if r[1] <= end:
				del self._l[i]
			else:
				r[0] = end+1

	def addlist(self, l):
		"""Add a list of [start,end] ranges to the set."""
		for s,e in l:
			self.addrange(s, e)
	def dellist(self, l):
		"""Remove a list of [start,end] ranges from the set."""
		for s,e in l:
			self.delrange(s, e)

	# NOTE: these use internal implementation details. You lose if
	# you pass bogus objects to them.
	def addRanges(self, rng):
		for s,e in rng._l:
			self.addrange(s, e)
	def delRanges(self, rng):
		for s,e in rng._l:
			self.delrange(s, e)

	# Contains is defined for the values that we contain, not for
	# set operations on ourselves. (Don't go there, really.) So
	# you apply 'val in Ranges' for integers, so we can just do
	# this.
	def __contains__(self, val):
		"""Is VAL a point in the set of ranges?"""
		if len(self._l) <= 4:
			for r in self._l:
				if r[0] <= val <= r[1]:
					return 1
			return 0

		# It's worth using binary search now.
		p = self._find(val)
		pm = p-1
		# This complicated expression checks for a valid
		# range element at p and then if val is inside it,
		# and then for a valid range element one back and
		# if val is inside *that*.
		return ((p < len(self._l) and \
			 (self._l[p][0] <= val <= self._l[p][1])) \
			or (pm >= 0 and \
			    (self._l[pm][0] <= val <= self._l[pm][1])))
		return 0

	# This is a hideously inefficient implementation. Don't use it
	# unless you have to!
	def copy(self):
		"""Return a new object that is a copy of this set of ranges."""
		n = self.__class__()
		for s,e in self._l:
			n._l.append([s,e])
		return n
	def __add__(self, other):
		n = self.copy()
		for s,e in other._l:
			n.addrange(s,e)
		return n
	def __sub__(self, other):
		n = self.copy()
		for s,e in other._l:
			n.delrange(s,e)
		return n

	def __eq__(self, other):
		if len(other._l) != len(self._l):
			return 0
		for i in xrange(0, len(self._l)):
			if self._l[i] != other._l[i]:
				return 0
		return 1

	# Is other a subset of us?
	def subset(self, other):
		"""Return True if other is a subset of this set of ranges."""
		i = 0; myl = self._l
		j = 0; otl = other._l
		while i < len(myl) and j < len(otl):
			# First: is otl[j] contained within myl[i]?
			if otl[j][0] >= myl[i][0] and otl[j][1] <= myl[i][1]:
				# push otl forward.
				j += 1
			# otl may have jumped ahead of myl because of the
			# last one; push us forward if so.
			elif otl[j][0] > myl[i][1]:
				i += 1
			# Any other case is a mismatch.
			else:
				return 0
		return j == len(otl)
	# Does other have elements in common with us?
	def intersect(self, other):
		"""Returns True if another set of ranges intersects us."""
		def _overlap(t1, t2):
			low1, hi1 = t1
			low2, hi2 = t2
			return (low2 <= low1 <= hi2) or \
			       (low2 <= hi1 <= hi2) or \
			       (low1 <= low2 <= hi1) or \
			       (low1 <= hi2 <= hi1)
		i = 0; myl = self._l
		j = 0; otl = other._l
		while i < len(myl) and j < len(otl):
			# Do the current elements overlap?
			if _overlap(myl[i], otl[j]):
				return 1
			# They do not. Advance one or the other, whichever
			# is lower.
			if myl[i][1] < otl[j][0]:
				i += 1
			else:
				j += 1
		return 0

	def adjacent(self, other):
		"""Return True if we are adjacent to another range."""
		if len(self._l) == 0 or len(other._l) == 0:
			return 0
		return (self._l[-1][1]+1 == other._l[0][0]) or \
		       (self._l[0][0] == other._l[-1][1]+1)

	# The length of a range is clearly the number of individual
	# elements it contains, ie len(tuple(range)) without actually,
	# like, generating that number.
	def len(self):
		"""The length of a set of ranges is the number of elements
		that it	contains."""
		return reduce(lambda x, y: x+y[1]-y[0]+1, self._l, 0)
	# If we are actually storing longs (such as, say, IP addresses),
	# our length can exceed sys.maxint and in any case can be turned
	# into a long. We try to coerce any inadvertant longs into ints;
	# if that fails, we die and you get a wierd TypeError.
	# So really, you want to use Ranges.len(), not len(Ranges).
	def __len__(self):
		"""Due to technical limitations of CPython, you should
		use Ranges.len() instead of len(Ranges)."""
		return int(self.len())

	def __nonzero__(self):
		return len(self._l) > 0

	def __cmp__(self, other):
		"""Any comparison between Ranges other than for inequality or
		equality has undefined results."""
		if self.__eq__(other):
			return 0
		# invalid to use except as ==, so I don't CARE.
		return 1

	# This works because as far as a lot of things are concerned,
	# __iter__ is merely a normal function (that is expected to
	# return an iterable). Since functions that use 'yield' are
	# actually iterable generators...
	def __iter__(self):
		"""Yields every number in the set of ranges."""
		for rng in self._l:
			# We would use xrange, except xrange demands
			# ints, not longs, and sometimes we store longs.
			# BITE ME.
			i = rng[0]
			while i <= rng[1]:
				yield self._rel(i)
				i += 1
