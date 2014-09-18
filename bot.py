import sys
import urllib2
import random
import time
import md5
import datetime
import getpass
import sqlite3

class AlbumBot:

	ACTION_LOGIN = 2
	ACTION_LOGOUT = 535
	ACTION_ATTACK = 512
	ACTION_PROFILE = 513
	ACTION_ALBUM = 116
	ACTION_TAVERN = 10
	RESP_ALBUM = 192
	INV_INDEX = 48
	SG_CLASS = 29

	def SendAction(self, act, params = [], relog = False):
		while True:
			sreq = self.session + str(act).zfill(3) + ('%3B'.join(params))
			srand = str(random.randrange(100000000, 999999998, 2)) + str(int(round(time.time()*1000)))
			opener = urllib2.build_opener()
			#opener.addheaders.append(("Cookie", "to_flimmerkiste=" + str(int(round(time.time()*1000)))))
			while True:
				try:
					resp = opener.open("http://" + self.server + "/request.php?req=" + sreq + "&random=%2&rnd=" + srand).read()
				except urllib2.URLError:
					print "Connection error"
					time.sleep(3)
					resp = None
				if resp != None:
					break
			if resp[0] == 'E' and relog == True:
				self.Logout()
				self.Login()
			else:
				break
		return resp

	def Login(self):
		print "Logging in:", self.name
		self.session = "00000000000000000000000000000000"
		resp = self.SendAction(self.ACTION_LOGIN, [urllib2.quote(self.name), self.passw, ""])
		self.session = resp.split(';')[2]
		print "Got session:", self.session

	def Logout(self):
		self.SendAction(self.ACTION_LOGOUT)

	def ChooseStartQuest(self):
		print "Fetching quest list"
		questinfo = self.SendAction(self.ACTION_TAVERN, [], True).split('/')
		print questinfo

	def MakeCharMap(self, lowrank, highrank, rankmap = None):
		charmap = {}
		print "Loading Hall of Fame"
		for rank in range(lowrank, highrank, 15):
			print "\r", (100*(rank-lowrank))/(highrank-lowrank), "%",
			sys.stdout.flush()
			chars = self.SendAction(7, ['', str(rank)], True).split('/')
			for i in [x*5+1 for x in range(15)]:
				try:
					charmap[chars[i]] = self.GetItems(chars[i])
					if rankmap != None:
						rankmap[chars[i]] = rank
				except:
					"Error getting items:", chars[i]
				time.sleep(.1)
		print "\r100 %"
		return charmap

	def GetItems(self, name):
		#print "Getting items of ", name
		sg = self.SendAction(self.ACTION_PROFILE, [urllib2.quote(name)], True).split('/')
		itemlist = []
		if len(sg) == 1:
			return itemlist
		for i in range(10):
			slot = int(sg[self.INV_INDEX + i*12])
			pic = int(sg[self.INV_INDEX + 1 + i*12])
			ench = slot / (2**24)
			sock = slot - ench*(2**24)
			sock /= 2**16
			slot -= ench*(2**24) + sock*(2**16)
			enchpow = pic / (2**16)
			pic -= enchpow * (2**16)
			pic %= 1000
			color = 0
			for l in range(8):
				color += int(sg[self.INV_INDEX + i*12 + 2 + l])
			color = (color % 5) + 1
			if pic >= 50 or slot == 10:
				color = 1
			if slot in range(1, 8):
				pclass = int(sg[self.SG_CLASS])
			else:
				pclass = 1
			item = tuple([slot, pic, color, pclass])
			itemlist.append(item)
		return itemlist

	def GetMissing(self):
		albumstr = self.SendAction(self.ACTION_ALBUM, [], True)
		if albumstr[0] == '+':
			albumstr = albumstr[1:]
		if int(albumstr[:3]) != self.RESP_ALBUM:
			return None
		arr = []
		for i in albumstr[3:].decode('base64', 'strict'):
			for l in [2**e for e in range(7, -1, -1)]:
				arr.append((ord(i) & l) / l)
		albindexes = [792+316, 1804, 2500, len(arr)]
		missitems = []
		for i in range(3):
			if i == 0:
				for item in range(30):
					for color in range(5):
						if arr[792 + item*5 + color] == 0:
							t = tuple([1, item+1, color+1, 1])
							if t not in missitems:
								missitems.append(t)
				for item in range(792+300, 792+308):
					if arr[item] == 0:
						t = tuple([1, item+50, 1, 1])
						if t not in missitems:
							missitems.append(t)
			self.AddMissingTo(missitems, arr[albindexes[i]:albindexes[i+1]], i+1)
		misc = arr[300:792]
		for i in range(21):
			for l in range(5):
				if misc[i*5 + l] == 0:
					t = tuple([8, i+1, l+1, 1])
					if t not in missitems:
						missitems.append(t)
		for i in range(13):
			if misc[210 + i] == 0:
				t = tuple([8, 50 + i, 1, 1])
				if t not in missitems:
					missitems.append(t)
		for i in range(16):
			for l in range(5):
				if misc[226 + i*5 + l] == 0:
					t = tuple([9, i+1, l+1, 1])
					if t not in missitems:
						missitems.append(t)
		for i in range(13):
			if misc[386 + i] == 0:
				t = tuple([9, 50 + i, 1, 1])
				if t not in missitems:
					missitems.append(t)
		for i in range(37):
			if misc[402 + i] == 0:
				t = tuple([10, i+1, 1, 1])
				if t not in missitems:
					missitems.append(t)
		for i in range(8):
			if misc[476 + i] == 0:
				t = tuple([10, 50 + i, 1, 1])
				if t not in missitems:
					missitems.append(t)
		return missitems

	def AddMissingTo(self, target, arr, pclass):
		for i in range(len(arr)):
			l = i % 116
			if l in (range(60, 100) + range(108, 120)) or arr[i] == 1:
				continue
			if pclass != 1:
				slot = [1,3,4,5,6,7,8][i/116]
			else:
				slot = [2,3,4,5,6,7,8][i/116]
			if l in range (100, 108):
				pic = l - 50
				color = 1
			else:
				pic = l/5 + 1
				color = (l % 5) + 1
			t = tuple([slot, pic, color, pclass])
			if t not in target:
				target.append(t)

	def FindBestOpponent(self, cm, miss):
		maxv = 0
		maxchar = ''
		for c in cm:
			if c == self.name:
				continue
			val = 0
			for item in cm[c]:
				if item in miss:
					val += 1
			if val > maxv:
				maxv = val
				maxchar = c
		print "Best opponent with", maxv, "items:", maxchar
		return maxchar


	def BeginAuto(self, low = 2900, high = 3100):
		cm = self.MakeCharMap(low, high)
		miss = self.GetMissing()
		while True:
			opp = self.FindBestOpponent(cm, miss)
			print "Attacking", opp
			resp = self.SendAction(self.ACTION_ATTACK, [urllib2.quote(opp)], True)
			while len(resp.split(';')) != 10
				time.sleep(120)
				resp = self.SendAction(self.ACTION_ATTACK, [urllib2.quote(opp)], True)
			fdata = resp.split(';')[1].split('/')
			hpindex = (len(fdata)/6 - 1)*6
			if int(fdata[hpindex]) > int(fdata[hpindex + 3]):
				print "Won",
				for i in cm[opp]:
					if i in miss:
						miss.remove(i)
			else:
				print "Lost",
				del cm[opp]
			print "(Gold gain:", float(resp.split(';')[8])/100, ", Rank gain:", resp.split(';')[7], ", HP difference:", abs(int(resp.split('/')[59]) - int(resp.split('/')[62])), ")"
			wtime = 60*10 + random.randrange(20, 80)
			endtime = datetime.datetime.now() + datetime.timedelta(seconds = wtime)
			print "Waiting until", endtime.strftime("%H:%M:%S")
			time.sleep(wtime)

	def BeginManual(self, low = 2500, high = 6000):
		cm = self.MakeCharMap(low, high)
		miss = self.GetMissing()
		while True:
			opp = self.FindBestOpponent(cm, miss)
			raw_input("Press enter to continue\n")
			for i in cm[opp]:
				if i in miss:
					miss.remove(i)

	def UpdateDB(self):
		db = sqlite3.connect('sfalbumsite/db/development.sqlite3')
		rankmap = {}
		cm = self.MakeCharMap(1, 8000, rankmap)
		db.execute('DELETE FROM players')
		db.execute('DELETE FROM items')
		for player in cm:
			db.execute('INSERT INTO players (name, rank) VALUES (?, ?)', (player.decode('utf-8'), rankmap[player]))
			(pid,) = db.execute("SELECT id FROM players WHERE name = ?", (player.decode('utf-8'),)).fetchone()
			if pid == None:
				continue
			for item in cm[player]:
				itemnum = int(str(item[0]) + str(item[1]) + str(item[2]) + str(item[3]))
				db.execute('INSERT INTO items (player_id, itemnum) VALUES (?, ?)', (pid, itemnum))
		db.commit()
		db.close()

	def __init__(self, name, passw, server):
		self.name = name
		self.passw = md5.md5(passw).hexdigest()
		self.server = server
		self.Login()

def Begin():
	name = raw_input("Username: ")
	passw = getpass.getpass("Password: ")
	low = raw_input("Low rank: ")
	high = raw_input("High rank: ")
	AlbumBot(name, passw, "s6.sfgame.gr").BeginAuto(int(low), int(high))