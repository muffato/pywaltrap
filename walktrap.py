
#
# Fonctions communes de traitement des communautes
# Formats d'entree des donnees:
#  - Fonction de score
#  - Dictionnaire d'aretes
#  - Fichier "node1 node2 weight"
# Format de sortie des donnees:
#  - Liste pour chaque composante connexe
#    - Les noeuds de la composante
#    - Les coupures interessantes (score,alpha)
#    - Le dendogramme (liste des (alphas, fils, pere))
#    - Le dendogramme (instance de WalktrapDendogram)


import os
import sys
import _walktrap
import utils.myMaths
import utils.myTools


###############################################
# Lancer un walktrap en bufferisant le graphe #
# Permet de detecter les composantes connexes #
###############################################
class WalktrapLauncher:

	def __init__(self, randomWalksLength=5, verboseLevel=0, showProgress=False, memoryUseLimit=0):
		self.edges = utils.myTools.defaultdict(dict)
		self.randomWalksLength = randomWalksLength
		self.verboseLevel = verboseLevel
		self.showProgress = showProgress
		self.memoryUseLimit = memoryUseLimit

	# Ajout d'une arete
	####################
	def addEdge(self, x, y, weight):

		weight = float(weight)
		if weight <= 0:
			return

		try:
			x = int(x)
		except ValueError:
			pass
		try:
			y = int(y)
		except ValueError:
			pass

		self.edges[x][y] = weight
		self.edges[y][x] = weight

	# Ajout automatique depuis un fichier
	######################################
	def updateFromFile(self, f):
		for l in f:
			c = l.split()
			self.addEdge(c[0], c[1], c[2])

	# Ajout automatique depuis une fonction
	########################################
	def updateFromFunc(self, items, func):
		for (x1,x2) in utils.myTools.myIterator.tupleOnStrictUpperList(items):
			self.addEdge(x1, x2, func(x1, x2))

	# Ajout automatique depuis des dictionnaires existants
	#######################################################
	def updateFromDict(self, d, items = None):
		for x1 in d:
			if (items != None) and (x1 not in items):
				continue
			for (x2,v) in self.edges[x1].iteritems():
				if (items != None) and (x2 not in items):
					continue
				self.addEdge(x1, x2, v)


	# Lancement du walktrap
	########################
	def doWalktrap(self):

		print >> sys.stderr, "Computing connected components ...",
		# Les composantes connexes
		combin = utils.myTools.myCombinator()
		for (x,l) in self.edges.iteritems():
			combin.addLink(l.keys() + [x])

		self.res = []

		n = len(self.edges)
		print >> sys.stderr, "Launching walktrap ",
		for nodes in combin:
			if len(nodes) != len(set(nodes)):
				# Cette erreur se declenche si il y a une boucle d'un noeud sur lui-meme ?
				print >> sys.stderr, "ERROR: BAD CONNECTED COMPONENT"
			# Reindexation des noeuds
			indNodes = {}
			for (i,node) in enumerate(nodes):
				#if node in self.edges:
				#	for j in xrange(i):
				#		if nodes[j] in self.edges[node]:
				#			print j, i, self.edges[node][nodes[j]]
				indNodes[node] = i

			# On lance le walktrap
			(relevantCuts,dend) = _walktrap.doWalktrap(indNodes, self.edges, randomWalksLength=self.randomWalksLength, verboseLevel=self.verboseLevel, showProgress=self.showProgress, memoryUseLimit=self.memoryUseLimit)

			# On doit revenir aux noms de noeuds originels
			def translate(x):
				if x < len(nodes):
					return nodes[x]
				else:
					return (x,)
			dend = [(cut,tuple(translate(f) for f in fils),translate(pere)) for (cut,fils,pere) in dend]
			self.res.append( (nodes, relevantCuts, dend, WalktrapDendogram(dend, nodes)) )
			sys.stderr.write('.')
		print >> sys.stderr, " OK"


#################################################################################
# Lancer un walktrap lorsqu'on sait qu'il n'y a qu'une seule composante connexe #
#################################################################################
class WalktrapDirectLauncher:

	def __init__(self, randomWalksLength=5, verboseLevel=0, showProgress=False, memoryUseLimit=0):
		self.edges = {}
		s = '/users/ldog/muffato/work/scripts/utils/walktrap/walktrap -t%d -d2 -m%d' % (randomWalksLength, memoryUseLimit)
		if showProgress:
			(self.stdin,self.stdout) = os.popen2(s)
		else:
			(self.stdin,self.stdout,stderr) = os.popen3(s + " -s")
			stderr.close()
		self.nodes = set()

	def addEdge(self, x, y, weight):
		self.nodes.add(x)
		self.nodes.add(y)
		print >> self.stdin, x, y, weight

	def updateFromFile(self, f):
		for l in f:
			c = l.split()
			self.nodes.add(int(c[0]))
			self.nodes.add(int(c[1]))
			print >> self.stdin, l,

	def updateFromFunc(self, items, func):
		for (x1,x2) in utils.myTools.myIterator.tupleOnStrictUpperList(items):
			score = func(x1, x2)
			if score > 0:
				self.addEdge(x1, x2, score)

	def updateFromDict(self, d):
		for x1 in d:
			for (x2,v) in self.edges[x1].iteritems():
				self.addEdge(x1, x2, v)

	def doWalktrap(self):

		self.stdin.close()
		(relevantCuts,dend) = loadWalktrapOutput(self.stdout)
		self.res = [(self.nodes, relevantCuts, dend, WalktrapDendogram(dend, self.nodes))]


###################################################
# Chargement d'un fichier de resultat de walktrap #
###################################################
def loadWalktrapOutput(f):

	# On charge les fusions
	allMerges = []
	lstFils = {}
	for line in f:
		if line == "\n":
			break

		l = line.split(':')
		scale = float(l[0])
		l = l[1].split('-->')

		allMerges.append( (scale,tuple([int(x) for x in l[0].split('+')]),int(l[1])) )

	allMerges.sort( reverse = True )

	lstCoup = []
	for line in f:
		try:
			# On extrait les lignes "alpha relevance"
			c = line.split()
			lstCoup.append( (float(c[0]),float(c[1])) )
		except ValueError:
			pass

	return (lstCoup, allMerges)


########################################################################################
# Le dendogramme resultat, que l'on peut couper a un niveau pour recuperer les classes #
########################################################################################
class WalktrapDendogram:

	def __init__(self, lstMerges, lstNodes):

		self.allMerges = lstMerges
		self.allMerges.sort(reverse = True)

		self.lstFils = {}
		for (_,fils,pere) in self.allMerges:
			self.lstFils[pere] = fils

		self.lstAll = lstNodes

	# Renvoie (la liste des clusters, les noeuds en dehors des clusters)
	def cut(self, scale):

		# On extrait les communautes correspondantes
		lstClusters = []
		fathersAlreadySeen = set()
		nodesNotSeen = set(self.lstAll)
		for (s,_,pere) in self.allMerges:
			if (s < scale) and (pere not in fathersAlreadySeen):
				cluster = []
				todo = [pere]
				while len(todo) > 0:
					father = todo.pop()
					if father in self.lstFils:
						fathersAlreadySeen.add(father)
						todo.extend(self.lstFils[father])
					else:
						nodesNotSeen.discard(father)
						cluster.append(father)
				lstClusters.append( cluster )
		return (lstClusters, list(nodesNotSeen))


####################################################
# Demande a l'utilisateur quelle partition choisir #
####################################################
def askPartitionChoice(dend, cuts):

	def mystr( (alpha,relevance,(clusters,lonely)) ):
		return "alpha=%f relevance=%f clusters=%d size=%d lonely=%d sizes={%s}" % \
			(alpha,relevance,len(clusters),sum([len(c) for c in clusters]),len(lonely),utils.myMaths.myStats([len(c) for c in clusters]))

	res = [(alpha,relevance,dend.cut(alpha)) for (alpha,relevance) in cuts]
	# Le choix par defaut
	if len(res) == 1:
		print >> sys.stderr, "1 seule possibilite"
		x = 0
	else:
		# Si on peut, on propose a l'utilisateur de choisir
		for x in res:
			print >> sys.stderr, "> " + mystr(x)
		if utils.myTools.stdinInput:
			print >> sys.stderr, "Aucune entree utilisateur"
			x = 0
		else:
			while True:
				try:
					print >> sys.stderr, "Choix ? ",
					x = int(raw_input())
					break
				except ValueError:
					pass
				except EOFError:
					x = 0
					break
	print >> sys.stderr, "Choix de " + mystr(res[x])
	return res[x]

