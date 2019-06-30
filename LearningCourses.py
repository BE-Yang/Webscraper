'''
How:
Program checks INDEX_FILENAME for all items to be downloaded. then navigate
to the item's link and proceed to scrape for all video links and corresponding
video names and add them to an array/file for queue.

Notes: Each video has a unique signature and expires after 2 hours.
'''
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import os, sys, re
from urllib2 import urlopen
from math import floor
from random import randint
from bs4 import BeautifulSoup as bs
from time import sleep
from datetime import datetime
import LCConstants

def startSession(link):
	session = webdriver.Firefox()
	session.get(link)
	sleep(3)
	return session

def login(session):
	session.find_element_by_id(LCConstants.USER_ID).send_keys(LCConstants.USER)
	sleep(3)
	session.find_element_by_id(LCConstants.PASS_ID).send_keys(LCConstants.PASS)
	sleep(2)
	session.find_element_by_id(LCConstants.PASS_ID).send_keys(Keys.ENTER)
	WebDriverWait(session, 30).until(
		EC.presence_of_element_located(
			(By.PARTIAL_LINK_TEXT, LCConstants.SIGNIN_VERIFICATION)
		)
	)

def appendToFile(link, fullTextPath):
	with open(fullTextPath, 'ab') as openedFile:
		openedFile.write(link.encode('utf-8') + '\n')


def checkIfDownloaded(link, downloadedLinks):
	# checks if the link is already downloaded, if so return True.
	# if false add the link to the file and return false
	fullTextPath = os.path.join(os.getcwd(), downloadedLinks)

	# base case for new courses
	if not os.path.exists(fullTextPath):
		appendToFile(link, fullTextPath)
		return False

	else:
		#checks if video already on downloaded list
		with open(downloadedLinks, 'rb') as openedFile:
			if link in openedFile.read():
				return True

		return False


def loadPageAndWait(session, link, delay=5):
	session.get(link)
	sleep(delay)


def makeFolder(folderPath):
	# creates the directory if the path does not exist
	if not os.path.exists(folderPath):
		os.makedirs(folderPath)


def main(session, itemLink, folderPath):
	try:
		topicTitle = itemLink.split('/')[-2]
	except Exception as e:
		print itemLink + '\n' + e

	fullFolderPath = os.path.join(folderPath, topicTitle)
	downloadedLinks = os.path.join(fullFolderPath, topicTitle + '.txt')
	makeFolder(fullFolderPath)
	soup = bs(session.page_source, 'html.parser')
	listOfLinks = soup.find_all('ul')
	grabbed = []
	# grabbing the links of all the videos to append to grabbed
	for link in listOfLinks:
		grabbedItem = link.find_all('li', class_= LCConstants.LIST_OF_ITEMS)
		if grabbedItem:
			grabbed.append(grabbedItem)

	# links are in a nested list structured by section and then by category
	results = {}
	count = 1
	for section in grabbed:
		for video in section:
			title = video.find('h3').next
			link = video.find('a')['href']
			start, end = video.find('div', class_= LCConstants.TIME_CLASS).next.split(' - ')
			startTime = datetime.strptime(start, '%H:%M:%S')
			endTime = datetime.strptime(end, '%H:%M:%S')
			duration = (endTime - startTime).total_seconds()
			results[count] = {'title':title, 'link': link, 'duration': duration}
			count += 1

	# grabbing the video
	for item in results.keys():
		link = results[item]['link']
		if not (checkIfDownloaded(link, downloadedLinks)):
			try:
				loadPageAndWait(session, LCConstants.ROOT_PAGE + link)
				WebDriverWait(session, 10).until(
					EC.presence_of_element_located(
						(By.CLASS_NAME, LCConstants.VIDEO_CLASS)
					)
				)
			except TimeoutException:
				print '\n\n TimeOutException error \n\n'
				session.quit()
				session = startSession(LCConstants.LOGIN_PAGE)
				login(session)
				loadPageAndWait(session, LCConstants.ROOT_PAGE + link)
				WebDriverWait(session, 10).until(
					EC.presence_of_element_located(
						(By.CLASS_NAME, LCConstants.VIDEO_CLASS)
					)
				)

			sleep(5)
			soup = bs(session.page_source, 'html.parser')

			video = soup.find('video')['src']
			summary = soup.find('div', class_= LCConstants.VIDEO_CLASS).text
			downloadedVideo = urlopen(video)
			fileName = re.sub(r'/', '-', str(item)+'-'+results[item]['title'])
			with open(fullFolderPath + '/' + fileName + '.mp4', 'wb') as f:
				f.write(downloadedVideo.read())

			with open(fullFolderPath + '/' + fileName + '.txt', 'wb') as f:
				f.write(summary.encode('utf-8'))

			appendToFile(link, downloadedLinks)

			halfDuration = floor(results[item]['duration'] / 2)
			if halfDuration > 300:
				sleepTime = randint(300, halfDuration)
			else:
				sleepTime = halfDuration

			print '%s: time until next video %d seconds' %(fileName, sleepTime)
			sleep(sleepTime)


if __name__ == '__main__':
	startPage = LCConstants.LOGIN_PAGE
	session = startSession(startPage)
	login(session)
	outputDirectory = LCConstants.OUTPUT_DIRECTORY
	folderName = LCConstants.OUTPUT_FOLDER_NAME
	folderPath = os.path.join(outputDirectory, folderName)

	makeFolder(folderPath)
	with open(os.path.join(folderPath, LCConstants.INDEX_FILENAME), 'rb') as openedFile:
		listOfTopics = openedFile.read().split('\n')

	for item in listOfTopics:
		loadPageAndWait(session, item)
		main(session, item, folderPath)




