# -*- coding: utf-8 -*-
#  Dreambox Enigma2 iptv player
#
#  Copyright (c) 2013 Alex Revetchi <revetski@gmail.com>
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  web: http://techhost.dlinkddns.com/
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from abstract_api import MODE_STREAM, AbstractAPI, AbstractStream
from datetime import datetime
from . import tdSec, secTd, setSyncTime, syncTime, unescapeEntities, Timezone, APIException


class KartinaAPI(AbstractAPI):
	
	iProvider = "kartinatv"
	NUMBER_PASS = True
	
	site = "http://iptv.kartina.tv"
	
	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)

	def start(self):
		self.authorize()
		
	def authorize(self):
		self.trace("Authorization started")
		self.trace("username = %s" % self.username)
		params = {"login" : self.username, "pass" : self.password, "settings" : "all"}
		reply = self.getXmlData(self.site+'/api/xml/login?', params, 'authorize', 1)

		if reply.find("error"):
			raise APIException(reply.find('error').findtext('message'))
		
		try:
			self.packet_expire = datetime.fromtimestamp(int(reply.find('account').findtext('packet_expire')))
		except:
			pass
		
		#Load settings here, because kartina api is't friendly
		self.settings = {}
		sett = reply.find("settings")
		for s in sett:
			if s.tag == "http_caching": continue
			value = s.findtext('value')
			vallist = []
			if s.tag == "stream_server":
				vallist = [(x.findtext('ip'), x.findtext('descr')) for x in s.find('list')]
			elif s.find('list'):
				valist = [x.text for x in s.find('list')]

			self.settings[s.tag] = {'id':s.tag, 'value':value, 'vallist':vallist}
		
		self.trace("Packet expire: %s" % self.packet_expire)
		self.sid = True
	
class e2iptv(KartinaAPI, AbstractStream):
	
	iName = "KartinaTV"
	MODE = MODE_STREAM
	NEXT_API = "KartinaMovies"
	
	HAS_PIN = True
	
	def __init__(self, username, password):
		KartinaAPI.__init__(self, username, password)
		AbstractStream.__init__(self)

	def on_channelEpgCurrent(self, channel):
		if channel.findtext("epg_progname") and channel.findtext("epg_end"):
			txt = channel.findtext("epg_progname").encode("utf-8")
			start = datetime.fromtimestamp(int(channel.findtext("epg_start").encode("utf-8")))
			end = datetime.fromtimestamp(int(channel.findtext("epg_end").encode("utf-8")))
			yield ({"text":txt,"start":start,"end":end})

	
	def on_setChannelsList(self):
		root = self.getXmlData(self.site+"/api/xml/channel_list?", {}, "channels list")
		try:
			setSyncTime(datetime.fromtimestamp(int(root.findtext("servertime").encode("utf-8"))))
		except:
			pass

		number = -1
		for group in root.find("groups"):
			group_id   = int(group.findtext("id"))
			group_name = group.findtext("name").encode("utf-8") 
			for channel in group.find("channels"):
				number += 1
				id           = int(channel.findtext("id").encode("utf-8"))
				name         = channel.findtext("name").encode("utf-8")
				has_archive  = channel.findtext("have_archive") or 0
				is_protected = channel.findtext("protected") or 0
				yield ({"id":id,
						"group_id":group_id,
						"group_name":group_name,
						"name":name,
						"number":number,
						"has_archive":has_archive,
						"is_protected":is_protected,
						"epg_data_opaque":channel})

	def setTimeShift(self, timeShift):
		params = {"var":"timeshift", "val":timeShift}
		self.getData(self.site+"/api/xml/settings_set?", params, "time shift new api %s" % timeShift) 

	def on_getStreamUrl(self, cid, pin, time = None):
		params = {"cid" : cid}
		if time:
			params["gmt"] = time.strftime("%s")
		if pin:
			params["protect_code"] = pin
		root = self.getXmlData(self.site+"/api/xml/get_url?", params, "URL of stream %s" % cid)
		url = root.findtext("url").encode("utf-8").split(' ')[0].replace('http/ts://', 'http://')
		if url == "protected": return self.ACCESS_DENIED
		return url
	
	def on_getChannelsEpg(self, cids):
		params = {"cids" : ",".join(map(str, cids))}
		root = self.getXmlData(self.site+"/api/xml/epg_current?", params, "getting epg of cids = %s" % cids)
		for channel in root.find('epg'):
			cid = int(channel.findtext("cid").encode("utf-8"))
			e = channel.find("epg")
			t = int(e.findtext('epg_start').encode("utf-8"))
			t_start = datetime.fromtimestamp(t)
			t = int(e.findtext('epg_end').encode("utf-8"))
			t_end = datetime.fromtimestamp(t)
			txt = e.findtext('epg_progname').encode('utf-8')
			yield ({'id':cid,'text':txt, 'start':t_start, 'end':t_end})
	
	def on_getDayEpg(self, cid, date):
		params = {"day" : date.strftime("%d%m%y"), "cid" : cid}
		root = self.getXmlData(self.site+"/api/xml/epg?", params, "day EPG for channel %s" % cid)
		for program in root.find('epg'):
			t = int(program.findtext("ut_start").encode("utf-8"))
			t_start= datetime.fromtimestamp(t)
			txt = unescapeEntities(program.findtext("progname")).encode("utf-8")
			yield ({'text':txt, 'start':t_start, 'end':None})

	def getSettings(self):
		return self.settings
	
	def pushSettings(self, sett):
		for x in sett:
			params = {"var" : x[0]['id'],
			          "val" : x[1]}
			self.getData(self.site+"/api/xml/settings_set?", params, "setting %s" % x[0]['id'])
