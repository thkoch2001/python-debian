#
# Debtags.py -- Access and manipulate Debtags information
#
# Copyright (C) 2006  Enrico Zini <enrico@enricozini.org>
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import math

def readTagDatabase(input):
	"Read the tag database, returning a pkg->tags dictionary"
	db = {}
	for line in input:
		# Is there a way to remove the last character of a line that does not
		# make a copy of the entire line?
		line = line.rstrip("\n")
		pkgs, tags = line.split(": ")
		# Create the tag set using the native set
		tags = set(tags.split(", "))
		for p in pkgs.split(", "):
			db[p] = tags.copy()
	return db;

def readTagDatabaseReversed(input):
	"Read the tag database, returning a tag->pkgs dictionary"
	db = {}
	for line in input:
		# Is there a way to remove the last character of a line that does not
		# make a copy of the entire line?
		line = line.rstrip("\n")
		pkgs, tags = line.split(": ")
		# Create the tag set using the native set
		pkgs = set(pkgs.split(", "))
		for tag in tags.split(", "):
			if db.has_key(tag):
				db[tag] |= pkgs
			else:
				db[tag] = pkgs.copy()
	return db;

def readTagDatabaseBothWays(input, tagFilter = None):
	"Read the tag database, returning a pkg->tags and a tag->pkgs dictionary"
	db = {}
	dbr = {}
	for line in input:
		# Is there a way to remove the last character of a line that does not
		# make a copy of the entire line?
		line = line.rstrip("\n")
		pkgs, tags = line.split(": ")
		# Create the tag set using the native set
		pkgs = set(pkgs.split(", "))
		if tagFilter == None:
			tags = set(tags.split(", "))
		else:
			tags = set(filter(tagFilter, tags.split(', ')))
		for pkg in pkgs:
			db[pkg] = tags.copy()
		for tag in tags:
			if dbr.has_key(tag):
				dbr[tag] |= pkgs
			else:
				dbr[tag] = pkgs.copy()
	return db, dbr;


def reverse(db):
	"Reverse a tag database, from package -> tags to tag->packages"
	res = {}
	for pkg, tags in db.items():
		for tag in tags:
			if not res.has_key(tag):
				res[tag] = set()
			res[tag].add(pkg)
	return res


def output(db):
	"Write the tag database"
	for pkg, tags in db.items():
		# Using % here seems awkward to me, but if I use calls to
		# sys.stdout.write it becomes a bit slower
		print "%s:" % (pkg), ", ".join(tags)


def relevanceIndexFunction(full, sub):
	#return (float(sub.card(tag)) / float(sub.tagCount())) / \
	#       (float(full.card(tag)) / float(full.tagCount()))
	#return sub.card(tag) * full.card(tag) / sub.tagCount()

	# New cardinality divided by the old cardinality
	#return float(sub.card(tag)) / float(full.card(tag))

	## Same as before, but weighted by the relevance the tag had in the
	## full collection, to downplay the importance of rare tags
	#return float(sub.card(tag) * full.card(tag)) / float(full.card(tag) * full.tagCount())
	# Simplified version:
	#return float(sub.card(tag)) / float(full.tagCount())
	
	# Weighted by the square root of the relevance, to downplay the very
	# common tags a bit
	#return lambda tag: float(sub.card(tag)) / float(full.card(tag)) * math.sqrt(full.card(tag) / float(full.tagCount()))
	#return lambda tag: float(sub.card(tag)) / float(full.card(tag)) * math.sqrt(full.card(tag) / float(full.packageCount()))
	# One useless factor removed, and simplified further, thanks to Benjamin Mesing
	return lambda tag: float(sub.card(tag)**2) / float(full.card(tag))

	# The difference between how many packages are in and how many packages are out
	# (problems: tags that mean many different things can be very much out
	# as well.  In the case of 'image editor', for example, there will be
	# lots of editors not for images in the outside group.
	# It is very, very good for nonambiguous keywords like 'image'.
	#return lambda tag: 2 * sub.card(tag) - full.card(tag)
	# Same but it tries to downplay the 'how many are out' value in the
	# case of popular tags, to mitigate the 'there will always be popular
	# tags left out' cases.  Does not seem to be much of an improvement.
	#return lambda tag: sub.card(tag) - float(full.card(tag) - sub.card(tag))/(math.sin(float(full.card(tag))*3.1415/full.packageCount())/4 + 0.75)


class DB:
	def __init__(self):
		self.db = {}
		self.rdb = {}
	
	def read(self, input, tagFilter = None):
		"Read the database from a file"
		self.db, self.rdb = readTagDatabaseBothWays(input, tagFilter)

	def dump(self):
		output(self.db)

	def dumpReverse(self):
		output(self.rdb)
	
	def reverse(self):
		"Return the reverse collection, sharing tagsets with this one"
		res = DB()
		res.db = self.rdb
		res.rdb = self.db
		return res

	def reverseCopy(self):
		"""
		Return the reverse collection, with a copy of the tagsets of
		this one
		"""
		res = DB()
		res.db = self.rdb.copy()
		res.rdb = self.db.copy()
		return res

	def choosePackages(self, packageIter):
		"""
		Return a collection with only the packages in packageIter,
		sharing tagsets with this one
		"""
		res = DB()
		db = {}
		for pkg in packageIter:
			if self.db.has_key(pkg): db[pkg] = self.db[pkg]
		res.db = db
		res.rdb = reverse(db)
		return res

	def choosePackagesCopy(self, packageIter):
		"""
		Return a collection with only the packages in packageIter,
		with a copy of the tagsets of this one
		"""
		res = DB()
		db = {}
		for pkg in packageIter:
			db[pkg] = self.db[pkg]
		res.db = db
		res.rdb = reverse(db)
		return res

	def filterPackages(self, packageFilter):
		"""
		Return a collection with only those packages that match a
		filter, sharing tagsets with this one
		"""
		res = DB()
		db = {}
		for pkg in filter(packageFilter, self.db.iterkeys()):
			db[pkg] = self.db[pkg]
		res.db = db
		res.rdb = reverse(db)
		return res

	def filterPackagesCopy(self, filter):
		"""
		Return a collection with only those packages that match a
		filter, with a copy of the tagsets of this one
		"""
		res = DB()
		db = {}
		for pkg in filter(filter, self.db.iterkeys()):
			db[pkg] = self.db[pkg].copy()
		res.db = db
		res.rdb = reverse(db)
		return res

	def hasPackage(self, pkg):
		"""Check if the collection contains the given package"""
		return self.db.has_key(pkg)

	def hasTag(self, tag):
		"""Check if the collection contains packages tagged with tag"""
		return self.rdb.has_key(tag)

	def tagsOfPackage(self, pkg):
		"""Return the tag set of a package"""
		return self.db.has_key(pkg) and self.db[pkg] or set()

	def packagesOfTag(self, tag):
		"""Return the package set of a tag"""
		return self.rdb.has_key(tag) and self.rdb[tag] or set()

	def tagsOfPackages(self, pkgs):
		"""Return the set of tags that have all the packages in pkgs"""
		res = None
		for p in pkgs:
			if res == None:
				res = set(self.tagsOfPackage(p))
			else:
				res &= self.tagsOfPackage(p)
		return res

	def packagesOfTags(self, tags):
		"""Return the set of packages that have all the tags in tags"""
		res = None
		for t in tags:
			if res == None:
				res = set(self.packagesOfTag(t))
			else:
				res &= self.packagesOfTag(t)
		return res

	def card(self, tag):
		"""
		Return the cardinality of a tag
		"""
		return self.rdb.has_key(tag) and len(self.rdb[tag]) or 0

	def discriminance(self, tag):
		"""
		Return the discriminance index if the tag, that is, the minimum
		number of packages that would be eliminated by selecting only
		those tagged with this tag or only those not tagged with this
		tag.
		"""
		n = self.card(tag)
		tot = self.packageCount()
		return min(n, tot - n)

	def iterPackages(self):
		"""Iterate over the packages"""
		return self.db.iterkeys()

	def iterTags(self):
		"""Iterate over the tags"""
		return self.rdb.iterkeys()

	def iterPackagesTags(self):
		"""Iterate over 2-tuples of (pkg, tags)"""
		return self.db.iteritems()

	def iterTagsPackages(self):
		"""Iterate over 2-tuples of (tag, pkgs)"""
		return self.rdb.iteritems()

	def packageCount(self):
		"""Return the number of packages"""
		return len(self.db)

	def tagCount(self):
		"""Return the number of tags"""
		return len(self.rdb)

	def idealTagset(self, tags):
		"""
		Return the tagset made of the highest number of tags taken in
		consecutive sequence from the beginning of the given vector,
		that would intersecate with the tagset of a comfortable amount
		of packages.

		Comfortable is defined in terms of how far it is from 7.
		"""

		# TODO: the scoring function is quite ok, but may need more
		# tuning.  I also center it on 15 instead of 7 since we're
		# setting a starting point for the search, not a target point
		def score_fun(x):
			return float((x-15)*(x-15))/x

		hits = []
		tagset = set()
		min_score = 3
		for i in range(len(tags)):
			pkgs = self.packagesOfTags(tags[:i+1])
			card = len(pkgs)
			if card == 0: break;
			score = score_fun(card)
			if score < min_score:
				min_score = score
				tagset = set(tags[:i+1])
			i = i + 1

		# Return always at least the first tag
		if len(tagset) == 0:
			return set(tags[:1])
		else:
			return tagset
