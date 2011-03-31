# -*- coding: utf-8 -*-
from Crypto.Cipher import DES
import time
import datetime
import base64

####################################################################################################
# Author 		: GuinuX
# Contributors 	: Pierre
####################################################################################################
# CHANGELOG : - Pierre : Some changes to be Compatible With PLEX 8
####################################################################################################

PLUGIN_PREFIX = '/video/m6replay'
NAME          = 'M6Replay'
ART           = 'art-default.jpg'
ICON          = 'icon-default.png'

CONFIGURATION_URL = "http://www.m6replay.fr/files/configurationm6_lv3.xml"

####################################################################################################

def Start():

	Plugin.AddPrefixHandler(PLUGIN_PREFIX, VideoMainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("Coverflow", viewMode="Coverflow", mediaType="items")
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	
	MediaContainer.art = R(ART)
	MediaContainer.title1 = NAME
	DirectoryItem.thumb = R(ICON)
	HTTP.CacheTime = CACHE_1HOUR
	
	Dict['CATALOG_XML'] = ""
	Dict['IMAGES_SERVER'] = ""


def VideoMainMenu():
	dir = MediaContainer(viewGroup="Coverflow")
	xml = HTTP.Request(CONFIGURATION_URL).content

	Dict['IMAGES_SERVER'] = XML.ElementFromString( xml ).xpath("/config/path/image")[0].text
	EnCryptCatalogueURL = XML.ElementFromString( xml ).xpath("/config/services/service[@name='GetEnCryptCatalogueService']/url")[0].text
	
	cryptedXML = HTTP.Request(EnCryptCatalogueURL,cacheTime=CACHE_1HOUR).content	
	decryptor = DES.new( "ElFsg.Ot", DES.MODE_ECB )
	Dict['CATALOG_XML'] = decryptor.decrypt( base64.decodestring( cryptedXML ) )
	
	#
	# TODO : Tester si le decryptage s'est bien passé.
	#
	
	finXML = Dict['CATALOG_XML'].find( "</template_exchange_WEB>" ) + len( "</template_exchange_WEB>" )
	Dict['CATALOG_XML'] = Dict['CATALOG_XML'][ : finXML ]
	
	for category in XML.ElementFromString(Dict['CATALOG_XML']).xpath("//template_exchange_WEB/categorie"):
		nom = category.xpath("./nom")[0].text
		image = Dict['IMAGES_SERVER'] + category.get('big_img_url')
		idCategorie = category.get('id')
		dir.Append(Function(DirectoryItem(ListShows, title = nom, thumb = image), idCategorie = idCategorie, nomCategorie = nom))
	
	return dir


def ListShows(sender, idCategorie, nomCategorie):
	dir = MediaContainer(viewGroup="Coverflow", title1 = "M6 Replay", title2 = nomCategorie)
	search = "/template_exchange_WEB/categorie[@id='" + idCategorie + "']/categorie"

	for item in XML.ElementFromString(Dict['CATALOG_XML']).xpath(search):
		nom = item.xpath("nom")[0].text
		image = Dict['IMAGES_SERVER'] + item.get('big_img_url')
		idCategorie = item.get('id')

		dir.Append(Function(DirectoryItem(ListEpisodes, title = nom, thumb = image), idCategorie = idCategorie, nomCategorie = nom))
	
	return dir


def ListEpisodes(sender, idCategorie, nomCategorie):
	dir = MediaContainer(viewGroup="InfoList", title1 = "M6 Replay", title2 = nomCategorie)
	search = "//template_exchange_WEB/categorie/categorie[@id=" + idCategorie + "]/produit"
	
	for episode in XML.ElementFromString(Dict['CATALOG_XML']).xpath(search):
		idProduit = episode.get('id')
		nom = episode.xpath("./nom")[0].text
		description = episode.xpath("./resume")[0].text
		image = Dict['IMAGES_SERVER'] + episode.get('big_img_url')
		url = episode.xpath("./fichemedia")[0].get('video_url')[:-4]
		lienValideVideo = "rtmp://m6dev.fcod.llnwd.net:443/a3100/d1/"
		#date_diffusion = datetime.datetime(*(time.strptime(episode.xpath("./diffusion")[0].get('date'), "%Y-%m-%d %H:%M:%S")[0:6])).strftime("%d/%m/%Y à %Hh%M")
		date_diffusion = episode.xpath("./diffusion")[0].get('date').replace(" "," à ")
		str_duree = episode.xpath("./fichemedia")[0].get('duree')
		duree = long(str_duree) / 60
		dureevideo = long(str_duree)*1000
		description = description + '\n\nDiffusé le ' + date_diffusion + '\n' + 'Durée : ' + str(duree) + ' mn'
		dir.Append(RTMPVideoItem(url = lienValideVideo, width=640, height=375, clip = url, title = nom, subtitle = nomCategorie, summary = description, duration = dureevideo, thumb = image))
	return dir
	
	
