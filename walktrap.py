
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


import sys
import _walktrap
import utils.myTools


# Lancer un walktrap a partir d'un graphe
# Permet de detecter les composantes connexes
###############################################

def doWalktrap(edges, randomWalksLength=5, verboseLevel=0, showProgress=False, memoryUseLimit=0):

	print >> sys.stderr, "Computing connected components ...",
	# Les composantes connexes
	combin = utils.myTools.myCombinator()
	for (x,l) in edges.iteritems():
		l.pop(x, None)
		combin.addLink(l.keys() + [x])

	print >> sys.stderr, "Launching walktrap ",
	res = []
	n = len(edges)
	for nodes in combin:
		# Reindexation des noeuds
		indNodes = {}
		for (i,node) in enumerate(nodes):
			indNodes[node] = i

		# On lance le walktrap
		(relevantCuts,dend) = _walktrap.doWalktrap(indNodes, edges, randomWalksLength=randomWalksLength, verboseLevel=verboseLevel, showProgress=showProgress, memoryUseLimit=memoryUseLimit)

		# On doit revenir aux noms de noeuds originels
		def translate(x):
			if x < len(nodes):
				return nodes[x]
			else:
				return (x,)
		dend = [(cut,tuple(translate(f) for f in fils),translate(pere)) for (cut,fils,pere) in dend]
		res.append( (nodes, relevantCuts, dend, WalktrapDendogram(dend, nodes)) )
		sys.stderr.write('.')
	print >> sys.stderr, " OK"

	return res


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

	import utils.myMaths

	def mystr( (alpha,relevance,(clusters,lonely)) ):
		return "alpha=%f relevance=%f clusters=%d size=%d lonely=%d sizes={%s}" % \
			(alpha,relevance,len(clusters),sum([len(c) for c in clusters]),len(lonely),utils.myMaths.myStats.txtSummary([len(c) for c in clusters]))

	res = [(alpha,relevance,dend.cut(alpha)) for (alpha,relevance) in cuts]
	# Le choix par defaut
	if len(res) == 1:
		print >> sys.stderr, "1 seule possibilite"
		x = 0
	else:
		# Si on peut, on propose a l'utilisateur de choisir
		for x in res:
			print >> sys.stderr, "> " + mystr(x)
		import os
		if os.isatty(sys.stdin.fileno()):
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

